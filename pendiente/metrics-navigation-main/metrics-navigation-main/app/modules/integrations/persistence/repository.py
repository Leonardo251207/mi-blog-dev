"""Puertos de persistencia del contexto Integrations."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.modules.integrations.domain.models import EjecucionSincronizacion, Integracion, MetricaIntegracion


class IntegracionRepository(Protocol):
    async def add(self, integracion: Integracion) -> None: ...
    async def get(self, id: str) -> Integracion | None: ...
    async def list_by_propiedad(self, propiedad_id: str, activo: bool | None = None) -> list[Integracion]: ...
    async def list_activas(self) -> list[Integracion]: ...
    async def update(self, integracion: Integracion) -> None: ...
    async def delete(self, id: str) -> None: ...


class EjecucionSincronizacionRepository(Protocol):
    async def add(self, ejecucion: EjecucionSincronizacion) -> None: ...
    async def list(
        self,
        integracion_id: str,
        desde: datetime,
        hasta: datetime,
        limite: int = 100,
    ) -> list[EjecucionSincronizacion]: ...
    async def ultima(self, integracion_id: str) -> EjecucionSincronizacion | None: ...


class MetricaIntegracionRepository(Protocol):
    async def add_many(self, metricas: list[MetricaIntegracion]) -> tuple[int, int]: ...
    async def list(
        self,
        propiedad_id: str,
        desde: datetime,
        hasta: datetime,
        nombre_metrica: str | None = None,
    ) -> list[MetricaIntegracion]: ...
    async def upsert_many(self, metricas: list[MetricaIntegracion]) -> tuple[int, int]: ...