"""Entidades del contexto Edge: visitas de servidor, bots, peticiones."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.shared.enums import Entorno
from app.shared.ids import ahora_utc, nueva_id


class EdgeVisit(BaseModel):
    """Una petición HTTP recibida en el servidor (edge, middleware, log drain)."""

    id: str = Field(default_factory=nueva_id)
    propiedad_id: str
    canal_id: str
    host: str
    entorno: Entorno
    ocurrio_en: datetime
    metodo: str = "GET"
    path: str
    ruta_patron: str
    query_string: str = ""
    user_agent: str
    ip_hash: str
    asn: Optional[str] = None
    pais: Optional[str] = None
    status_code: int
    bytes_enviados: int = 0
    bytes_recibidos: int = 0
    duracion_ms: Optional[int] = None
    referrer: Optional[str] = None
    # Clasificación del agente (se rellena enriqueciendo)
    agente_id: Optional[str] = None
    agente_categoria: Optional[str] = None
    agente_verificado: bool = False
    # Evidencia de verificación
    evidencia_dns: bool = False
    evidencia_ip_range: bool = False
    evidencia_firma: bool = False
    creado_en: datetime = Field(default_factory=ahora_utc)


class EdgeVisitEntrante(BaseModel):
    """Entrada cruda para ingesta edge (desde middleware, log drain, etc.)."""

    ts: Optional[datetime] = None
    method: str = "GET"
    path: str
    host: str
    query_string: str = ""
    user_agent: str
    ip: str
    status_code: int
    bytes_sent: int = 0
    bytes_received: int = 0
    duration_ms: Optional[int] = None
    referrer: Optional[str] = None
    # Metadatos opcionales del edge
    asn: Optional[str] = None
    country: Optional[str] = None


class LoteEdgeVisitas(BaseModel):
    """Lote de visitas edge para ingesta批量."""

    key: str = Field(min_length=8, max_length=256)
    site: Optional[str] = None
    events: list[EdgeVisitEntrante] = Field(min_length=1, max_length=500)


class ResultadoIngestaEdge(BaseModel):
    """Resultado de la ingesta de visitas edge."""

    aceptados: int
    duplicados: int
    rechazados: int = 0


class FilaDimensionEdge(BaseModel):
    """Fila para dimensiones en reportes edge."""

    clave: str
    valor: int


class PuntoTraficoEdge(BaseModel):
    """Punto de serie temporal para tráfico edge."""

    cubo: datetime
    peticiones: int
    bytes_enviados: int
    agentes_unicos: int


class ProcedenciaEdge(BaseModel):
    """Procedencia de un reporte edge."""

    fuente: str
    canal: str
    grano: str
    extraido_en: datetime
    datos_hasta: Optional[datetime]
    completitud: str
    zona_horaria: str


class TraficoEdge(BaseModel):
    """Reporte de tráfico edge (peticiones de servidor)."""

    desde: datetime
    hasta: datetime
    grano: str
    total_peticiones: int
    total_bytes_enviados: int
    agentes_unicos_estimados: int
    por_ruta: list[FilaDimensionEdge]
    por_status: list[FilaDimensionEdge]
    por_agente_categoria: list[FilaDimensionEdge]
    por_agente: list[FilaDimensionEdge]
    serie: list[PuntoTraficoEdge]
    procedencia: ProcedenciaEdge