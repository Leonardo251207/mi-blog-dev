from __future__ import annotations

from httpx import AsyncClient

from app.shared.enums import Entorno, ModoOrigen, TipoCanal
from app.shared.ids import ahora_utc
from tests.helpers import graphql

EDGE_KEY = "pk_live_edge_00000000000000000000000000000000"


async def setup_edge_channel(container, propiedad):
    canal, _ = await container.properties_service.crear_canal(
        propiedad=propiedad,
        tipo=TipoCanal.EDGE,
        modo_origen=ModoOrigen.EXACTO,
        origenes=["http://testserver"],
        entornos=[Entorno.PRODUCTION],
        clave_publica=EDGE_KEY,
    )
    return canal


async def test_crear_agente_y_consultar(client: AsyncClient):
    mutacion = """
    mutation CrearAgente($input: AgenteInput!) {
      crearAgente(input: $input) { id nombre categoria activo }
    }
    """
    resp = await graphql(
        client,
        mutacion,
        {
            "input": {
                "nombre": "GPTBot",
                "categoria": "crawler_ia",
                "patronesUa": ["GPTBot/1\\.0", "ChatGPT-User"],
                "notas": "Rastreador de OpenAI",
            }
        },
    )
    assert resp.status_code == 200
    datos = resp.json()
    assert "errors" not in datos, datos
    agente = datos["data"]["crearAgente"]
    assert agente["nombre"] == "GPTBot"
    assert agente["categoria"] == "crawler_ia"
    assert agente["activo"] is True

    # Consultar catálogo
    consulta = await graphql(client, "query { agentes { nombre categoria } }")
    agentes = consulta.json()["data"]["agentes"]
    assert any(a["nombre"] == "GPTBot" for a in agentes)


async def test_ingesta_edge_m2m_sin_origin_y_clasificacion(client: AsyncClient, container, sitio):
    propiedad, _ = sitio
    await setup_edge_channel(container, propiedad)

    # 1. Registrar agente conocido
    await container.agente_admin_service.crear_agente(
        nombre="ClaudeBot",
        categoria="crawler_ia",
        patrones_ua=["ClaudeBot/1\\.0", "AnthropicAI"],
    )

    ahora = ahora_utc()
    evento_edge = {
        "ts": ahora.isoformat(),
        "method": "GET",
        "path": "/articulos/ia",
        "host": "testserver",
        "status_code": 200,
        "bytes_sent": 5420,
        "bytes_received": 310,
        "duration_ms": 45,
        "ip": "198.51.100.1",
        "user_agent": "Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
        "country": "US",
    }

    # Llamada M2M: sin cabecera 'Origin'
    respuesta = await client.post(
        "/v1/collect/edge",
        json={"key": EDGE_KEY, "site": "demo", "events": [evento_edge]},
    )
    assert respuesta.status_code == 202, respuesta.text
    resultado = respuesta.json()
    assert resultado["aceptados"] == 1
    assert resultado["rechazados"] == 0

    # 2. Consultar trafico_edge
    consulta_edge = """
    query TraficoEdge($slug: String!, $desde: DateTime!, $hasta: DateTime!) {
      traficoEdge(sitioSlug: $slug, desde: $desde, hasta: $hasta) {
        totalPeticiones
        totalBytesEnviados
        porRuta { clave valor }
        porAgenteCategoria { clave valor }
      }
    }
    """
    datos_edge = await graphql(
        client,
        consulta_edge,
        {
            "slug": "demo",
            "desde": "2026-01-01T00:00:00Z",
            "hasta": "2027-01-01T00:00:00Z",
        },
    )
    cuerpo_edge = datos_edge.json()
    assert "errors" not in cuerpo_edge, cuerpo_edge
    t_edge = cuerpo_edge["data"]["traficoEdge"]
    assert t_edge["totalPeticiones"] == 1
    assert t_edge["totalBytesEnviados"] == 5420
    assert {"clave": "crawler_ia", "valor": 1} in t_edge["porAgenteCategoria"]

    # 3. Consultar trafico_agentes (debe haberse enriquecido automáticamente)
    consulta_agentes = """
    query TraficoAgentes($slug: String!, $desde: DateTime!, $hasta: DateTime!) {
      traficoAgentes(sitioSlug: $slug, desde: $desde, hasta: $hasta) {
        totalPeticiones
        totalBytesEnviados
        porCategoria { clave valor }
      }
    }
    """
    datos_agentes = await graphql(
        client,
        consulta_agentes,
        {
            "slug": "demo",
            "desde": "2026-01-01T00:00:00Z",
            "hasta": "2027-01-01T00:00:00Z",
        },
    )
    cuerpo_agentes = datos_agentes.json()
    assert "errors" not in cuerpo_agentes, cuerpo_agentes
    t_agentes = cuerpo_agentes["data"]["traficoAgentes"]
    assert t_agentes["totalPeticiones"] == 1
    assert t_agentes["totalBytesEnviados"] == 5420
    assert {"clave": "crawler_ia", "valor": 1} in t_agentes["porCategoria"]
