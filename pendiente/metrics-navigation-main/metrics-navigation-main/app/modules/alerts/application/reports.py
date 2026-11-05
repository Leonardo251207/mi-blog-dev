"""Tipos de reporte para GraphQL - Alerts."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import strawberry
from pydantic import BaseModel


@strawberry.type
class ReglaAlertaType:
    id: strawberry.ID
    propiedad_id: str
    nombre: str
    tipo: str
    metrica: str
    condicion: str
    ventana: str
    agregacion: str
    severidad: str
    canales_notificacion: list[str]
    silencio_minutos: int
    estado: str
    ultima_evaluacion_en: datetime | None
    ultima_disparo_en: datetime | None
    creado_en: datetime
    actualizado_en: datetime


@strawberry.type
class CanalNotificacionType:
    id: strawberry.ID
    tipo: str
    nombre: str
    config: str  # JSON string (sin secretos)
    estado: str
    ultima_entrega_en: datetime | None
    creado_en: datetime


@strawberry.type
class NotificacionType:
    id: strawberry.ID
    regla_id: str
    canal_id: str
    ocurrio_en: datetime
    titulo: str
    cuerpo: str
    severidad: str
    estado: str
    intentos: int
    proximo_intento_en: datetime | None
    error_ultimo_intento: str | None
    creado_en: datetime


@strawberry.input
class CrearReglaAlertaInput:
    propiedad_id: str
    nombre: str
    tipo: str
    metrica: str
    condicion: str
    ventana: str
    agregacion: str = "sum"
    severidad: str = "AVISO"
    canales_notificacion: list[str] | None = None
    silencio_minutos: int = 30


@strawberry.input
class ActualizarReglaAlertaInput:
    nombre: str | None = None
    condicion: str | None = None
    ventana: str | None = None
    severidad: str | None = None
    canales_notificacion: list[str] | None = None
    silencio_minutos: int | None = None
    estado: str | None = None


@strawberry.input
class CrearCanalNotificacionInput:
    tipo: str
    nombre: str
    config: str  # JSON string
    estado: str = "ACTIVO"


@strawberry.input
class ReglaAlertaIdInput:
    regla_id: str


@strawberry.input
class CanalNotificacionIdInput:
    canal_id: str


@strawberry.input
class ProbarNotificacionInput:
    canal_id: str
    titulo: str = "Prueba de notificación"
    cuerpo: str = "Esta es una notificación de prueba desde Metrics Collector."
    severidad: str = "INFO"