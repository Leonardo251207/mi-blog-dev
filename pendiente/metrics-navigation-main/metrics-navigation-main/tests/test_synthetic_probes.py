from __future__ import annotations

import json
from datetime import timedelta
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.modules.synthetic.domain.models import Sonda
from app.shared.ids import ahora_utc
from tests.helpers import graphql


async def test_crear_sonda_y_reporte(client: AsyncClient, container, sitio):
    propiedad, _ = sitio

    mutacion_sonda = """
    mutation CrearSonda($input: CrearSondaInput!) {
      crearSonda(input: $input) {
        id
        nombre
        tipo
        objetivo
        activo
      }
    }
    """
    resp_sonda = await graphql(
        client,
        mutacion_sonda,
        {
            "input": {
                "propiedadId": propiedad.id,
                "nombre": "Healthcheck Homepage",
                "tipo": "HTTP",
                "objetivo": "http://testserver/health",
                "esperadoStatus": 200,
                "intervaloSegundos": 60,
            }
        },
    )
    assert resp_sonda.status_code == 200
    datos = resp_sonda.json()
    assert "errors" not in datos, datos
    sonda = datos["data"]["crearSonda"]
    sonda_id = sonda["id"]
    assert sonda["nombre"] == "Healthcheck Homepage"

    # Consultar sondas
    consulta_sondas = f"""
    query {{
      sondas(propiedadId: "{propiedad.id}") {{
        id
        nombre
        objetivo
      }}
    }}
    """
    resp_list = await graphql(client, consulta_sondas)
    assert any(s["id"] == sonda_id for s in resp_list.json()["data"]["sondas"])

    # Ejecutar sonda simulando respuesta HTTP
    with patch.object(container.synthetic_service.runner.client, "request") as mock_req:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{"status": "ok"}'
        mock_resp.text = '{"status": "ok"}'
        mock_resp.headers = {"content-type": "application/json"}
        mock_req.return_value = mock_resp

        mutacion_ejecutar = f"""
        mutation {{
          ejecutarSonda(input: {{ sondaId: "{sonda_id}" }}) {{
            id
            exito
            statusCode
            latenciaMs
          }}
        }}
        """
        resp_ejecutar = await graphql(client, mutacion_ejecutar)
        datos_ej = resp_ejecutar.json()
        assert "errors" not in datos_ej, datos_ej
        ejecucion = datos_ej["data"]["ejecutarSonda"]
        assert ejecucion["exito"] is True
        assert ejecucion["statusCode"] == 200

    # Consultar reporte de sondas para la ventana actual
    ahora = ahora_utc()
    desde = (ahora - timedelta(hours=2)).isoformat()
    hasta = (ahora + timedelta(hours=2)).isoformat()
    consulta_reporte = f"""
    query {{
      reporteSondas(
        sitioSlug: "{propiedad.slug}",
        desde: "{desde}",
        hasta: "{hasta}",
        grano: "HORA"
      ) {{
        sondas {{
          sondaId
          disponibilidad
          totalEjecuciones
          exitosas
        }}
      }}
    }}
    """
    resp_rep = await graphql(client, consulta_reporte)
    datos_rep = resp_rep.json()
    assert "errors" not in datos_rep, datos_rep
    reporte = datos_rep["data"]["reporteSondas"]
    assert len(reporte["sondas"]) >= 1
    assert reporte["sondas"][0]["disponibilidad"] == 1.0
    assert reporte["sondas"][0]["exitosas"] == 1


async def test_sonda_tls_timezone_safe(container, sitio):
    propiedad, _ = sitio
    sonda = Sonda(
        propiedad_id=propiedad.id,
        nombre="TLS Test",
        tipo="TLS",
        objetivo="example.com:443",
        timeout_segundos=5,
    )
    # Ejecutamos con mock en socket para verificar que el parsing de cert con timezone no falle
    cert_sample = {"notAfter": "Jul 25 12:00:00 2028 GMT"}
    with patch("socket.create_connection"), patch("ssl.create_default_context") as mock_ssl:
        mock_context = mock_ssl.return_value
        mock_ssock = mock_context.wrap_socket.return_value.__enter__.return_value
        mock_ssock.version.return_value = "TLSv1.3"
        mock_ssock.getpeercert.return_value = cert_sample

        ejecucion = await container.synthetic_service.runner.ejecutar(sonda)
        assert ejecucion.exito is True
        assert ejecucion.tls_version == "TLSv1.3"
        assert ejecucion.cert_expira_en is not None
        assert ejecucion.cert_dias_restantes > 0
