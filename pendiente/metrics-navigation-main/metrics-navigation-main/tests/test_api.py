from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import TEST_KEY, graphql


def evento(id_evento: str = "evt-1", path: str = "/hola") -> dict:
    return {
        "id": id_evento,
        "type": "PAGEVIEW",
        "path": path,
        "host": "testserver",
        "session": "sesion-1",
        "visitor": "visitante-1",
        "screen": "1920x1080",
        "language": "es-ES",
        "referrer": "https://www.google.com/search?q=metrics",
    }


async def test_crear_sitio_y_consultar(client: AsyncClient):
    mutacion = """
    mutation Crear($input: CrearSitioInput!) {
      crearSitio(input: $input) { slug estadoVerificacion }
    }
    """
    respuesta = await graphql(
        client,
        mutacion,
        {"input": {"slug": "blog", "nombre": "Blog"}},
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "errors" not in datos, datos
    assert datos["data"]["crearSitio"]["slug"] == "blog"
    assert datos["data"]["crearSitio"]["estadoVerificacion"] == "PROVISIONAL"

    consulta = await graphql(client, "query { sitios { slug } }")
    assert consulta.json()["data"]["sitios"] == [{"slug": "blog"}]


async def test_mutacion_sin_admin_falla(client: AsyncClient):
    respuesta = await graphql(
        client,
        'mutation { crearSitio(input: {slug: "x", nombre: "X"}) { slug } }',
        admin=False,
    )
    datos = respuesta.json()
    assert datos["errors"][0]["extensions"]["code"] == "NO_AUTORIZADO"


async def test_beacon_ingesta_y_trafico(client: AsyncClient, sitio):
    respuesta = await client.post(
        "/v1/collect",
        json={"key": TEST_KEY, "site": "demo", "events": [evento()]},
        headers={"Origin": "http://testserver"},
    )
    assert respuesta.status_code == 202, respuesta.text
    assert respuesta.json() == {"aceptados": 1, "duplicados": 0, "rechazados": 0}

    consulta = """
    query Trafico($slug: String!, $desde: DateTime!, $hasta: DateTime!) {
      trafico(sitioSlug: $slug, desde: $desde, hasta: $hasta) {
        pageviews
        sesiones
        visitantesUnicosEstimados
        porRuta { clave valor }
        porHost { clave valor }
        porReferrer { clave valor }
        procedencia { fuente canal completitud }
      }
    }
    """
    datos = await graphql(
        client,
        consulta,
        {
            "slug": "demo",
            "desde": "2026-01-01T00:00:00Z",
            "hasta": "2027-01-01T00:00:00Z",
        },
    )
    cuerpo = datos.json()
    assert "errors" not in cuerpo, cuerpo
    trafico = cuerpo["data"]["trafico"]
    assert trafico["pageviews"] == 1
    assert trafico["sesiones"] == 1
    assert trafico["visitantesUnicosEstimados"] == 1
    assert trafico["porRuta"] == [{"clave": "/hola", "valor": 1}]
    assert trafico["porHost"] == [{"clave": "testserver", "valor": 1}]
    assert trafico["porReferrer"] == [{"clave": "www.google.com", "valor": 1}]
    assert trafico["procedencia"]["completitud"] == "COMPLETA"


async def test_evento_duplicado_no_suma(client: AsyncClient, sitio):
    carga = {"key": TEST_KEY, "site": "demo", "events": [evento("evt-dup")]}
    primera = await client.post(
        "/v1/collect", json=carga, headers={"Origin": "http://testserver"}
    )
    segunda = await client.post(
        "/v1/collect", json=carga, headers={"Origin": "http://testserver"}
    )
    assert primera.json()["aceptados"] == 1
    assert segunda.json() == {"aceptados": 0, "duplicados": 1, "rechazados": 0}


async def test_origen_no_permitido(client: AsyncClient, sitio):
    respuesta = await client.post(
        "/v1/collect",
        json={"key": TEST_KEY, "site": "demo", "events": [evento()]},
        headers={"Origin": "http://evil.example"},
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "ORIGEN_NO_PERMITIDO"


async def test_cobertura_declara_lo_no_observable(client: AsyncClient, sitio):
    consulta = """
    query { cobertura(sitioSlug: "demo") { metrica observable motivo } }
    """
    respuesta = await graphql(client, consulta)
    cuerpo = respuesta.json()
    assert "errors" not in cuerpo, cuerpo
    cobertura = {fila["metrica"]: fila for fila in cuerpo["data"]["cobertura"]}
    assert cobertura["pageviews"]["observable"] is True
    assert cobertura["agent_requests"]["observable"] is False
    assert cobertura["ga4_sessions"]["observable"] is False


async def test_verificar_dominio_promociona_propiedad(client: AsyncClient, container, sitio):
    propiedad, _ = sitio
    dominios = await container.properties_service.dominios_de(propiedad.id)
    dominio = dominios[0]

    mutacion = """
    mutation Verificar($input: DominioIdInput!) {
      verificarDominio(input: $input) { estado }
    }
    """
    respuesta = await graphql(client, mutacion, {"input": {"dominioId": dominio.id}})
    cuerpo = respuesta.json()
    assert "errors" not in cuerpo, cuerpo
    assert cuerpo["data"]["verificarDominio"]["estado"] == "VERIFICADO"

    consulta = await graphql(client, 'query { sitio(slug: "demo") { estadoVerificacion } }')
    assert consulta.json()["data"]["sitio"]["estadoVerificacion"] == "VERIFICADO"
