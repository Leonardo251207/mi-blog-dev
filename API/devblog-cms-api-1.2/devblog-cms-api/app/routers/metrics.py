"""Resumen de métricas para la consola del CMS.

El endpoint vive en el CMS y consulta el servicio de métricas por GraphQL. Si
el servicio está dormido o no responde, devuelve `disponible: false` en lugar
de romper el panel: la consola puede seguir administrando contenido.
"""
from typing import Annotated, Literal

from fastapi import APIRouter, Query

from .. import schemas
from ..dependencies import ConsolePrincipal, SettingsDep
from ..metrics_client import overview

router = APIRouter(prefix="/metrics", tags=["Métricas"])

_ERR = {"model": schemas.ErrorResponse}
_COMMON = {401: _ERR, 403: _ERR, 429: _ERR}


@router.get("/overview", response_model=schemas.MetricsOverview,
            summary="Resumen de tráfico del sitio",
            responses={**_COMMON, 422: _ERR})
def metrics_overview(principal: ConsolePrincipal, settings: SettingsDep,
                     days: Annotated[int, Query(ge=1, le=365)] = 7,
                     grano: Annotated[Literal["DIA", "HORA"], Query()] = "DIA"):
    """KPIs, rutas y serie temporal del sitio configurado en `CMS_METRICS_SITE`."""
    return schemas.MetricsOverview(**overview(settings, days=days, grano=grano))
