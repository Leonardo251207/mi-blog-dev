"""Adaptador MongoDB para propiedades, dominios y canales."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.properties.domain.models import Canal, Dominio, Propiedad
from app.shared.mongo import from_doc, to_doc


class MongoPropiedadRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["propiedades"]

    async def add(self, propiedad: Propiedad) -> None:
        await self.col.insert_one(to_doc(propiedad))

    async def get(self, id: str) -> Propiedad | None:
        doc = await self.col.find_one({"_id": id})
        return from_doc(doc, Propiedad) if doc else None

    async def get_by_slug(self, slug: str) -> Propiedad | None:
        doc = await self.col.find_one({"slug": slug})
        return from_doc(doc, Propiedad) if doc else None

    async def list(self) -> list[Propiedad]:
        return [from_doc(doc, Propiedad) async for doc in self.col.find().sort("slug", 1)]

    async def update(self, propiedad: Propiedad) -> None:
        await self.col.replace_one({"_id": propiedad.id}, to_doc(propiedad))


class MongoDominioRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["dominios"]

    async def add(self, dominio: Dominio) -> None:
        await self.col.insert_one(to_doc(dominio))

    async def get(self, id: str) -> Dominio | None:
        doc = await self.col.find_one({"_id": id})
        return from_doc(doc, Dominio) if doc else None

    async def list_by_propiedad(self, propiedad_id: str) -> list[Dominio]:
        cursor = self.col.find({"propiedad_id": propiedad_id}).sort("creado_en", 1)
        return [from_doc(doc, Dominio) async for doc in cursor]

    async def get_by_host(self, propiedad_id: str, host: str) -> Dominio | None:
        doc = await self.col.find_one(
            {"propiedad_id": propiedad_id, "host": host, "estado": {"$ne": "RETIRADO"}}
        )
        return from_doc(doc, Dominio) if doc else None

    async def update(self, dominio: Dominio) -> None:
        await self.col.replace_one({"_id": dominio.id}, to_doc(dominio))

    async def quitar_canonico(self, propiedad_id: str) -> None:
        await self.col.update_many(
            {"propiedad_id": propiedad_id, "es_canonico": True},
            {"$set": {"es_canonico": False}},
        )

    async def contar_verificados(self, propiedad_id: str) -> int:
        return await self.col.count_documents(
            {"propiedad_id": propiedad_id, "estado": "VERIFICADO"}
        )


class MongoCanalRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["canales_captura"]

    @staticmethod
    def _documento(canal: Canal) -> dict:
        documento = to_doc(canal)
        # Un índice unique+sparse indexa los `null`; si el canal no tiene clave
        # pública (por ejemplo, edge), el campo debe estar ausente, no en `None`.
        if documento.get("clave_publica_hash") is None:
            documento.pop("clave_publica_hash", None)
        return documento

    async def add(self, canal: Canal) -> None:
        await self.col.insert_one(self._documento(canal))

    async def get(self, id: str) -> Canal | None:
        doc = await self.col.find_one({"_id": id})
        return from_doc(doc, Canal) if doc else None

    async def list_by_propiedad(self, propiedad_id: str) -> list[Canal]:
        cursor = self.col.find({"propiedad_id": propiedad_id}).sort("creado_en", 1)
        return [from_doc(doc, Canal) async for doc in cursor]

    async def get_by_key_hash(self, clave_hash: str) -> Canal | None:
        doc = await self.col.find_one({"clave_publica_hash": clave_hash})
        return from_doc(doc, Canal) if doc else None

    async def get_by_tipo(self, propiedad_id: str, tipo: str) -> Canal | None:
        doc = await self.col.find_one({"propiedad_id": propiedad_id, "tipo": tipo})
        return from_doc(doc, Canal) if doc else None

    async def update(self, canal: Canal) -> None:
        await self.col.replace_one({"_id": canal.id}, self._documento(canal))


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db["propiedades"].create_index("slug", unique=True)
    await db["dominios"].create_index([("propiedad_id", 1), ("host", 1)])
    await db["dominios"].create_index([("propiedad_id", 1), ("estado", 1)])
    await db["canales_captura"].create_index("clave_publica_hash", unique=True, sparse=True)
    await db["canales_captura"].create_index([("propiedad_id", 1), ("tipo", 1)])
