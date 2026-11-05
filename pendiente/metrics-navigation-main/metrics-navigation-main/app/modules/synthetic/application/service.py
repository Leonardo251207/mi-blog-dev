"""Servicio principal del módulo Synthetic."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.modules.synthetic.application.reports import SondaReportsService
from app.modules.synthetic.application.runner import SondaRunner
from app.modules.synthetic.domain.models import Sonda
from app.modules.synthetic.persistence.repository import (
    EjecucionSondaRepository,
    MetricaSondaRepository,
    SondaRepository,
)
from app.modules.properties.application.services import PropertiesService


class SyntheticService:
    """Coordina sondas, ejecuciones y reportes."""

    def __init__(
        self,
        properties: PropertiesService,
        sondas: SondaRepository,
        ejecuciones: EjecucionSondaRepository,
        metricas: MetricaSondaRepository,
    ) -> None:
        self.properties = properties
        self.sondas_repo = sondas
        self.ejecuciones_repo = ejecuciones
        self.metricas_repo = metricas
        self.runner = SondaRunner(sondas, ejecuciones)
        self.reports = SondaReportsService(properties, sondas, ejecuciones, metricas)

    async def close(self) -> None:
        """Cierra recursos del runner."""
        await self.runner.close()

    # --- CRUD Sondas ---

    async def crear_sonda(self, sonda: Sonda) -> Sonda:
        await self.sondas_repo.add(sonda)
        return sonda

    async def obtener_sonda(self, id: str) -> Sonda | None:
        return await self.sondas_repo.get(id)

    async def listar_sondas(self, propiedad_id: str, activo: bool | None = None) -> list[Sonda]:
        return await self.sondas_repo.list_by_propiedad(propiedad_id, activo)

    async def actualizar_sonda(self, sonda: Sonda) -> Sonda:
        await self.sondas_repo.update(sonda)
        return sonda

    async def eliminar_sonda(self, id: str) -> None:
        await self.sondas_repo.delete(id)

    # --- Ejecución ---

    async def ejecutar_todas(self) -> int:
        return await self.runner.ejecutar_todas()

    async def ejecutar_sonda(self, sonda_id: str) -> Any:
        sonda = await self.sondas_repo.get(sonda_id)
        if not sonda:
            raise ValueError("Sonda no encontrada")
        return await self.runner.ejecutar(sonda)

    # --- Reportes ---

    async def reporte(
        self,
        *,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: str = "HORA",
    ) -> Any:
        from app.shared.enums import Grano
        return await self.reports.reporte(
            sitio_slug=sitio_slug,
            desde=desde,
            hasta=hasta,
            grano=Grano(grano),
        )

    async def materializar_metricas(self, sitio_slug: str, grano: str = "HORA") -> int:
        from app.shared.enums import Grano
        return await self.reports.materializar_metricas(
            sitio_slug=sitio_slug,
            grano=Grano(grano),
        )
