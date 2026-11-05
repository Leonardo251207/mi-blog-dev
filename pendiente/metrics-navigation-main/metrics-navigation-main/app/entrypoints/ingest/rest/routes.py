"""Puerta de ingesta REST: colector de beacon, edge y activo JavaScript."""

from __future__ import annotations

import html
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

from app.modules.edge.domain.models import LoteEdgeVisitas, ResultadoIngestaEdge
from app.modules.navigation.domain.models import LoteEventos, ResultadoIngesta

router = APIRouter(tags=["ingest"])

STATIC_DIR = Path(__file__).resolve().parents[3] / "static"


@router.get("/beacon.js", include_in_schema=False)
async def beacon_js() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "beacon.js",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.post("/collect", response_model=ResultadoIngesta, status_code=202)
async def collect(lote: LoteEventos, request: Request) -> ResultadoIngesta:
    container = request.app.state.container
    return await container.navigation_service.ingerir(
        lote,
        origin=request.headers.get("origin"),
        referer=request.headers.get("referer"),
    )


@router.post("/collect/edge", response_model=ResultadoIngestaEdge, status_code=202)
async def collect_edge(lote: LoteEdgeVisitas, request: Request) -> ResultadoIngestaEdge:
    container = request.app.state.container
    return await container.edge_service.ingerir(
        lote,
        origin=request.headers.get("origin"),
        referer=request.headers.get("referer"),
    )


@router.get("/demo", response_class=HTMLResponse, include_in_schema=False)
async def demo(request: Request) -> HTMLResponse:
    settings = request.app.state.settings
    clave = html.escape(settings.dev_beacon_key or "")
    if not clave:
        cuerpo = "<p>Configura <code>DEV_BEACON_KEY</code> en el <code>.env</code>.</p>"
    else:
        cuerpo = f"""
        <p>Esta página carga el beacon y envía un pageview al colector.</p>
        <p>Abre la consola del navegador para ver el evento con <code>data-debug=\"true\"</code>.</p>
        <p><a href=\"/v1/query\">Abrir GraphiQL</a></p>
        <script
          defer
          src=\"/v1/beacon.js\"
          data-key=\"{clave}\"
          data-site=\"demo\"
          data-debug=\"true\"
        ></script>
        """
    return HTMLResponse(
        f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Demo del beacon</title>
  </head>
  <body>
    <h1>Metrics Collector & Retriever</h1>
    {cuerpo}
  </body>
</html>"""
    )