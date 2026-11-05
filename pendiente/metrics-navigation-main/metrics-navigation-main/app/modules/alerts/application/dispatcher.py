"""Despachador de notificaciones: Telegram, Discord, Webhook."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.modules.alerts.domain.models import CanalNotificacion, Notificacion
from app.modules.alerts.persistence.repository import CanalNotificacionRepository, NotificacionRepository
from app.shared.ids import ahora_utc


class NotificationDispatcher:
    """Envía notificaciones por los canales configurados."""

    def __init__(
        self,
        notificaciones: NotificacionRepository,
        canales: CanalNotificacionRepository,
        settings: dict[str, Any],
    ) -> None:
        self.notificaciones = notificaciones
        self.canales = canales
        self.settings = settings
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        await self.client.aclose()

    async def despachar_pendientes(self, limite: int = 50) -> int:
        """Procesa notificaciones pendientes."""
        pendientes = await self.notificaciones.list_pendientes(limite=limite)
        enviados = 0
        for notif in pendientes:
            if await self._enviar(notif):
                enviados += 1
        return enviados

    async def _enviar(self, notif: Notificacion) -> bool:
        canal = await self.canales.get(notif.canal_id)
        if not canal or canal.estado != "ACTIVO":
            notif.estado = "DESCARTADA"
            await self.notificaciones.update(notif)
            return False

        exito = False
        error = None
        try:
            if canal.tipo == "TELEGRAM":
                exito = await self._enviar_telegram(canal, notif)
            elif canal.tipo == "DISCORD":
                exito = await self._enviar_discord(canal, notif)
            elif canal.tipo == "WEBHOOK":
                exito = await self._enviar_webhook(canal, notif)
        except Exception as e:
            error = str(e)
            exito = False

        if exito:
            notif.estado = "ENVIADA"
            canal.ultima_entrega_en = ahora_utc()
            await self.canales.update(canal)
        else:
            notif.intentos += 1
            notif.error_ultimo_intento = error
            if notif.intentos >= 5:
                notif.estado = "DESCARTADA"
            else:
                # Reintento: 1m, 5m, 15m, 1h, 6h
                retrasos = [1, 5, 15, 60, 360]
                minutos = retrasos[min(notif.intentos - 1, len(retrasos) - 1)]
                notif.proximo_intento_en = ahora_utc() + timedelta(minutes=minutos)
                notif.estado = "PENDIENTE"

        await self.notificaciones.update(notif)
        return exito

    async def _enviar_telegram(self, canal: CanalNotificacion, notif: Notificacion) -> bool:
        bot_token = self._resolver_secreto(canal.config.get("bot_token_ref"))
        chat_id = canal.config.get("chat_id")
        if not bot_token or not chat_id:
            return False

        emoji = {"INFO": "ℹ️", "AVISO": "⚠️", "CRITICO": "🚨"}.get(notif.severidad, "📢")
        texto = f"{emoji} <b>{notif.titulo}</b>\n{notif.cuerpo}"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        resp = await self.client.post(url, json={
            "chat_id": chat_id,
            "text": texto,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        })
        return resp.status_code == 200

    async def _enviar_discord(self, canal: CanalNotificacion, notif: Notificacion) -> bool:
        webhook_url = self._resolver_secreto(canal.config.get("webhook_url_ref"))
        if not webhook_url:
            return False

        color = {"INFO": 0x3498db, "AVISO": 0xf39c12, "CRITICO": 0xe74c3c}.get(notif.severidad, 0x95a5a6)
        payload = {
            "embeds": [{
                "title": notif.titulo,
                "description": notif.cuerpo,
                "color": color,
                "timestamp": notif.ocurrio_en.isoformat(),
            }]
        }

        resp = await self.client.post(webhook_url, json=payload)
        return resp.status_code in (200, 204)

    async def _enviar_webhook(self, canal: CanalNotificacion, notif: Notificacion) -> bool:
        url = self._resolver_secreto(canal.config.get("url_ref"))
        if not url:
            return False

        headers = {"Content-Type": "application/json"}
        headers_ref = canal.config.get("headers_ref")
        if headers_ref:
            extra_headers = self._resolver_secreto(headers_ref)
            if isinstance(extra_headers, dict):
                headers.update(extra_headers)

        payload = {
            "id": notif.id,
            "regla_id": notif.regla_id,
            "titulo": notif.titulo,
            "cuerpo": notif.cuerpo,
            "severidad": notif.severidad,
            "ocurrio_en": notif.ocurrio_en.isoformat(),
        }

        resp = await self.client.post(url, json=payload, headers=headers)
        return 200 <= resp.status_code < 300

    def _resolver_secreto(self, ref: str | None) -> Any:
        """Resuelve referencias a secretos: env:VAR, literal:valor, o settings.key."""
        if not ref:
            return None
        if ref.startswith("env:"):
            import os
            return os.environ.get(ref[4:])
        if ref.startswith("literal:"):
            return ref[8:]
        if ref.startswith("settings."):
            return self.settings.get(ref[9:])
        return ref
