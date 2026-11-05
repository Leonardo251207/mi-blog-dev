"""Servicio de alertas: coordina evaluación y notificación."""

from __future__ import annotations

from typing import Any

from app.modules.alerts.application.dispatcher import NotificationDispatcher
from app.modules.alerts.application.evaluator import AlertEvaluator
from app.modules.alerts.domain.models import CanalNotificacion, Notificacion, ReglaAlerta
from app.modules.alerts.persistence.repository import (
    CanalNotificacionRepository,
    NotificacionRepository,
    ReglaAlertaRepository,
)
from app.shared.ids import ahora_utc, nueva_id


class AlertasService:
    """Orquesta evaluación de reglas y envío de notificaciones."""

    def __init__(
        self,
        evaluator: AlertEvaluator,
        dispatcher: NotificationDispatcher,
        reglas: ReglaAlertaRepository,
        notificaciones: NotificacionRepository,
        canales: CanalNotificacionRepository,
    ) -> None:
        self.evaluator = evaluator
        self.dispatcher = dispatcher
        self.reglas = reglas
        self.notificaciones = notificaciones
        self.canales = canales

    async def ciclo_evaluacion(self) -> dict[str, int]:
        """Ejecuta un ciclo completo: evaluar -> notificar -> despachar."""
        evaluaciones = await self.evaluator.evaluar_todas()
        notificaciones_creadas = 0

        for eval_result in evaluaciones:
            if eval_result.disparo:
                regla = await self.reglas.get(eval_result.regla_id)
                if regla:
                    creadas = await self._crear_notificaciones(regla, eval_result)
                    notificaciones_creadas += creadas

        despachadas = await self.dispatcher.despachar_pendientes()

        return {
            "reglas_evaluadas": len(evaluaciones),
            "reglas_disparadas": sum(1 for e in evaluaciones if e.disparo),
            "notificaciones_creadas": notificaciones_creadas,
            "notificaciones_enviadas": despachadas,
        }

    async def _crear_notificaciones(self, regla: ReglaAlerta, eval_result) -> int:
        """Crea notificaciones para cada canal configurado en la regla."""
        creadas = 0
        timestamp = getattr(eval_result, "evaluado_en", None) or ahora_utc()
        for canal_id in regla.canales_notificacion:
            # Clave de deduplicación por minuto
            clave = f"{regla.id}:{canal_id}:{timestamp.strftime('%Y%m%d%H%M')}"

            notif = Notificacion(
                id=nueva_id(),
                regla_id=regla.id,
                canal_id=canal_id,
                ocurrio_en=timestamp,
                titulo=f"Alerta: {regla.nombre}",
                cuerpo=eval_result.mensaje,
                severidad=regla.severidad,
                clave_deduplicacion=clave,
            )
            await self.notificaciones.add(notif)
            creadas += 1
        return creadas

    async def probar_notificacion(
        self,
        canal_id: str,
        titulo: str = "Prueba de notificación",
        cuerpo: str = "Esta es una notificación de prueba desde Metrics Collector.",
        severidad: str = "INFO",
    ) -> Notificacion:
        """Genera y despacha una notificación de prueba hacia un canal."""
        notif = Notificacion(
            id=nueva_id(),
            regla_id="test",
            canal_id=canal_id,
            ocurrio_en=ahora_utc(),
            titulo=titulo,
            cuerpo=cuerpo,
            severidad=severidad,  # type: ignore[arg-type]
            estado="PENDIENTE",
            clave_deduplicacion=f"test:{canal_id}:{ahora_utc().strftime('%Y%m%d%H%M%S')}",
        )
        await self.notificaciones.add(notif)
        await self.dispatcher.despachar_pendientes(limite=1)
        # Recuperar estado actualizado tras despacho
        actualizada = await self.notificaciones.get(notif.id)
        return actualizada or notif

    # --- CRUD Reglas ---

    async def crear_regla(self, regla: ReglaAlerta) -> ReglaAlerta:
        await self.reglas.add(regla)
        return regla

    async def obtener_regla(self, id: str) -> ReglaAlerta | None:
        return await self.reglas.get(id)

    async def listar_reglas(self, propiedad_id: str, estado: str | None = None) -> list[ReglaAlerta]:
        return await self.reglas.list_by_propiedad(propiedad_id, estado)

    async def actualizar_regla(self, regla: ReglaAlerta) -> ReglaAlerta:
        regla.actualizado_en = ahora_utc()
        await self.reglas.update(regla)
        return regla

    async def eliminar_regla(self, id: str) -> None:
        await self.reglas.delete(id)

    # --- CRUD Canales ---

    async def crear_canal(self, canal: CanalNotificacion) -> CanalNotificacion:
        await self.canales.add(canal)
        return canal

    async def obtener_canal(self, id: str) -> CanalNotificacion | None:
        return await self.canales.get(id)

    async def listar_canales(self, estado: str | None = None) -> list[CanalNotificacion]:
        return await self.canales.list(estado)

    async def actualizar_canal(self, canal: CanalNotificacion) -> CanalNotificacion:
        await self.canales.update(canal)
        return canal

    async def eliminar_canal(self, id: str) -> None:
        await self.canales.delete(id)

    # --- Historial notificaciones ---

    async def historial_notificaciones(self, regla_id: str, limite: int = 50) -> list[Notificacion]:
        return await self.notificaciones.list_por_regla(regla_id, limite)
