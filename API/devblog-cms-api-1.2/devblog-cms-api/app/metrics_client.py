"""Cliente del servicio de métricas (GraphQL).

La consola del CMS no llama directamente al servicio de métricas desde el
navegador: lo hace este backend. Así se evita depender de CORS, se puede
cachear/limitar y la URL del servicio queda en configuración del servidor.

La consulta usa el esquema real de `metrics-navigation`:
    trafico(sitioSlug, desde, hasta, grano) -> TraficoType
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from .config import Settings
from .domain import iso, utcnow

QUERY = """
query Trafico($sitio: String!, $desde: DateTime!, $hasta: DateTime!, $grano: Grano!) {
  trafico(sitioSlug: $sitio, desde: $desde, hasta: $hasta, grano: $grano) {
    pageviews
    sesiones
    visitantesUnicosEstimados
    porRuta { clave valor }
    porHost { clave valor }
    serie { cubo pageviews sesiones }
  }
}
"""


class MetricsUnavailable(Exception):
    """El servicio de métricas no respondió o devolvió un error GraphQL."""


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def query_metrics(settings: Settings, *, days: int, grano: str) -> dict:
    """Consulta el tráfico y devuelve el bloque `data.trafico`."""
    if not settings.metrics_url:
        raise MetricsUnavailable("CMS_METRICS_URL no está configurada.")

    hasta = utcnow()
    desde = hasta - timedelta(days=days)
    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "sitio": settings.metrics_site,
            "desde": iso(desde),
            "hasta": iso(hasta),
            "grano": grano,
        },
    }).encode("utf-8")

    request = urllib.request.Request(
        settings.metrics_url.rstrip("/") + "/v1/query",
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=settings.metrics_timeout_s) as response:
            body = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise MetricsUnavailable(f"No se pudo conectar con métricas: {exc}") from exc

    try:
        result = json.loads(body)
    except json.JSONDecodeError as exc:
        raise MetricsUnavailable("El servicio de métricas devolvió una respuesta inválida.") from exc

    if result.get("errors"):
        message = "; ".join(
            str(item.get("message", "error GraphQL")) for item in result["errors"]
        )
        raise MetricsUnavailable(message)

    trafico = (result.get("data") or {}).get("trafico")
    if not isinstance(trafico, dict):
        raise MetricsUnavailable("La respuesta de métricas no incluyó el bloque 'trafico'.")
    return trafico


def overview(settings: Settings, *, days: int, grano: str) -> dict:
    """Devuelve un resumen listo para el panel, disponible o no."""
    hasta = utcnow()
    desde = hasta - timedelta(days=days)
    base = {
        "sitio": settings.metrics_site,
        "desde": desde,
        "hasta": hasta,
        "grano": grano,
    }
    try:
        data = query_metrics(settings, days=days, grano=grano)
    except MetricsUnavailable as exc:
        return {
            **base,
            "disponible": False,
            "pageviews": 0,
            "sesiones": 0,
            "visitantes_unicos": 0,
            "por_ruta": [],
            "por_host": [],
            "serie": [],
            "error": str(exc),
        }

    def rows(key: str) -> list[dict]:
        return [
            {"clave": str(item.get("clave", "")), "valor": int(item.get("valor") or 0)}
            for item in (data.get(key) or [])
        ]

    serie = []
    for point in data.get("serie") or []:
        cubo = point.get("cubo")
        if not cubo:
            continue
        serie.append({
            "cubo": _parse_datetime(str(cubo)),
            "pageviews": int(point.get("pageviews") or 0),
            "sesiones": int(point.get("sesiones") or 0),
        })

    return {
        **base,
        "disponible": True,
        "pageviews": int(data.get("pageviews") or 0),
        "sesiones": int(data.get("sesiones") or 0),
        "visitantes_unicos": int(data.get("visitantesUnicosEstimados") or 0),
        "por_ruta": rows("porRuta"),
        "por_host": rows("porHost"),
        "serie": serie,
        "error": None,
    }
