"""Implementación MongoDB del repositorio Edge."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.modules.edge.domain.models import EdgeVisit
from app.modules.edge.persistence.repository import EdgeVisitRepository
from app.shared.ids import hash_pseudonimo


COLECCION = "edge_visits"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    col = db[COLECCION]
    await col.create_indexes(
        [
            IndexModel([("propiedad_id", ASCENDING), ("ocurrio_en", DESCENDING)]),
            IndexModel([("propiedad_id", ASCENDING), ("agente_categoria", ASCENDING), ("ocurrio_en", DESCENDING)]),
            IndexModel([("propiedad_id", ASCENDING), ("ruta_patron", ASCENDING), ("ocurrio_en", DESCENDING)]),
            IndexModel([("propiedad_id", ASCENDING), ("status_code", ASCENDING), ("ocurrio_en", DESCENDING)]),
            IndexModel([("propiedad_id", ASCENDING), ("ip_hash", ASCENDING), ("ocurrio_en", DESCENDING)]),
            IndexModel([("canal_id", ASCENDING), ("ocurrio_en", DESCENDING)]),
        ]
    )


class MongoEdgeVisitRepository:
    def __init__(self, db: AsyncIOMotorDatabase, salt: str) -> None:
        self.col = db[COLECCION]
        self.salt = salt

    async def add_many(self, visitas: list[EdgeVisit]) -> tuple[int, int]:
        if not visitas:
            return 0, 0
        docs = [self._to_doc(v) for v in visitas]
        try:
            await self.col.insert_many(docs, ordered=False)
            return len(docs), 0
        except Exception:
            # Manejar duplicados por _id si los hay
            insertados = 0
            duplicados = 0
            for doc in docs:
                try:
                    await self.col.insert_one(doc)
                    insertados += 1
                except Exception:
                    duplicados += 1
            return insertados, duplicados

    async def list(
        self,
        propiedad_id: str,
        desde: datetime,
        hasta: datetime,
        ruta: str | None = None,
        agente_categoria: str | None = None,
    ) -> list[EdgeVisit]:
        filtro: dict[str, Any] = {
            "propiedad_id": propiedad_id,
            "ocurrio_en": {"$gte": desde, "$lte": hasta},
        }
        if ruta:
            filtro["ruta_patron"] = ruta
        if agente_categoria:
            filtro["agente_categoria"] = agente_categoria
        cursor = self.col.find(filtro).sort("ocurrio_en", ASCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def contar_por_categoria(
        self, propiedad_id: str, desde: datetime, hasta: datetime
    ) -> dict[str, int]:
        pipeline = [
            {"$match": {"propiedad_id": propiedad_id, "ocurrio_en": {"$gte": desde, "$lte": hasta}}},
            {"$group": {"_id": "$agente_categoria", "count": {"$sum": 1}}},
        ]
        resultado = {}
        async for doc in self.col.aggregate(pipeline):
            cat = doc["_id"] or "desconocido"
            resultado[cat] = doc["count"]
        return resultado

    async def top_agentes(
        self, propiedad_id: str, desde: datetime, hasta: datetime, limite: int = 10
    ) -> list[tuple[str, int]]:
        pipeline = [
            {"$match": {"propiedad_id": propiedad_id, "ocurrio_en": {"$gte": desde, "$lte": hasta}}},
            {"$group": {"_id": "$agente_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limite},
        ]
        resultado = []
        async for doc in self.col.aggregate(pipeline):
            agente = doc["_id"] or "desconocido"
            resultado.append((agente, doc["count"]))
        return resultado

    async def top_rutas(
        self, propiedad_id: str, desde: datetime, hasta: datetime, limite: int = 10
    ) -> list[tuple[str, int]]:
        pipeline = [
            {"$match": {"propiedad_id": propiedad_id, "ocurrio_en": {"$gte": desde, "$lte": hasta}}},
            {"$group": {"_id": "$ruta_patron", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limite},
        ]
        resultado = []
        async for doc in self.col.aggregate(pipeline):
            ruta = doc["_id"] or "/"
            resultado.append((ruta, doc["count"]))
        return resultado

    async def ultimas_por_agente(
        self, propiedad_id: str, agente_id: str, limite: int = 100
    ) -> list[EdgeVisit]:
        cursor = (
            self.col.find({"propiedad_id": propiedad_id, "agente_id": agente_id})
            .sort("ocurrio_en", DESCENDING)
            .limit(limite)
        )
        return [self._from_doc(doc) async for doc in cursor]

    def _to_doc(self, visita: EdgeVisit) -> dict[str, Any]:
        return {
            "_id": visita.id,
            "propiedad_id": visita.propiedad_id,
            "canal_id": visita.canal_id,
            "host": visita.host,
            "entorno": visita.entorno.value,
            "ocurrio_en": visita.ocurrio_en,
            "metodo": visita.metodo,
            "path": visita.path,
            "ruta_patron": visita.ruta_patron,
            "query_string": visita.query_string,
            "user_agent": visita.user_agent,
            "ip_hash": visita.ip_hash,
            "asn": visita.asn,
            "pais": visita.pais,
            "status_code": visita.status_code,
            "bytes_enviados": visita.bytes_enviados,
            "bytes_recibidos": visita.bytes_recibidos,
            "duracion_ms": visita.duracion_ms,
            "referrer": visita.referrer,
            "agente_id": visita.agente_id,
            "agente_categoria": visita.agente_categoria,
            "agente_verificado": visita.agente_verificado,
            "evidencia_dns": visita.evidencia_dns,
            "evidencia_ip_range": visita.evidencia_ip_range,
            "evidencia_firma": visita.evidencia_firma,
            "creado_en": visita.creado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> EdgeVisit:
        return EdgeVisit(
            id=doc["_id"],
            propiedad_id=doc["propiedad_id"],
            canal_id=doc["canal_id"],
            host=doc["host"],
            entorno=doc["entorno"],
            ocurrio_en=doc["ocurrio_en"],
            metodo=doc["metodo"],
            path=doc["path"],
            ruta_patron=doc["ruta_patron"],
            query_string=doc.get("query_string", ""),
            user_agent=doc["user_agent"],
            ip_hash=doc["ip_hash"],
            asn=doc.get("asn"),
            pais=doc.get("pais"),
            status_code=doc["status_code"],
            bytes_enviados=doc.get("bytes_enviados", 0),
            bytes_recibidos=doc.get("bytes_recibidos", 0),
            duracion_ms=doc.get("duracion_ms"),
            referrer=doc.get("referrer"),
            agente_id=doc.get("agente_id"),
            agente_categoria=doc.get("agente_categoria"),
            agente_verificado=doc.get("agente_verificado", False),
            evidencia_dns=doc.get("evidencia_dns", False),
            evidencia_ip_range=doc.get("evidencia_ip_range", False),
            evidencia_firma=doc.get("evidencia_firma", False),
            creado_en=doc.get("creado_en", doc["ocurrio_en"]),
        )