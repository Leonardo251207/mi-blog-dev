"""Puerto de persistencia de eventos de navegación."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.modules.navigation.domain.models import EventoNavegacion


class EventoRepository(Protocol):
    async def add_many(self, eventos: list[EventoNavegacion]) -> tuple[int, int]: ...
    async def list(
        self,
        propiedad_id: str,
        desde: datetime,
        hasta: datetime,
        ruta: str | None = None,
    ) -> list[EventoNavegacion]: ...
    async def ultimo(self, propiedad_id: str) -> EventoNavegacion | None: ...
