"""Implementación MongoDB de los repositorios Integrations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.modules.integrations.domain.models import EjecucionSincronizacion, Integracion, MetricaIntegracion
from app.shared.ids import ahora_utc
from app.modules.integrations.persistence.repository import (
    EjecucionSincronizacionRepository,
    IntegracionRepository,
    MetricaIntegracionRepository,
)


COLECCION_INTEGRACIONES = "integraciones"
COLECCION_EJECUCIONES = "integracion_ejecuciones"
COLECCION_METRICAS = "integracion_metricas"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    # Integraciones
    await db[COLECCION_INTEGRACIONES].create_indexes([
        IndexModel([("propiedad_id", ASCENDING), ("activo", ASCENDING)]),
        IndexModel([("tipo", ASCENDING), ("estado", ASCENDING)]),
    ])

    # Ejecuciones
    await db[COLECCION_EJECUCIONES].create_indexes([
        IndexModel([("integracion_id", ASCENDING), ("iniciado_en", DESCENDING)]),
        IndexModel([("propiedad_id", ASCENDING), ("iniciado_en", DESCENDING)]),
    ])

    # Métricas
    await db[COLECCION_METRICAS].create_indexes([
        IndexModel([("integracion_id", ASCENDING), ("fecha_dato", DESCENDING)]),
        IndexModel([("propiedad_id", ASCENDING), ("nombre", ASCENDING), ("fecha_dato", DESCENDING)]),
    ])


class MongoIntegracionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_INTEGRACIONES]

    async def add(self, integracion: Integracion) -> None:
        await self.col.insert_one(self._to_doc(integracion))

    async def get(self, id: str) -> Integracion | None:
        doc = await self.col.find_one({"_id": id})
        return self._from_doc(doc) if doc else None

    async def list_by_propiedad(self, propiedad_id: str, activo: bool | None = None) -> list[Integracion]:
        filtro = {"propiedad_id": propiedad_id}
        if activo is not None:
            filtro["activo"] = activo
        cursor = self.col.find(filtro).sort("creado_en", DESCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def list_activas(self) -> list[Integracion]:
        cursor = self.col.find({"activo": True, "estado": {"$ne": "DESHABILITADA"}}).sort("creado_en", ASCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def update(self, integracion: Integracion) -> None:
        integracion.actualizado_en = ahora_utc()
        await self.col.replace_one({"_id": integracion.id}, self._to_doc(integracion))

    async def delete(self, id: str) -> None:
        await self.col.delete_one({"_id": id})

    def _to_doc(self, integracion: Integracion) -> dict[str, Any]:
        return {
            "_id": integracion.id,
            "propiedad_id": integracion.propiedad_id,
            "tipo": integracion.tipo,
            "nombre": integracion.nombre,
            "credenciales_ref": integracion.credenciales_ref,
            "config": integracion.config,
            "estado": integracion.estado,
            "ultima_sincronizacion_en": integracion.ultima_sincronizacion_en,
            "ultima_sincronizacion_exitosa_en": integracion.ultima_sincronizacion_exitosa_en,
            "error_ultima_sincronizacion": integracion.error_ultima_sincronizacion,
            "intervalo_horas": integracion.intervalo_horas,
            "activo": integracion.activo,
            "creado_en": integracion.creado_en,
            "actualizado_en": integracion.actualizado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> Integracion:
        return Integracion(
            id=doc["_id"],
            propiedad_id=doc["propiedad_id"],
            tipo=doc["tipo"],
            nombre=doc["nombre"],
            credenciales_ref=doc["credenciales_ref"],
            config=doc.get("config", {}),
            estado=doc.get("estado", "PENDIENTE"),
            ultima_sincronizacion_en=doc.get("ultima_sincronizacion_en"),
            ultima_sincronizacion_exitosa_en=doc.get("ultima_sincronizacion_exitosa_en"),
            error_ultima_sincronizacion=doc.get("error_ultima_sincronizacion"),
            intervalo_horas=doc.get("intervalo_horas", 24),
            activo=doc.get("activo", True),
            creado_en=doc.get("creado_en", ahora_utc()),
            actualizado_en=doc.get("actualizado_en", ahora_utc()),
        )


class MongoEjecucionSincronizacionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_EJECUCIONES]

    async def add(self, ejecucion: EjecucionSincronizacion) -> None:
        await self.col.insert_one(self._to_doc(ejecucion))

    async def list(
        self,
        integracion_id: str,
        desde: datetime,
        hasta: datetime,
        limite: int = 100,
    ) -> list[EjecucionSincronizacion]:
        cursor = (
            self.col.find({
                "integracion_id": integracion_id,
                "iniciado_en": {"$gte": desde, "$lte": hasta},
            })
            .sort("iniciado_en", DESCENDING)
            .limit(limite)
        )
        return [self._from_doc(doc) async for doc in cursor]

    async def ultima(self, integracion_id: str) -> EjecucionSincronizacion | None:
        doc = await self.col.find_one({"integracion_id": integracion_id}, sort=[("iniciado_en", DESCENDING)])
        return self._from_doc(doc) if doc else None

    def _to_doc(self, ejecucion: EjecucionSincronizacion) -> dict[str, Any]:
        return {
            "_id": ejecucion.id,
            "integracion_id": ejecucion.integracion_id,
            "propiedad_id": ejecucion.propiedad_id,
            "iniciado_en": ejecucion.iniciado_en,
            "finalizado_en": ejecucion.finalizado_en,
            "exito": ejecucion.exito,
            "metricas_obtenidas": ejecucion.metricas_obtenidas,
            "error": ejecucion.error,
            "error_tipo": ejecucion.error_tipo,
            "datos_muestra": ejecucion.datos_muestra,
            "creado_en": ejecucion.creado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> EjecucionSincronizacion:
        return EjecucionSincronizacion(
            id=doc["_id"],
            integracion_id=doc["integracion_id"],
            propiedad_id=doc["propiedad_id"],
            iniciado_en=doc["iniciado_en"],
            finalizado_en=doc.get("finalizado_en"),
            exito=doc.get("exito", False),
            metricas_obtenidas=doc.get("metricas_obtenidas", 0),
            error=doc.get("error"),
            error_tipo=doc.get("error_tipo"),
            datos_muestra=doc.get("datos_muestra", {}),
            creado_en=doc.get("creado_en", ahora_utc()),
        )


class MongoMetricaIntegracionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_METRICAS]

    async def add_many(self, metricas: list[MetricaIntegracion]) -> tuple[int, int]:
        if not metricas:
            return 0, 0
        docs = [self._to_doc(m) for m in metricas]
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
        nombre_metrica: str | None = None,
    ) -> list[MetricaIntegracion]:
        filtro: dict[str, Any] = {
            "propiedad_id": propiedad_id,
            "fecha_dato": {"$gte": desde, "$lte": hasta},
        }
        if nombre_metrica:
            filtro["nombre"] = nombre_metrica
        cursor = self.col.find(filtro).sort("fecha_dato", ASCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def upsert_many(self, metricas: list[MetricaIntegracion]) -> tuple[int, int]:
        if not metricas:
            return 0, 0
        insertados = 0
        actualizados = 0
        for metrica in metricas:
            doc = self._to_doc(metrica)
            result = await self.col.replace_one(
                {"integracion_id": metrica.integracion_id, "nombre": metrica.nombre, "fecha_dato": metrica.fecha_dato},
                doc,
                upsert=True,
            )
            if result.upserted_id:
                insertados += 1
            else:
                actualizados += 1
        return insertados, actualizados

    def _to_doc(self, metrica: MetricaIntegracion) -> dict[str, Any]:
        return {
            "_id": metrica.id,
            "integracion_id": metrica.integracion_id,
            "propiedad_id": metrica.propiedad_id,
            "nombre": metrica.nombre,
            "valor": metrica.valor,
            "dimensiones": metrica.dimensiones,
            "fecha_dato": metrica.fecha_dato,
            "obtenido_en": metrica.obtenido_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> MetricaIntegracion:
        return MetricaIntegracion(
            id=doc["_id"],
            integracion_id=doc["integracion_id"],
            propiedad_id=doc["propiedad_id"],
            nombre=doc["nombre"],
            valor=doc["valor"],
            dimensiones=doc.get("dimensiones", {}),
            fecha_dato=doc["fecha_dato"],
            obtenido_en=doc.get("obtenido_en", ahora_utc()),
        )
