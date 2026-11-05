"""Implementación MongoDB de los repositorios Agents."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.modules.agents.domain.models import Agente, EvidenciaVerificacion, IdentidadAgente, VisitaAgente
from app.shared.ids import ahora_utc
from app.modules.agents.persistence.repository import (
    AgenteRepository,
    EvidenciaRepository,
    IdentidadAgenteRepository,
    VisitaAgenteRepository,
)


COLECCION_AGENTES = "agentes"
COLECCION_IDENTIDADES = "agente_identidades"
COLECCION_VISITAS = "agente_visitas"
COLECCION_EVIDENCIAS = "agente_evidencias"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    # Agentes
    await db[COLECCION_AGENTES].create_indexes([
        IndexModel("nombre", unique=True),
        IndexModel("categoria"),
        IndexModel("activo"),
    ])

    # Identidades
    await db[COLECCION_IDENTIDADES].create_indexes([
        IndexModel([("agente_id", ASCENDING), ("verificado_en", DESCENDING)]),
        IndexModel([("ip_hash", ASCENDING), ("ua_declarado", ASCENDING)], unique=True),
        IndexModel("verificado"),
    ])

    # Visitas
    await db[COLECCION_VISITAS].create_indexes([
        IndexModel([("propiedad_id", ASCENDING), ("ocurrio_en", DESCENDING)]),
        IndexModel([("propiedad_id", ASCENDING), ("agente_id", ASCENDING), ("ocurrio_en", DESCENDING)]),
        IndexModel([("propiedad_id", ASCENDING), ("categoria", ASCENDING), ("ocurrio_en", DESCENDING)]),
        IndexModel([("propiedad_id", ASCENDING), ("verificado", ASCENDING), ("ocurrio_en", DESCENDING)]),
    ])

    # Evidencias
    await db[COLECCION_EVIDENCIAS].create_indexes([
        IndexModel("identidad_id"),
    ])


class MongoAgenteRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_AGENTES]

    async def add(self, agente: Agente) -> None:
        await self.col.insert_one(self._to_doc(agente))

    async def get(self, id: str) -> Agente | None:
        doc = await self.col.find_one({"_id": id})
        return self._from_doc(doc) if doc else None

    async def get_by_nombre(self, nombre: str) -> Agente | None:
        doc = await self.col.find_one({"nombre": nombre})
        return self._from_doc(doc) if doc else None

    async def list(self, activo: bool | None = None) -> list[Agente]:
        filtro = {}
        if activo is not None:
            filtro["activo"] = activo
        cursor = self.col.find(filtro).sort("nombre", ASCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def update(self, agente: Agente) -> None:
        agente.actualizado_en = ahora_utc()
        await self.col.replace_one({"_id": agente.id}, self._to_doc(agente))

    async def delete(self, id: str) -> None:
        await self.col.delete_one({"_id": id})

    def _to_doc(self, agente: Agente) -> dict[str, Any]:
        return {
            "_id": agente.id,
            "nombre": agente.nombre,
            "categoria": agente.categoria,
            "patrones_ua": agente.patrones_ua,
            "rangos_ip": agente.rangos_ip,
            "dns_sufijos": agente.dns_sufijos,
            "verifica_firma": agente.verifica_firma,
            "notas": agente.notas,
            "activo": agente.activo,
            "creado_en": agente.creado_en,
            "actualizado_en": agente.actualizado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> Agente:
        return Agente(
            id=doc["_id"],
            nombre=doc["nombre"],
            categoria=doc["categoria"],
            patrones_ua=doc.get("patrones_ua", []),
            rangos_ip=doc.get("rangos_ip", []),
            dns_sufijos=doc.get("dns_sufijos", []),
            verifica_firma=doc.get("verifica_firma", False),
            notas=doc.get("notas", ""),
            activo=doc.get("activo", True),
            creado_en=doc.get("creado_en", ahora_utc()),
            actualizado_en=doc.get("actualizado_en", ahora_utc()),
        )


class MongoIdentidadAgenteRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_IDENTIDADES]

    async def add(self, identidad: IdentidadAgente) -> None:
        await self.col.insert_one(self._to_doc(identidad))

    async def get(self, id: str) -> IdentidadAgente | None:
        doc = await self.col.find_one({"_id": id})
        return self._from_doc(doc) if doc else None

    async def get_by_ip_hash_ua(self, ip_hash: str, ua: str) -> IdentidadAgente | None:
        doc = await self.col.find_one({"ip_hash": ip_hash, "ua_declarado": ua})
        return self._from_doc(doc) if doc else None

    async def list_by_agente(self, agente_id: str, limite: int = 100) -> list[IdentidadAgente]:
        cursor = (
            self.col.find({"agente_id": agente_id})
            .sort("verificado_en", DESCENDING)
            .limit(limite)
        )
        return [self._from_doc(doc) async for doc in cursor]

    async def update(self, identidad: IdentidadAgente) -> None:
        await self.col.replace_one({"_id": identidad.id}, self._to_doc(identidad))

    def _to_doc(self, identidad: IdentidadAgente) -> dict[str, Any]:
        return {
            "_id": identidad.id,
            "agente_id": identidad.agente_id,
            "ip_hash": identidad.ip_hash,
            "ua_declarado": identidad.ua_declarado,
            "categoria_declarada": identidad.categoria_declarada,
            "dns_confirmado": identidad.dns_confirmado,
            "dns_detalle": identidad.dns_detalle,
            "ip_range_confirmado": identidad.ip_range_confirmado,
            "ip_range_detalle": identidad.ip_range_detalle,
            "firma_verificada": identidad.firma_verificada,
            "firma_detalle": identidad.firma_detalle,
            "verificado": identidad.verificado,
            "confianza": identidad.confianza,
            "verificado_en": identidad.verificado_en,
            "creado_en": identidad.creado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> IdentidadAgente:
        return IdentidadAgente(
            id=doc["_id"],
            agente_id=doc["agente_id"],
            ip_hash=doc["ip_hash"],
            ua_declarado=doc["ua_declarado"],
            categoria_declarada=doc["categoria_declarada"],
            dns_confirmado=doc.get("dns_confirmado", False),
            dns_detalle=doc.get("dns_detalle", ""),
            ip_range_confirmado=doc.get("ip_range_confirmado", False),
            ip_range_detalle=doc.get("ip_range_detalle", ""),
            firma_verificada=doc.get("firma_verificada", False),
            firma_detalle=doc.get("firma_detalle", ""),
            verificado=doc.get("verificado", False),
            confianza=doc.get("confianza", 0.0),
            verificado_en=doc.get("verificado_en"),
            creado_en=doc.get("creado_en", ahora_utc()),
        )


class MongoVisitaAgenteRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_VISITAS]

    async def add_many(self, visitas: list[VisitaAgente]) -> tuple[int, int]:
        if not visitas:
            return 0, 0
        docs = [self._to_doc(v) for v in visitas]
        try:
            await self.col.insert_many(docs, ordered=False)
            return len(docs), 0
        except Exception:
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
        agente_id: str | None = None,
        categoria: str | None = None,
        verificado: bool | None = None,
    ) -> list[VisitaAgente]:
        filtro: dict[str, Any] = {
            "propiedad_id": propiedad_id,
            "ocurrio_en": {"$gte": desde, "$lte": hasta},
        }
        if agente_id:
            filtro["agente_id"] = agente_id
        if categoria:
            filtro["categoria"] = categoria
        if verificado is not None:
            filtro["verificado"] = verificado
        cursor = self.col.find(filtro).sort("ocurrio_en", ASCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def contar_por_categoria(
        self, propiedad_id: str, desde: datetime, hasta: datetime
    ) -> dict[str, int]:
        pipeline = [
            {"$match": {"propiedad_id": propiedad_id, "ocurrio_en": {"$gte": desde, "$lte": hasta}}},
            {"$group": {"_id": "$categoria", "count": {"$sum": 1}}},
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

    def _to_doc(self, visita: VisitaAgente) -> dict[str, Any]:
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
            "identidad_id": visita.identidad_id,
            "categoria": visita.categoria,
            "verificado": visita.verificado,
            "confianza": visita.confianza,
            "evidencia_dns": visita.evidencia_dns,
            "evidencia_ip_range": visita.evidencia_ip_range,
            "evidencia_firma": visita.evidencia_firma,
            "creado_en": visita.creado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> VisitaAgente:
        return VisitaAgente(
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
            identidad_id=doc.get("identidad_id"),
            categoria=doc.get("categoria", "desconocido"),
            verificado=doc.get("verificado", False),
            confianza=doc.get("confianza", 0.0),
            evidencia_dns=doc.get("evidencia_dns", False),
            evidencia_ip_range=doc.get("evidencia_ip_range", False),
            evidencia_firma=doc.get("evidencia_firma", False),
            creado_en=doc.get("creado_en", doc["ocurrio_en"]),
        )


class MongoEvidenciaRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_EVIDENCIAS]

    async def add(self, evidencia: EvidenciaVerificacion) -> None:
        await self.col.insert_one(self._to_doc(evidencia))

    async def list_by_identidad(self, identidad_id: str) -> list[EvidenciaVerificacion]:
        cursor = self.col.find({"identidad_id": identidad_id}).sort("creado_en", ASCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    def _to_doc(self, evidencia: EvidenciaVerificacion) -> dict[str, Any]:
        return {
            "_id": evidencia.id,
            "identidad_id": evidencia.identidad_id,
            "tipo": evidencia.tipo,
            "exitosa": evidencia.exitosa,
            "detalle": evidencia.detalle,
            "datos_crudos": evidencia.datos_crudos,
            "creado_en": evidencia.creado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> EvidenciaVerificacion:
        return EvidenciaVerificacion(
            id=doc["_id"],
            identidad_id=doc["identidad_id"],
            tipo=doc["tipo"],
            exitosa=doc["exitosa"],
            detalle=doc["detalle"],
            datos_crudos=doc.get("datos_crudos", {}),
            creado_en=doc.get("creado_en", ahora_utc()),
        )
