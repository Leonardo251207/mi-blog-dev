"""Implementación MongoDB de los repositorios Synthetic."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.modules.synthetic.domain.models import EjecucionSonda, MetricaSonda, Sonda
from app.shared.ids import ahora_utc
from app.modules.synthetic.persistence.repository import (
    EjecucionSondaRepository,
    MetricaSondaRepository,
    SondaRepository,
)


COLECCION_SONDAS = "sondas"
COLECCION_EJECUCIONES = "sonda_ejecuciones"
COLECCION_METRICAS = "sonda_metricas"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    # Sondas
    await db[COLECCION_SONDAS].create_indexes([
        IndexModel([("propiedad_id", ASCENDING), ("activo", ASCENDING)]),
    ])

    # Ejecuciones
    await db[COLECCION_EJECUCIONES].create_indexes([
        IndexModel([("sonda_id", ASCENDING), ("iniciado_en", DESCENDING)]),
        IndexModel([("propiedad_id", ASCENDING), ("iniciado_en", DESCENDING)]),
    ])

    # Métricas
    await db[COLECCION_METRICAS].create_indexes([
        IndexModel([("sonda_id", ASCENDING), ("cubo", ASCENDING), ("grano", ASCENDING)], unique=True),
        IndexModel([("propiedad_id", ASCENDING), ("cubo", ASCENDING), ("grano", ASCENDING)]),
    ])


class MongoSondaRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_SONDAS]

    async def add(self, sonda: Sonda) -> None:
        await self.col.insert_one(self._to_doc(sonda))

    async def get(self, id: str) -> Sonda | None:
        doc = await self.col.find_one({"_id": id})
        return self._from_doc(doc) if doc else None

    async def list_by_propiedad(self, propiedad_id: str, activo: bool | None = None) -> list[Sonda]:
        filtro = {"propiedad_id": propiedad_id}
        if activo is not None:
            filtro["activo"] = activo
        cursor = self.col.find(filtro).sort("creado_en", DESCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def list_activas(self) -> list[Sonda]:
        cursor = self.col.find({"activo": True}).sort("creado_en", ASCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def update(self, sonda: Sonda) -> None:
        sonda.actualizado_en = ahora_utc()
        await self.col.replace_one({"_id": sonda.id}, self._to_doc(sonda))

    async def delete(self, id: str) -> None:
        await self.col.delete_one({"_id": id})

    def _to_doc(self, sonda: Sonda) -> dict[str, Any]:
        return {
            "_id": sonda.id,
            "propiedad_id": sonda.propiedad_id,
            "nombre": sonda.nombre,
            "tipo": sonda.tipo,
            "objetivo": sonda.objetivo,
            "metodo": sonda.metodo,
            "headers": sonda.headers,
            "cuerpo": sonda.cuerpo,
            "esperado_status": sonda.esperado_status,
            "esperado_contiene": sonda.esperado_contiene,
            "verificar_certificado": sonda.verificar_certificado,
            "dias_alerta_expiracion": sonda.dias_alerta_expiracion,
            "intervalo_segundos": sonda.intervalo_segundos,
            "timeout_segundos": sonda.timeout_segundos,
            "regiones": sonda.regiones,
            "activo": sonda.activo,
            "creado_en": sonda.creado_en,
            "actualizado_en": sonda.actualizado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> Sonda:
        return Sonda(
            id=doc["_id"],
            propiedad_id=doc["propiedad_id"],
            nombre=doc["nombre"],
            tipo=doc["tipo"],
            objetivo=doc["objetivo"],
            metodo=doc.get("metodo", "GET"),
            headers=doc.get("headers", {}),
            cuerpo=doc.get("cuerpo"),
            esperado_status=doc.get("esperado_status", 200),
            esperado_contiene=doc.get("esperado_contiene"),
            verificar_certificado=doc.get("verificar_certificado", True),
            dias_alerta_expiracion=doc.get("dias_alerta_expiracion", 30),
            intervalo_segundos=doc.get("intervalo_segundos", 300),
            timeout_segundos=doc.get("timeout_segundos", 10),
            regiones=doc.get("regiones", ["default"]),
            activo=doc.get("activo", True),
            creado_en=doc.get("creado_en", ahora_utc()),
            actualizado_en=doc.get("actualizado_en", ahora_utc()),
        )


class MongoEjecucionSondaRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_EJECUCIONES]

    async def add(self, ejecucion: EjecucionSonda) -> None:
        await self.col.insert_one(self._to_doc(ejecucion))

    async def list(
        self,
        sonda_id: str,
        desde: datetime,
        hasta: datetime,
        limite: int = 1000,
    ) -> list[EjecucionSonda]:
        cursor = (
            self.col.find({
                "sonda_id": sonda_id,
                "iniciado_en": {"$gte": desde, "$lte": hasta},
            })
            .sort("iniciado_en", DESCENDING)
            .limit(limite)
        )
        return [self._from_doc(doc) async for doc in cursor]

    async def ultima(self, sonda_id: str) -> EjecucionSonda | None:
        doc = await self.col.find_one({"sonda_id": sonda_id}, sort=[("iniciado_en", DESCENDING)])
        return self._from_doc(doc) if doc else None

    def _to_doc(self, ejecucion: EjecucionSonda) -> dict[str, Any]:
        return {
            "_id": ejecucion.id,
            "sonda_id": ejecucion.sonda_id,
            "propiedad_id": ejecucion.propiedad_id,
            "region": ejecucion.region,
            "iniciado_en": ejecucion.iniciado_en,
            "finalizado_en": ejecucion.finalizado_en,
            "exito": ejecucion.exito,
            "status_code": ejecucion.status_code,
            "latencia_ms": ejecucion.latencia_ms,
            "dns_resuelto": ejecucion.dns_resuelto,
            "dns_latencia_ms": ejecucion.dns_latencia_ms,
            "ips_resueltas": ejecucion.ips_resueltas,
            "tcp_conectado": ejecucion.tcp_conectado,
            "tcp_latencia_ms": ejecucion.tcp_latencia_ms,
            "tls_establecido": ejecucion.tls_establecido,
            "tls_latencia_ms": ejecucion.tls_latencia_ms,
            "tls_version": ejecucion.tls_version,
            "cert_expira_en": ejecucion.cert_expira_en,
            "cert_dias_restantes": ejecucion.cert_dias_restantes,
            "error": ejecucion.error,
            "error_tipo": ejecucion.error_tipo,
            "respuesta_tamano": ejecucion.respuesta_tamano,
            "respuesta_headers": ejecucion.respuesta_headers,
            "creado_en": ejecucion.creado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> EjecucionSonda:
        return EjecucionSonda(
            id=doc["_id"],
            sonda_id=doc["sonda_id"],
            propiedad_id=doc["propiedad_id"],
            region=doc["region"],
            iniciado_en=doc["iniciado_en"],
            finalizado_en=doc.get("finalizado_en"),
            exito=doc.get("exito", False),
            status_code=doc.get("status_code"),
            latencia_ms=doc.get("latencia_ms"),
            dns_resuelto=doc.get("dns_resuelto", False),
            dns_latencia_ms=doc.get("dns_latencia_ms"),
            ips_resueltas=doc.get("ips_resueltas", []),
            tcp_conectado=doc.get("tcp_conectado", False),
            tcp_latencia_ms=doc.get("tcp_latencia_ms"),
            tls_establecido=doc.get("tls_establecido", False),
            tls_latencia_ms=doc.get("tls_latencia_ms"),
            tls_version=doc.get("tls_version"),
            cert_expira_en=doc.get("cert_expira_en"),
            cert_dias_restantes=doc.get("cert_dias_restantes"),
            error=doc.get("error"),
            error_tipo=doc.get("error_tipo"),
            respuesta_tamano=doc.get("respuesta_tamano"),
            respuesta_headers=doc.get("respuesta_headers", {}),
            creado_en=doc.get("creado_en", ahora_utc()),
        )


class MongoMetricaSondaRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db[COLECCION_METRICAS]

    async def upsert(self, metrica: MetricaSonda) -> None:
        await self.col.replace_one(
            {"sonda_id": metrica.sonda_id, "cubo": metrica.cubo, "grano": metrica.grano},
            self._to_doc(metrica),
            upsert=True,
        )

    async def list(
        self,
        propiedad_id: str,
        desde: datetime,
        hasta: datetime,
        grano: str,
    ) -> list[MetricaSonda]:
        cursor = self.col.find({
            "propiedad_id": propiedad_id,
            "cubo": {"$gte": desde, "$lte": hasta},
            "grano": grano,
        }).sort("cubo", ASCENDING)
        return [self._from_doc(doc) async for doc in cursor]

    async def get(self, sonda_id: str, cubo: datetime, grano: str) -> MetricaSonda | None:
        doc = await self.col.find_one({"sonda_id": sonda_id, "cubo": cubo, "grano": grano})
        return self._from_doc(doc) if doc else None

    def _to_doc(self, metrica: MetricaSonda) -> dict[str, Any]:
        return {
            "_id": metrica.id,
            "sonda_id": metrica.sonda_id,
            "propiedad_id": metrica.propiedad_id,
            "cubo": metrica.cubo,
            "grano": metrica.grano,
            "total_ejecuciones": metrica.total_ejecuciones,
            "exitosas": metrica.exitosas,
            "fallidas": metrica.fallidas,
            "latencia_p50": metrica.latencia_p50,
            "latencia_p95": metrica.latencia_p95,
            "latencia_p99": metrica.latencia_p99,
            "disponibilidad": metrica.disponibilidad,
            "errores_por_tipo": metrica.errores_por_tipo,
            "cert_expira_en": metrica.cert_expira_en,
            "cert_dias_restantes_min": metrica.cert_dias_restantes_min,
            "actualizado_en": metrica.actualizado_en,
        }

    def _from_doc(self, doc: dict[str, Any]) -> MetricaSonda:
        return MetricaSonda(
            id=doc["_id"],
            sonda_id=doc["sonda_id"],
            propiedad_id=doc["propiedad_id"],
            cubo=doc["cubo"],
            grano=doc["grano"],
            total_ejecuciones=doc.get("total_ejecuciones", 0),
            exitosas=doc.get("exitosas", 0),
            fallidas=doc.get("fallidas", 0),
            latencia_p50=doc.get("latencia_p50"),
            latencia_p95=doc.get("latencia_p95"),
            latencia_p99=doc.get("latencia_p99"),
            disponibilidad=doc.get("disponibilidad", 0.0),
            errores_por_tipo=doc.get("errores_por_tipo", {}),
            cert_expira_en=doc.get("cert_expira_en"),
            cert_dias_restantes_min=doc.get("cert_dias_restantes_min"),
            actualizado_en=doc.get("actualizado_en", ahora_utc()),
        )
