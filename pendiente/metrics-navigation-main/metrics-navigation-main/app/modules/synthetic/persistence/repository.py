"""Puertos de persistencia del contexto Synthetic."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.modules.synthetic.domain.models import EjecucionSonda, MetricaSonda, Sonda


class SondaRepository(Protocol):
    async def add(self, sonda: Sonda) -> None: ...
    async def get(self, id: str) -> Sonda | None: ...
    async def list_by_propiedad(self, propiedad_id: str, activo: bool | None = None) -> list[Sonda]: ...
    async def list_activas(self) -> list[Sonda]: ...
    async def update(self, sonda: Sonda) -> None: ...
    async def delete(self, id: str) -> None: ...


class EjecucionSondaRepository(Protocol):
    async def add(self, ejecucion: EjecucionSonda) -> None: ...
    async def list(
        self,
        sonda_id: str,
        desde: datetime,
        hasta: datetime,
        limite: int = 1000,
    ) -> list[EjecucionSonda]: ...
    async def ultima(self, sonda_id: str) -> EjecucionSonda | None: ...


class MetricaSondaRepository(Protocol):
    async def upsert(self, metrica: MetricaSonda) -> None: ...
    async def list(
        self,
        propiedad_id: str,
        desde: datetime,
        hasta: datetime,
        grano: str,
    ) -> list[MetricaSonda]: ...
    async def get(self, sonda_id: str, cubo: datetime, grano: str) -> MetricaSonda | None: ...