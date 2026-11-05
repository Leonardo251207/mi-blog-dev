"""Adaptador MongoDB para eventos de navegación."""

from __future__ import annotations

from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.navigation.domain.models import EventoNavegacion
from app.shared.mongo import from_doc, to_doc


class MongoEventoRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["eventos_navegacion"]

    async def add_many(self, eventos: list[EventoNavegacion]) -> tuple[int, int]:
        insertados = 0
        for evento in eventos:
            documento = to_doc(evento)
            # El `_id` lo aporta el filtro del upsert; repetirlo en `$setOnInsert`
            # hace que MongoDB real rechace la escritura sobre un campo inmutable.
            documento.pop("_id", None)
            resultado = await self.col.update_one(
                {"_id": evento.id_evento},
                {"$setOnInsert": documento},
                upsert=True,
            )
            if resultado.upserted_id is not None:
                insertados += 1
        return insertados, len(eventos) - insertados

    async def list(
        self,
        propiedad_id: str,
        desde: datetime,
        hasta: datetime,
        ruta: str | None = None,
    ) -> list[EventoNavegacion]:
        consulta: dict = {
            "propiedad_id": propiedad_id,
            "ocurrio_en": {"$gte": desde, "$lte": hasta},
        }
        if ruta:
            consulta["ruta_patron"] = ruta
        cursor = self.col.find(consulta).sort("ocurrio_en", 1)
        return [from_doc(doc, EventoNavegacion) async for doc in cursor]

    async def ultimo(self, propiedad_id: str) -> EventoNavegacion | None:
        doc = await self.col.find_one(
            {"propiedad_id": propiedad_id},
            sort=[("ocurrio_en", -1)],
        )
        return from_doc(doc, EventoNavegacion) if doc else None


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    coleccion = db["eventos_navegacion"]
    await coleccion.create_index("id_evento", unique=True)
    await coleccion.create_index([("propiedad_id", 1), ("ocurrio_en", -1)])
    try:
        await coleccion.create_index("ocurrio_en", expireAfterSeconds=90 * 24 * 60 * 60)
    except Exception:
        # mongomock no implementa TTL; en MongoDB real el índice se crea sin problema.
        pass
