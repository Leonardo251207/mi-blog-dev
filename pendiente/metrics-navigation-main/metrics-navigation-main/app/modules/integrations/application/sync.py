"""Sincronización con APIs externas (GA4, Search Console, AdSense)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.modules.integrations.domain.models import EjecucionSincronizacion, Integracion, MetricaIntegracion
from app.modules.integrations.persistence.repository import (
    EjecucionSincronizacionRepository,
    IntegracionRepository,
    MetricaIntegracionRepository,
)
from app.shared.ids import ahora_utc, nueva_id


class IntegracionSyncService:
    """Coordina la sincronización con APIs externas."""

    def __init__(
        self,
        integraciones: IntegracionRepository,
        ejecuciones: EjecucionSincronizacionRepository,
        metricas: MetricaIntegracionRepository,
    ) -> None:
        self.integraciones = integraciones
        self.ejecuciones = ejecuciones
        self.metricas = metricas

    async def sincronizar_todas(self) -> int:
        """Ejecuta sincronización de todas las integraciones activas que tocan."""
        integraciones = await self.integraciones.list_activas()
        sincronizadas = 0
        for integracion in integraciones:
            if await self._debe_sincronizar(integracion):
                await self.sincronizar(integracion)
                sincronizadas += 1
        return sincronizadas

    async def _debe_sincronizar(self, integracion: Integracion) -> bool:
        """Verifica si la integración debe sincronizarse según su intervalo."""
        if not integracion.ultima_sincronizacion_en:
            return True
        transcurrido = (ahora_utc() - integracion.ultima_sincronizacion_en).total_seconds() / 3600
        return transcurrido >= integracion.intervalo_horas

    async def sincronizar(self, integracion: Integracion) -> EjecucionSincronizacion:
        """Ejecuta la sincronización de una integración."""
        inicio = ahora_utc()
        ejecucion = EjecucionSincronizacion(
            id=nueva_id(),
            integracion_id=integracion.id,
            propiedad_id=integracion.propiedad_id,
            iniciado_en=inicio,
        )

        try:
            if integracion.tipo == "GA4":
                metricas = await self._sincronizar_ga4(integracion)
            elif integracion.tipo == "SEARCH_CONSOLE":
                metricas = await self._sincronizar_search_console(integracion)
            elif integracion.tipo == "ADSENSE":
                metricas = await self._sincronizar_adsense(integracion)
            elif integracion.tipo == "AD_MANAGER":
                metricas = await self._sincronizar_ad_manager(integracion)
            else:
                raise ValueError(f"Tipo de integración no soportado: {integracion.tipo}")

            if metricas:
                await self.metricas.upsert_many(metricas)
                ejecucion.metricas_obtenidas = len(metricas)

            ejecucion.exito = True
            ejecucion.datos_muestra = {"metricas": len(metricas), "tipos": list(set(m.nombre for m in metricas))}

        except Exception as e:
            ejecucion.exito = False
            ejecucion.error = str(e)
            ejecucion.error_tipo = type(e).__name__

        ejecucion.finalizado_en = ahora_utc()
        await self.ejecuciones.add(ejecucion)

        # Actualizar estado de la integración
        integracion.ultima_sincronizacion_en = ahora_utc()
        if ejecucion.exito:
            integracion.ultima_sincronizacion_exitosa_en = ahora_utc()
            integracion.estado = "ACTIVA"
            integracion.error_ultima_sincronizacion = None
        else:
            integracion.estado = "ERROR"
            integracion.error_ultima_sincronizacion = ejecucion.error
        await self.integraciones.update(integracion)

        return ejecucion

    async def _sincronizar_ga4(self, integracion: Integracion) -> list[MetricaIntegracion]:
        """Sincroniza métricas de GA4 (Google Analytics Data API)."""
        # TODO: Implementar cliente real de GA4 Data API
        # Requiere: google-analytics-data, credenciales de service account
        # Métricas típicas: sessions, users, screenPageViews, engagementRate, averageSessionDuration
        # Dimensiones: date, pagePath, sessionSource, sessionMedium, country
        return []

    async def _sincronizar_search_console(self, integracion: Integracion) -> list[MetricaIntegracion]:
        """Sincroniza métricas de Search Console (Search Console API)."""
        # TODO: Implementar cliente real de Search Console API
        # Requiere: google-api-python-client, credenciales OAuth2
        # Métricas típicas: clicks, impressions, ctr, position
        # Dimensiones: date, query, page, country, device
        return []

    async def _sincronizar_adsense(self, integracion: Integracion) -> list[MetricaIntegracion]:
        """Sincroniza métricas de AdSense (AdSense Management API)."""
        # TODO: Implementar cliente real de AdSense API
        # Requiere: google-api-python-client, credenciales OAuth2
        # Métricas típicas: earnings, pageViews, clicks, ctr, cpc, rpm
        # Dimensiones: date, adUnit, country, platform
        return []

    async def _sincronizar_ad_manager(self, integracion: Integracion) -> list[MetricaIntegracion]:
        """Sincroniza métricas de Ad Manager (Google Ad Manager API)."""
        # TODO: Implementar cliente real de Ad Manager API
        # Requiere: googleads, credenciales OAuth2
        return []