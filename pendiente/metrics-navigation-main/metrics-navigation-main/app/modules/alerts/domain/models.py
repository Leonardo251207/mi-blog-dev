"""Entidades del contexto Alerts: reglas, canales, notificaciones."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.shared.ids import ahora_utc, nueva_id


class ReglaAlerta(BaseModel):
    """Regla de alerta: qué vigilar, cuándo disparar y por dónde avisar."""

    id: str = Field(default_factory=nueva_id)
    propiedad_id: str
    nombre: str
    tipo: Literal["UMBRAL", "AUSENCIA", "ANOMALIA", "ESTADO", "AGENTE_NUEVO"]
    # Qué vigilar
    metrica: str  # "pageviews", "agent_requests", "synthetic_latency_p95", etc.
    # Condición
    condicion: str  # expresión: "> 1000", "== 0", "< p50 * 0.5", etc.
    ventana: str  # "30m", "1h", "24h", "7d"
    agregacion: Literal["sum", "avg", "max", "min", "count"] = "sum"
    # Control
    severidad: Literal["INFO", "AVISO", "CRITICO"] = "AVISO"
    canales_notificacion: list[str] = Field(default_factory=list)  # ids de CanalNotificacion
    silencio_minutos: int = 30
    estado: Literal["ACTIVA", "SILENCIADA", "ARCHIVADA"] = "ACTIVA"
    # Metadatos
    ultima_evaluacion_en: Optional[datetime] = None
    ultima_disparo_en: Optional[datetime] = None
    creado_en: datetime = Field(default_factory=ahora_utc)
    actualizado_en: datetime = Field(default_factory=ahora_utc)


class CanalNotificacion(BaseModel):
    """Canal de notificación: Telegram, Discord o Webhook genérico."""

    id: str = Field(default_factory=nueva_id)
    tipo: Literal["TELEGRAM", "DISCORD", "WEBHOOK"]
    nombre: str
    # Configuración (secretos referenciados, no guardados)
    # TELEGRAM: bot_token_ref, chat_id
    # DISCORD: webhook_url_ref
    # WEBHOOK: url_ref, headers_ref (opcional)
    config: dict = Field(default_factory=dict)
    estado: Literal["ACTIVO", "INACTIVO"] = "ACTIVO"
    ultima_entrega_en: Optional[datetime] = None
    creado_en: datetime = Field(default_factory=ahora_utc)


class Notificacion(BaseModel):
    """Una notificación pendiente/enviada/fallida."""

    id: str = Field(default_factory=nueva_id)
    regla_id: str
    canal_id: str
    ocurrio_en: datetime
    titulo: str
    cuerpo: str
    severidad: Literal["INFO", "AVISO", "CRITICO"]
    estado: Literal["PENDIENTE", "ENVIADA", "FALLIDA", "DESCARTADA"] = "PENDIENTE"
    intentos: int = 0
    proximo_intento_en: Optional[datetime] = None
    clave_deduplicacion: str
    error_ultimo_intento: Optional[str] = None
    creado_en: datetime = Field(default_factory=ahora_utc)


class EvaluacionRegla(BaseModel):
    """Resultado de evaluar una regla."""

    regla_id: str
    disparo: bool
    valor_actual: float
    umbral: Optional[float] = None
    mensaje: str
    evaluado_en: datetime = Field(default_factory=ahora_utc)