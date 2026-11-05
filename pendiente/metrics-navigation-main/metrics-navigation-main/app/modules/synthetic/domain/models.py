"""Entidades del contexto Synthetic: sondas, ejecuciones, métricas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.shared.ids import ahora_utc, nueva_id


class Sonda(BaseModel):
    """Definición de una sonda sintética."""

    id: str = Field(default_factory=nueva_id)
    propiedad_id: str
    nombre: str
    tipo: Literal["HTTP", "HTTPS", "TCP", "DNS", "TLS"]
    objetivo: str  # URL o host:puerto
    # Configuración HTTP
    metodo: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    cuerpo: Optional[str] = None
    esperado_status: int = 200
    esperado_contiene: Optional[str] = None
    # Configuración TLS
    verificar_certificado: bool = True
    dias_alerta_expiracion: int = 30
    # Configuración general
    intervalo_segundos: int = 300  # 5 min por defecto
    timeout_segundos: int = 10
    regiones: list[str] = Field(default_factory=lambda: ["default"])
    activo: bool = True
    creado_en: datetime = Field(default_factory=ahora_utc)
    actualizado_en: datetime = Field(default_factory=ahora_utc)


class EjecucionSonda(BaseModel):
    """Resultado de una ejecución de sonda."""

    id: str = Field(default_factory=nueva_id)
    sonda_id: str
    propiedad_id: str
    region: str
    iniciado_en: datetime
    finalizado_en: Optional[datetime] = None
    # Resultado
    exito: bool = False
    status_code: Optional[int] = None
    latencia_ms: Optional[int] = None
    # DNS
    dns_resuelto: bool = False
    dns_latencia_ms: Optional[int] = None
    ips_resueltas: list[str] = Field(default_factory=list)
    # TCP/TLS
    tcp_conectado: bool = False
    tcp_latencia_ms: Optional[int] = None
    tls_establecido: bool = False
    tls_latencia_ms: Optional[int] = None
    tls_version: Optional[str] = None
    cert_expira_en: Optional[datetime] = None
    cert_dias_restantes: Optional[int] = None
    # Errores
    error: Optional[str] = None
    error_tipo: Optional[str] = None
    # Respuesta
    respuesta_tamano: Optional[int] = None
    respuesta_headers: dict[str, str] = Field(default_factory=dict)
    creado_en: datetime = Field(default_factory=ahora_utc)


class MetricaSonda(BaseModel):
    """Métricas agregadas de una sonda en un cubo temporal."""

    id: str = Field(default_factory=nueva_id)
    sonda_id: str
    propiedad_id: str
    cubo: datetime  # inicio del cubo (hora/día)
    grano: Literal["HORA", "DIA"]
    # Contadores
    total_ejecuciones: int = 0
    exitosas: int = 0
    fallidas: int = 0
    # Latencia
    latencia_p50: Optional[float] = None
    latencia_p95: Optional[float] = None
    latencia_p99: Optional[float] = None
    # Disponibilidad
    disponibilidad: float = 0.0  # 0.0 - 1.0
    # Errores por tipo
    errores_por_tipo: dict[str, int] = Field(default_factory=dict)
    # TLS
    cert_expira_en: Optional[datetime] = None
    cert_dias_restantes_min: Optional[int] = None
    actualizado_en: datetime = Field(default_factory=ahora_utc)


class FilaDimensionSonda(BaseModel):
    clave: str
    valor: int


class PuntoSonda(BaseModel):
    cubo: datetime
    disponibilidad: float
    latencia_p50: Optional[float]
    latencia_p95: Optional[float]
    total_ejecuciones: int
    exitosas: int


class ProcedenciaSonda(BaseModel):
    fuente: str
    canal: str
    grano: str
    extraido_en: datetime
    datos_hasta: Optional[datetime]
    completitud: str
    zona_horaria: str


class ReporteSonda(BaseModel):
    """Reporte de disponibilidad y latencia de sondas."""

    desde: datetime
    hasta: datetime
    grano: str
    sondas: list["ResumenSonda"]
    procedencia: ProcedenciaSonda


class ResumenSonda(BaseModel):
    sonda_id: str
    nombre: str
    tipo: str
    objetivo: str
    disponibilidad: float
    latencia_p50: Optional[float]
    latencia_p95: Optional[float]
    total_ejecuciones: int
    exitosas: int
    fallidas: int
    cert_expira_en: Optional[datetime]
    cert_dias_restantes: Optional[int]
    ultima_ejecucion: Optional[EjecucionSonda]