"""Implementación MongoDB de los repositorios Alerts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.modules.alerts.domain.models import CanalNotificacion, Notificacion, ReglaAlerta
from app.shared.ids import ahora_utc
from app.modules.alerts.persistence.repository import (
    CanalNotificacionRepository,
    NotificacionRepository,
    ReglaAlertaRepository,
)


COLECCION_REGLAS = "alertas_reglas"
COLECCION_CANALES = "alertas_canales"
COLECCION_NOTIFICACIONES = "alertas_notificaciones"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    # Reglas
    await db[COLECCION_REGLAS].create_indexes([
        IndexModel([("propiedad_id", ASCENDING), ("estado", ASCENDING)]),
        IndexModel([("estado", ASCENDING), ("ultima_evaluacion_en", ASCENDING)]),
    ])

    # Canales
    await db[COLECCION_CANALES].create_indexes([
        IndexModel("estado"),
    ])

    # Notificaciones
    await db[COLECCION_NOTIFICACIONES].create_indexes([
        IndexModel([("estado", ASCENDING), ("proximo_intento_en", ASCENDING)]),
        IndexModel([("regla_id", ASCENDING), ("ocurrio_en", DESCENDING)]),
        IndexModel([("clave_deduplicacion", ASCENDING), ("ocurrio_en", DESCENDING)]),
    ])


class MongoReglaAlertaRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_REGLAS]

    async def add(self, regla: ReglaAlerta) -> None:
        await self.col.insert_one(self._to_doc(regla))

    async def get(self, id: str) -> ReglaAlerta | None:
        doc = await self.col.find_one({"_id": id})
        return self._from_doc(doc) if doc else None

    async def list_by_propiedad(self, propiedad_id: str, estado: str | None = None) -> list[ReglaAlerta]:
        filtro = {"propiedad_id": propiedad_id}
        if estado:
            filtro["estado"] = estado
        cursor = self.col.find(filtro).sort("creado_en", DESCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def list_activas(self) -> list[ReglaAlerta]:
        cursor = self.col.find({"estado": "ACTIVA"}).sort("ultima_evaluacion_en", ASCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def update(self, regla: ReglaAlerta) -> None:
        regla.actualizado_en = ahora_utc()
        await self.col.replace_one({"_id": regla.id}, self._to_doc(regla))

    async def delete(self, id: str) -> None:
        await self.col.delete_one({"_id": id})

    def _to_doc(self, regla: ReglaAlerta) -> dict[str, Any]:
        return {
            "_id": regla.id,
            "propiedad_id": regla.propiedad_id,
            "nombre": regla.nombre,
            "tipo": regla.tipo,
            "metrica": regla.metrica,
            "condicion": regla.condicion,
            "ventana": regla.ventana,
            "agregacion": regla.agregacion,
            "severidad": regla.severidad,
            "canales_notificacion": regla.canales_notificacion,
            "silencio_minutos": regla.silencio_minutos,
            "estado": regla.estado,
            "ultima_evaluacion_en": regla.ultima_evaluacion_en,
            "ultima_disparo_en": regla.ultima_disparo_en,
            "creado_en": regla.creado_en,
            "actualizado_en": regla.actualizado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> ReglaAlerta:
        return ReglaAlerta(
            id=doc["_id"],
            propiedad_id=doc["propiedad_id"],
            nombre=doc["nombre"],
            tipo=doc["tipo"],
            metrica=doc["metrica"],
            condicion=doc["condicion"],
            ventana=doc["ventana"],
            agregacion=doc.get("agregacion", "sum"),
            severidad=doc.get("severidad", "AVISO"),
            canales_notificacion=doc.get("canales_notificacion", []),
            silencio_minutos=doc.get("silencio_minutos", 30),
            estado=doc.get("estado", "ACTIVA"),
            ultima_evaluacion_en=doc.get("ultima_evaluacion_en"),
            ultima_disparo_en=doc.get("ultima_disparo_en"),
            creado_en=doc.get("creado_en", ahora_utc()),
            actualizado_en=doc.get("actualizado_en", ahora_utc()),
        )


class MongoCanalNotificacionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_CANALES]

    async def add(self, canal: CanalNotificacion) -> None:
        await self.col.insert_one(self._to_doc(canal))

    async def get(self, id: str) -> CanalNotificacion | None:
        doc = await self.col.find_one({"_id": id})
        return self._from_doc(doc) if doc else None

    async def list(self, estado: str | None = None) -> list[CanalNotificacion]:
        filtro = {}
        if estado:
            filtro["estado"] = estado
        cursor = self.col.find(filtro).sort("creado_en", DESCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def update(self, canal: CanalNotificacion) -> None:
        await self.col.replace_one({"_id": canal.id}, self._to_doc(canal))

    async def delete(self, id: str) -> None:
        await self.col.delete_one({"_id": id})

    def _to_doc(self, canal: CanalNotificacion) -> dict[str, Any]:
        return {
            "_id": canal.id,
            "tipo": canal.tipo,
            "nombre": canal.nombre,
            "config": canal.config,
            "estado": canal.estado,
            "ultima_entrega_en": canal.ultima_entrega_en,
            "creado_en": canal.creado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> CanalNotificacion:
        return CanalNotificacion(
            id=doc["_id"],
            tipo=doc["tipo"],
            nombre=doc["nombre"],
            config=doc.get("config", {}),
            estado=doc.get("estado", "ACTIVO"),
            ultima_entrega_en=doc.get("ultima_entrega_en"),
            creado_en=doc.get("creado_en", ahora_utc()),
        )


class MongoNotificacionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_NOTIFICACIONES]

    async def add(self, notificacion: Notificacion) -> None:
        await self.col.insert_one(self._to_doc(notificacion))

    async def get(self, id: str) -> Notificacion | None:
        doc = await self.col.find_one({"_id": id})
        return self._from_doc(doc) if doc else None

    async def list_pendientes(self, limite: int = 100) -> list[Notificacion]:
        cursor = (
            self.col.find({"estado": "PENDIENTE"})
            .sort("proximo_intento_en", ASCENDING)
            .limit(limite)
        )
        return [self._from_doc(doc) async for doc in cursor]

    async def list_por_regla(self, regla_id: str, limite: int = 50) -> list[Notificacion]:
        cursor = (
            self.col.find({"regla_id": regla_id})
            .sort("ocurrio_en", DESCENDING)
            .limit(limite)
        )
        return [self._from_doc(doc) async for doc in cursor]

    async def update(self, notificacion: Notificacion) -> None:
        await self.col.replace_one({"_id": notificacion.id}, self._to_doc(notificacion))

    async def contar_por_clave_deduplicacion(self, clave: str, desde: datetime) -> int:
        return await self.col.count_documents({
            "clave_deduplicacion": clave,
            "ocurrio_en": {"$gte": desde},
        })

    def _to_doc(self, notificacion: Notificacion) -> dict[str, Any]:
        return {
            "_id": notificacion.id,
            "regla_id": notificacion.regla_id,
            "canal_id": notificacion.canal_id,
            "ocurrio_en": notificacion.ocurrio_en,
            "titulo": notificacion.titulo,
            "cuerpo": notificacion.cuerpo,
            "severidad": notificacion.severidad,
            "estado": notificacion.estado,
            "intentos": notificacion.intentos,
            "proximo_intento_en": notificacion.proximo_intento_en,
            "clave_deduplicacion": notificacion.clave_deduplicacion,
            "error_ultimo_intento": notificacion.error_ultimo_intento,
            "creado_en": notificacion.creado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> Notificacion:
        return Notificacion(
            id=doc["_id"],
            regla_id=doc["regla_id"],
            canal_id=doc["canal_id"],
            ocurrio_en=doc["ocurrio_en"],
            titulo=doc["titulo"],
            cuerpo=doc["cuerpo"],
            severidad=doc["severidad"],
            estado=doc.get("estado", "PENDIENTE"),
            intentos=doc.get("intentos", 0),
            proximo_intento_en=doc.get("proximo_intento_en"),
            clave_deduplicacion=doc["clave_deduplicacion"],
            error_ultimo_intento=doc.get("error_ultimo_intento"),
            creado_en=doc.get("creado_en", ahora_utc()),
        )
