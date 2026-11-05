"""Puertos de persistencia del contexto Edge."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.modules.edge.domain.models import EdgeVisit


class EdgeVisitRepository(Protocol):
    async def add_many(self, visitas: list[EdgeVisit]) -> tuple[int, int]: ...
    async def list(
        self,
        propiedad_id: str,
        desde: datetime,
        hasta: datetime,
        ruta: str | None = None,
        agente_categoria: str | None = None,
    ) -> list[EdgeVisit]: ...
    async def contar_por_categoria(
        self, propiedad_id: str, desde: datetime, hasta: datetime
    ) -> dict[str, int]: ...
    async def top_agentes(
        self, propiedad_id: str, desde: datetime, hasta: datetime, limite: int = 10
    ) -> list[tuple[str, int]]: ...
    async def top_rutas(
        self, propiedad_id: str, desde: datetime, hasta: datetime, limite: int = 10
    ) -> list[tuple[str, int]]: ...
    async def ultimas_por_agente(
        self, propiedad_id: str, agente_id: str, limite: int = 100
    ) -> list[EdgeVisit]: ...