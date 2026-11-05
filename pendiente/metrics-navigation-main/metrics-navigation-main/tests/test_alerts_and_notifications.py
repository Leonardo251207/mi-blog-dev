from __future__ import annotations

import json
from httpx import AsyncClient

from tests.helpers import graphql


async def test_crear_canal_notificacion_y_probar(client: AsyncClient):
    # 1. Crear canal de notificación Webhook
    mutacion_canal = """
    mutation CrearCanal($input: CrearCanalNotificacionInput!) {
      crearCanalNotificacion(input: $input) {
        id
        nombre
        tipo
        estado
      }
    }
    """
    config_json = json.dumps({"url_ref": "literal:https://webhook.site/test"})
    resp_canal = await graphql(
        client,
        mutacion_canal,
        {
            "input": {
                "nombre": "Canal Ops",
                "tipo": "WEBHOOK",
                "config": config_json,
                "estado": "ACTIVO",
            }
        },
    )
    assert resp_canal.status_code == 200
    datos_canal = resp_canal.json()
    assert "errors" not in datos_canal, datos_canal
    canal = datos_canal["data"]["crearCanalNotificacion"]
    canal_id = canal["id"]
    assert canal["nombre"] == "Canal Ops"
    assert canal["tipo"] == "WEBHOOK"

    # 2. Consultar lista de canales
    consulta_canales = """
    query {
      canalesNotificacion { id nombre tipo }
    }
    """
    resp_list = await graphql(client, consulta_canales)
    datos_list = resp_list.json()
    assert "errors" not in datos_list
    assert any(c["id"] == canal_id for c in datos_list["data"]["canalesNotificacion"])

    # 3. Probar notificación (verifica que no haya AttributeError ni fallos de despacho)
    mutacion_prueba = """
    mutation Probar($input: ProbarNotificacionInput!) {
      probarNotificacion(input: $input) {
        id
        reglaId
        canalId
        titulo
        severidad
      }
    }
    """
    resp_prueba = await graphql(
        client,
        mutacion_prueba,
        {
            "input": {
                "canalId": canal_id,
                "titulo": "Alerta Test",
                "cuerpo": "Verificación del despachador",
                "severidad": "INFO",
            }
        },
    )
    assert resp_prueba.status_code == 200
    datos_prueba = resp_prueba.json()
    assert "errors" not in datos_prueba, datos_prueba
    notif = datos_prueba["data"]["probarNotificacion"]
    assert notif["canalId"] == canal_id
    assert notif["titulo"] == "Alerta Test"


async def test_regla_alerta_ciclo(client: AsyncClient, container, sitio):
    propiedad, _ = sitio

    # 1. Crear canal
    canal_resp = await graphql(
        client,
        """
        mutation CrearCanal($input: CrearCanalNotificacionInput!) {
          crearCanalNotificacion(input: $input) { id }
        }
        """,
        {
            "input": {
                "nombre": "Webhook Alertas",
                "tipo": "WEBHOOK",
                "config": json.dumps({"url_ref": "literal:http://testserver/hook"}),
            }
        },
    )
    canal_id = canal_resp.json()["data"]["crearCanalNotificacion"]["id"]

    # 2. Crear regla de alerta de umbral
    mutacion_regla = """
    mutation CrearRegla($input: CrearReglaAlertaInput!) {
      crearReglaAlerta(input: $input) {
        id
        nombre
        tipo
        metrica
        condicion
        severidad
      }
    }
    """
    resp_regla = await graphql(
        client,
        mutacion_regla,
        {
            "input": {
                "propiedadId": propiedad.id,
                "nombre": "Exceso de pageviews",
                "tipo": "UMBRAL",
                "metrica": "pageviews",
                "condicion": "> 0",
                "ventana": "1h",
                "severidad": "AVISO",
                "canalesNotificacion": [canal_id],
                "silencioMinutos": 10,
            }
        },
    )
    assert resp_regla.status_code == 200
    datos_regla = resp_regla.json()
    assert "errors" not in datos_regla, datos_regla
    regla = datos_regla["data"]["crearReglaAlerta"]
    assert regla["nombre"] == "Exceso de pageviews"

    # 3. Evaluar reglas con el ciclo de evaluación
    ciclo = await container.alertas_service.ciclo_evaluacion()
    assert ciclo["reglas_evaluadas"] >= 1
