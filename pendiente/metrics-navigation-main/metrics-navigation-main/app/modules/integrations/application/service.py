"""Servicio principal del módulo Integrations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.modules.integrations.application.reports import IntegracionReportsService
from app.modules.integrations.application.sync import IntegracionSyncService
from app.modules.integrations.domain.models import Integracion
from app.modules.integrations.persistence.repository import (
    EjecucionSincronizacionRepository,
    IntegracionRepository,
    MetricaIntegracionRepository,
)
from app.modules.properties.application.services import PropertiesService


class IntegrationsService:
    """Coordina integraciones, sincronizaciones y reportes."""

    def __init__(
        self,
        properties: PropertiesService,
        integraciones: IntegracionRepository,
        ejecuciones: EjecucionSincronizacionRepository,
        metricas: MetricaIntegracionRepository,
    ) -> None:
        self.properties = properties
        self.integraciones_repo = integraciones
        self.ejecuciones_repo = ejecuciones
        self.metricas_repo = metricas
        self.sync = IntegracionSyncService(integraciones, ejecuciones, metricas)
        self.reports = IntegracionReportsService(properties, metricas)

    # --- CRUD Integraciones ---

    async def crear_integracion(self, integracion: Integracion) -> Integracion:
        await self.integraciones_repo.add(integracion)
        return integracion

    async def obtener_integracion(self, id: str) -> Integracion | None:
        return await self.integraciones_repo.get(id)

    async def listar_integraciones(self, propiedad_id: str, activo: bool | None = None) -> list[Integracion]:
        return await self.integraciones_repo.list_by_propiedad(propiedad_id, activo)

    async def actualizar_integracion(self, integracion: Integracion) -> Integracion:
        await self.integraciones_repo.update(integracion)
        return integracion

    async def eliminar_integracion(self, id: str) -> None:
        await self.integraciones_repo.delete(id)

    # --- Sincronización ---

    async def sincronizar_todas(self) -> int:
        return await self.sync.sincronizar_todas()

    async def sincronizar_integracion(self, integracion_id: str) -> Any:
        integracion = await self.integraciones_repo.get(integracion_id)
        if not integracion:
            raise ValueError("Integración no encontrada")
        return await self.sync.sincronizar(integracion)

    # --- Reportes ---

    async def reporte(
        self,
        *,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: str = "DIA",
    ) -> Any:
        from app.shared.enums import Grano
        return await self.reports.reporte(
            sitio_slug=sitio_slug,
            desde=desde,
            hasta=hasta,
            grano=Grano(grano),
        )
