"""Entidades del contexto Integrations: integraciones, ejecuciones, métricas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.shared.ids import ahora_utc, nueva_id


class Integracion(BaseModel):
    """Configuración de una integración externa."""

    id: str = Field(default_factory=nueva_id)
    propiedad_id: str
    tipo: Literal["GA4", "SEARCH_CONSOLE", "ADSENSE", "AD_MANAGER"]
    nombre: str
    # Credenciales (referenciadas, no guardadas en claro)
    credenciales_ref: str  # ej: "env:GA4_CREDENTIALS" o "secret:ga4-key"
    # Configuración específica
    config: dict = Field(default_factory=dict)  # property_id, site_url, etc.
    # Estado
    estado: Literal["PENDIENTE", "ACTIVA", "DEGRADADA", "ERROR", "DESHABILITADA"] = "PENDIENTE"
    ultima_sincronizacion_en: Optional[datetime] = None
    ultima_sincronizacion_exitosa_en: Optional[datetime] = None
    error_ultima_sincronizacion: Optional[str] = None
    # Programación
    intervalo_horas: int = 24
    activo: bool = True
    creado_en: datetime = Field(default_factory=ahora_utc)
    actualizado_en: datetime = Field(default_factory=ahora_utc)


class EjecucionSincronizacion(BaseModel):
    """Resultado de una ejecución de sincronización."""

    id: str = Field(default_factory=nueva_id)
    integracion_id: str
    propiedad_id: str
    iniciado_en: datetime
    finalizado_en: Optional[datetime] = None
    exito: bool = False
    metricas_obtenidas: int = 0
    error: Optional[str] = None
    error_tipo: Optional[str] = None
    datos_muestra: dict = Field(default_factory=dict)  # muestra de lo obtenido
    creado_en: datetime = Field(default_factory=ahora_utc)


class MetricaIntegracion(BaseModel):
    """Métrica obtenida de una integración externa."""

    id: str = Field(default_factory=nueva_id)
    integracion_id: str
    propiedad_id: str
    nombre: str  # ej: "ga4_sessions", "gsc_impressions", "adsense_earnings"
    valor: float
    dimensiones: dict[str, str] = Field(default_factory=dict)  # date, page, country, etc.
    fecha_dato: datetime  # fecha a la que corresponde el dato
    obtenido_en: datetime = Field(default_factory=ahora_utc)


class FilaDimensionIntegracion(BaseModel):
    clave: str
    valor: float


class PuntoIntegracion(BaseModel):
    cubo: datetime
    valor: float


class ProcedenciaIntegracion(BaseModel):
    fuente: str
    canal: str
    grano: str
    extraido_en: datetime
    datos_hasta: Optional[datetime]
    completitud: str
    zona_horaria: str


class ReporteIntegracion(BaseModel):
    """Reporte de métricas de integración externa."""

    desde: datetime
    hasta: datetime
    grano: str
    metricas: list["ResumenMetricaIntegracion"]
    procedencia: ProcedenciaIntegracion


class ResumenMetricaIntegracion(BaseModel):
    nombre: str
    tipo_integracion: str
    total: float
    por_dimension: list[FilaDimensionIntegracion]
    serie: list[PuntoIntegracion]