"""Entidades del contexto Agents: agentes, identidades, visitas, evidencias."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.shared.enums import Entorno
from app.shared.ids import ahora_utc, nueva_id


class Agente(BaseModel):
    """Catálogo de agentes conocidos (Googlebot, GPTBot, etc.)."""

    id: str = Field(default_factory=nueva_id)
    nombre: str  # "Googlebot", "GPTBot", "ClaudeBot"
    categoria: str  # "buscador", "entrenamiento_ia", "busqueda_ia", "fetcher_usuario", "scraper", "monitor", "preview_social"
    patrones_ua: list[str] = Field(default_factory=list)  # regex patterns
    rangos_ip: list[str] = Field(default_factory=list)  # CIDR ranges
    dns_sufijos: list[str] = Field(default_factory=list)  # e.g. ["googlebot.com", "google.com"]
    verifica_firma: bool = False  # si soporta HTTP Message Signatures
    notas: str = ""
    activo: bool = True
    creado_en: datetime = Field(default_factory=ahora_utc)
    actualizado_en: datetime = Field(default_factory=ahora_utc)


class IdentidadAgente(BaseModel):
    """Identidad verificada de un agente (resultado de verificación)."""

    id: str = Field(default_factory=nueva_id)
    agente_id: str  # referencia al catálogo
    ip_hash: str
    ua_declarado: str
    categoria_declarada: str
    # Evidencias
    dns_confirmado: bool = False
    dns_detalle: str = ""
    ip_range_confirmado: bool = False
    ip_range_detalle: str = ""
    firma_verificada: bool = False
    firma_detalle: str = ""
    # Resultado
    verificado: bool = False
    confianza: float = 0.0  # 0.0 - 1.0
    verificado_en: Optional[datetime] = None
    creado_en: datetime = Field(default_factory=ahora_utc)


class VisitaAgente(BaseModel):
    """Una visita de un agente (enriquecida desde EdgeVisit)."""

    id: str = Field(default_factory=nueva_id)
    propiedad_id: str
    canal_id: str
    host: str
    entorno: Entorno
    ocurrio_en: datetime
    metodo: str
    path: str
    ruta_patron: str
    query_string: str
    user_agent: str
    ip_hash: str
    asn: Optional[str] = None
    pais: Optional[str] = None
    status_code: int
    bytes_enviados: int
    bytes_recibidos: int
    duracion_ms: Optional[int] = None
    referrer: Optional[str] = None
    # Clasificación
    agente_id: Optional[str] = None  # referencia al catálogo
    identidad_id: Optional[str] = None  # referencia a la verificación
    categoria: str = "desconocido"
    verificado: bool = False
    confianza: float = 0.0
    # Evidencias copiadas de la identidad
    evidencia_dns: bool = False
    evidencia_ip_range: bool = False
    evidencia_firma: bool = False
    creado_en: datetime = Field(default_factory=ahora_utc)


class EvidenciaVerificacion(BaseModel):
    """Evidencia detallada de una verificación de agente."""

    id: str = Field(default_factory=nueva_id)
    identidad_id: str
    tipo: str  # "dns", "ip_range", "firma", "comportamiento"
    exitosa: bool
    detalle: str
    datos_crudos: dict = Field(default_factory=dict)
    creado_en: datetime = Field(default_factory=ahora_utc)


class CatalogoAgentes(BaseModel):
    """Catálogo versionado de agentes conocidos."""

    version: str
    agentes: list[Agente]
    actualizado_en: datetime = Field(default_factory=ahora_utc)