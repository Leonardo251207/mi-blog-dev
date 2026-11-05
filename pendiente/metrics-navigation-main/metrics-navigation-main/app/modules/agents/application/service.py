"""Servicio de aplicación para administración y consulta del catálogo de agentes."""

from __future__ import annotations

from app.modules.agents.domain.models import Agente
from app.modules.agents.persistence.repository import AgenteRepository
from app.shared.errors import NotFound
from app.shared.ids import ahora_utc


class AgenteAdminService:
    """Gestiona el catálogo de agentes (casos de uso administrativos)."""

    def __init__(self, agentes: AgenteRepository) -> None:
        self.agentes = agentes

    async def listar_agentes(self, activo: bool | None = None) -> list[Agente]:
        return await self.agentes.list(activo=activo)

    async def obtener_agente(self, id: str) -> Agente | None:
        return await self.agentes.get(id)

    async def crear_agente(
        self,
        *,
        nombre: str,
        categoria: str,
        patrones_ua: list[str] | None = None,
        rangos_ip: list[str] | None = None,
        dns_sufijos: list[str] | None = None,
        verifica_firma: bool = False,
        notas: str = "",
    ) -> Agente:
        agente = Agente(
            nombre=nombre,
            categoria=categoria,
            patrones_ua=patrones_ua or [],
            rangos_ip=rangos_ip or [],
            dns_sufijos=dns_sufijos or [],
            verifica_firma=verifica_firma,
            notas=notas,
        )
        await self.agentes.add(agente)
        return agente

    async def actualizar_agente(
        self,
        agente_id: str,
        *,
        nombre: str,
        categoria: str,
        patrones_ua: list[str] | None = None,
        rangos_ip: list[str] | None = None,
        dns_sufijos: list[str] | None = None,
        verifica_firma: bool = False,
        notas: str = "",
    ) -> Agente:
        agente = await self.agentes.get(agente_id)
        if not agente:
            raise NotFound("AGENTE_NO_ENCONTRADO", f"No existe el agente con id `{agente_id}`.")
        agente.nombre = nombre
        agente.categoria = categoria
        agente.patrones_ua = patrones_ua or []
        agente.rangos_ip = rangos_ip or []
        agente.dns_sufijos = dns_sufijos or []
        agente.verifica_firma = verifica_firma
        agente.notas = notas
        agente.actualizado_en = ahora_utc()
        await self.agentes.update(agente)
        return agente

    async def eliminar_agente(self, agente_id: str) -> None:
        await self.agentes.delete(agente_id)

    async def activar_agente(self, agente_id: str) -> Agente:
        agente = await self.agentes.get(agente_id)
        if not agente:
            raise NotFound("AGENTE_NO_ENCONTRADO", f"No existe el agente con id `{agente_id}`.")
        agente.activo = True
        agente.actualizado_en = ahora_utc()
        await self.agentes.update(agente)
        return agente

    async def desactivar_agente(self, agente_id: str) -> Agente:
        agente = await self.agentes.get(agente_id)
        if not agente:
            raise NotFound("AGENTE_NO_ENCONTRADO", f"No existe el agente con id `{agente_id}`.")
        agente.activo = False
        agente.actualizado_en = ahora_utc()
        await self.agentes.update(agente)
        return agente
