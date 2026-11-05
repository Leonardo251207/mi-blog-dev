"""Reporte de disponibilidad y latencia de sondas sintéticas."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import median
from typing import Any

from app.modules.synthetic.domain.models import (
    EjecucionSonda,
    FilaDimensionSonda,
    MetricaSonda,
    PuntoSonda,
    ProcedenciaSonda,
    ReporteSonda,
    ResumenSonda,
    Sonda,
)
from app.modules.synthetic.persistence.repository import (
    EjecucionSondaRepository,
    MetricaSondaRepository,
    SondaRepository,
)
from app.modules.properties.application.services import PropertiesService
from app.shared.enums import Grano
from app.shared.errors import DomainError
from app.shared.ids import ahora_utc
from app.shared.time import cubos, inicio_cubo, validar_rango


class SondaReportsService:
    def __init__(
        self,
        properties: PropertiesService,
        sondas: SondaRepository,
        ejecuciones: EjecucionSondaRepository,
        metricas: MetricaSondaRepository,
    ) -> None:
        self.properties = properties
        self.sondas = sondas
        self.ejecuciones = ejecuciones
        self.metricas = metricas

    async def reporte(
        self,
        *,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.HORA,
    ) -> ReporteSonda:
        propiedad = await self.properties.obtener_sitio(sitio_slug)
        desde, hasta = validar_rango(desde, hasta, grano)

        sondas = await self.sondas.list_by_propiedad(propiedad.id, activo=True)
        if not sondas:
            raise DomainError(
                "SIN_SONDAS",
                "La propiedad no tiene sondas activas.",
                status_code=422,
            )

        resumenes = []
        for sonda in sondas:
            resumen = await self._resumen_sonda(sonda, desde, hasta, grano)
            resumenes.append(resumen)

        return ReporteSonda(
            desde=desde,
            hasta=hasta,
            grano=grano.value,
            sondas=resumenes,
            procedencia=ProcedenciaSonda(
                fuente="synthetic",
                canal="SINTETICO",
                grano=grano.value,
                extraido_en=ahora_utc(),
                datos_hasta=hasta,
                completitud="COMPLETA",
                zona_horaria=propiedad.zona_horaria,
            ),
        )

    async def _resumen_sonda(
        self,
        sonda: Sonda,
        desde: datetime,
        hasta: datetime,
        grano: Grano,
    ) -> ResumenSonda:
        ejecuciones = await self.ejecuciones.list(sonda.id, desde, hasta)

        if not ejecuciones:
            return ResumenSonda(
                sonda_id=sonda.id,
                nombre=sonda.nombre,
                tipo=sonda.tipo,
                objetivo=sonda.objetivo,
                disponibilidad=0.0,
                latencia_p50=None,
                latencia_p95=None,
                total_ejecuciones=0,
                exitosas=0,
                fallidas=0,
                cert_expira_en=None,
                cert_dias_restantes=None,
                ultima_ejecucion=None,
            )

        exitosas = [e for e in ejecuciones if e.exito]
        fallidas = [e for e in ejecuciones if not e.exito]
        latencias = [e.latencia_ms for e in exitosas if e.latencia_ms is not None]

        # Última ejecución
        ultima = max(ejecuciones, key=lambda e: e.iniciado_en)

        # Certificado (de la última ejecución TLS)
        cert_expira = ultima.cert_expira_en
        cert_dias = ultima.cert_dias_restantes

        return ResumenSonda(
            sonda_id=sonda.id,
            nombre=sonda.nombre,
            tipo=sonda.tipo,
            objetivo=sonda.objetivo,
            disponibilidad=len(exitosas) / len(ejecuciones) if ejecuciones else 0.0,
            latencia_p50=median(latencias) if latencias else None,
            latencia_p95=self._percentil(latencias, 95) if latencias else None,
            total_ejecuciones=len(ejecuciones),
            exitosas=len(exitosas),
            fallidas=len(fallidas),
            cert_expira_en=cert_expira,
            cert_dias_restantes=cert_dias,
            ultima_ejecucion=ultima,
        )

    async def materializar_metricas(
        self,
        *,
        sitio_slug: str,
        grano: Grano = Grano.HORA,
    ) -> int:
        """Materializa métricas agregadas para dashboards rápidos."""
        propiedad = await self.properties.obtener_sitio(sitio_slug)
        sondas = await self.sondas.list_by_propiedad(propiedad.id, activo=True)

        materializadas = 0
        for sonda in sondas:
            # Obtener última métrica materializada para saber desde cuándo
            # Por simplicidad, materializamos las últimas 24h
            desde = ahora_utc().replace(hour=0, minute=0, second=0, microsecond=0)
            hasta = ahora_utc()

            for cubo in cubos(desde, hasta, grano, propiedad.zona_horaria):
                ejecuciones_cubo = [
                    e for e in await self.ejecuciones.list(sonda.id, cubo, cubo)
                    if inicio_cubo(e.iniciado_en, grano, propiedad.zona_horaria) == cubo
                ]

                if not ejecuciones_cubo:
                    continue

                exitosas = [e for e in ejecuciones_cubo if e.exito]
                latencias = [e.latencia_ms for e in exitosas if e.latencia_ms is not None]

                metrica = MetricaSonda(
                    sonda_id=sonda.id,
                    propiedad_id=propiedad.id,
                    cubo=cubo,
                    grano=grano.value,
                    total_ejecuciones=len(ejecuciones_cubo),
                    exitosas=len(exitosas),
                    fallidas=len(ejecuciones_cubo) - len(exitosas),
                    latencia_p50=median(latencias) if latencias else None,
                    latencia_p95=self._percentil(latencias, 95) if latencias else None,
                    latencia_p99=self._percentil(latencias, 99) if latencias else None,
                    disponibilidad=len(exitosas) / len(ejecuciones_cubo),
                    errores_por_tipo=self._contar_errores(ejecuciones_cubo),
                    cert_expira_en=ejecuciones_cubo[-1].cert_expira_en if ejecuciones_cubo else None,
                    cert_dias_restantes_min=min(
                        (e.cert_dias_restantes for e in ejecuciones_cubo if e.cert_dias_restantes is not None),
                        default=None,
                    ),
                )
                await self.metricas.upsert(metrica)
                materializadas += 1

        return materializadas

    def _percentil(self, valores: list[float], p: int) -> float | None:
        if not valores:
            return None
        valores_ordenados = sorted(valores)
        k = (len(valores_ordenados) - 1) * p / 100
        f = int(k)
        c = min(f + 1, len(valores_ordenados) - 1)
        if f == c:
            return valores_ordenados[f]
        return valores_ordenados[f] + (valores_ordenados[c] - valores_ordenados[f]) * (k - f)

    def _contar_errores(self, ejecuciones: list[EjecucionSonda]) -> dict[str, int]:
        conteo: dict[str, int] = defaultdict(int)
        for e in ejecuciones:
            if not e.exito and e.error_tipo:
                conteo[e.error_tipo] += 1
        return dict(conteo)