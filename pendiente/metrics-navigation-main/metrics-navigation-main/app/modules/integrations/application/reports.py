"""Reporte de métricas de integraciones externas."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from app.modules.integrations.domain.models import (
    FilaDimensionIntegracion,
    MetricaIntegracion,
    PuntoIntegracion,
    ProcedenciaIntegracion,
    ReporteIntegracion,
    ResumenMetricaIntegracion,
)
from app.modules.integrations.persistence.repository import MetricaIntegracionRepository
from app.modules.properties.application.services import PropertiesService
from app.shared.enums import Grano
from app.shared.errors import DomainError
from app.shared.ids import ahora_utc
from app.shared.time import cubos, inicio_cubo, validar_rango


class IntegracionReportsService:
    def __init__(
        self,
        properties: PropertiesService,
        metricas: MetricaIntegracionRepository,
    ) -> None:
        self.properties = properties
        self.metricas = metricas

    async def reporte(
        self,
        *,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.DIA,
    ) -> ReporteIntegracion:
        propiedad = await self.properties.obtener_sitio(sitio_slug)
        desde, hasta = validar_rango(desde, hasta, grano)

        metricas = await self.metricas.list(propiedad.id, desde, hasta)
        if not metricas:
            raise DomainError(
                "SIN_METRICAS_INTEGRACION",
                "No hay métricas de integraciones para el rango solicitado.",
                status_code=422,
            )

        # Agrupar por nombre de métrica
        por_nombre: dict[str, list[MetricaIntegracion]] = defaultdict(list)
        for m in metricas:
            por_nombre[m.nombre].append(m)

        resumenes = []
        for nombre, lista in por_nombre.items():
            resumen = self._resumen_metrica(nombre, lista, desde, hasta, grano, propiedad.zona_horaria)
            resumenes.append(resumen)

        return ReporteIntegracion(
            desde=desde,
            hasta=hasta,
            grano=grano.value,
            metricas=resumenes,
            procedencia=ProcedenciaIntegracion(
                fuente="api_externa",
                canal="API_EXTERNA",
                grano=grano.value,
                extraido_en=ahora_utc(),
                datos_hasta=hasta,
                completitud="COMPLETA" if metricas else "PARCIAL",
                zona_horaria=propiedad.zona_horaria,
            ),
        )

    def _resumen_metrica(
        self,
        nombre: str,
        metricas: list[MetricaIntegracion],
        desde: datetime,
        hasta: datetime,
        grano: Grano,
        zona_horaria: str,
    ) -> ResumenMetricaIntegracion:
        # Determinar tipo de integración por el nombre
        tipo = "desconocido"
        if nombre.startswith("ga4_"):
            tipo = "GA4"
        elif nombre.startswith("gsc_") or nombre.startswith("search_console_"):
            tipo = "SEARCH_CONSOLE"
        elif nombre.startswith("adsense_") or nombre.startswith("ad_manager_"):
            tipo = "ADSENSE"

        total = sum(m.valor for m in metricas)

        # Agrupar por dimensión principal (ej: page, query, country)
        por_dimension: dict[str, float] = defaultdict(float)
        for m in metricas:
            dim_key = m.dimensiones.get("page") or m.dimensiones.get("query") or m.dimensiones.get("country") or "total"
            por_dimension[dim_key] += m.valor

        # Serie temporal
        serie: list[PuntoIntegracion] = []
        agrupados: dict[datetime, float] = defaultdict(float)
        for m in metricas:
            cubo = inicio_cubo(m.fecha_dato, grano, zona_horaria)
            agrupados[cubo] += m.valor

        for cubo in cubos(desde, hasta, grano, zona_horaria):
            serie.append(PuntoIntegracion(cubo=cubo, valor=agrupados.get(cubo, 0.0)))

        return ResumenMetricaIntegracion(
            nombre=nombre,
            tipo_integracion=tipo,
            total=total,
            por_dimension=[FilaDimensionIntegracion(clave=k, valor=v) for k, v in sorted(por_dimension.items(), key=lambda x: -x[1])[:20]],
            serie=serie,
        )