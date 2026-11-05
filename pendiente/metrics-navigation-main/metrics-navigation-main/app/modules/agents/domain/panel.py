"""Modelos para referidos de IA y panel de decisiones."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.shared.ids import ahora_utc, nueva_id


class ReferidoIA(BaseModel):
    """Un referido detectado desde una IA (humano que hace clic desde respuesta de IA)."""

    id: str = Field(default_factory=nueva_id)
    propiedad_id: str
    canal_id: str
    host: str
    ocurrio_en: datetime
    ruta_patron: str
    referrer: str  # chatgpt.com, perplexity.ai, etc.
    plataforma_ia: str  # "chatgpt", "perplexity", "copilot", "gemini", "claude"
    session_id: str
    visitor_id: str
    user_agent: str
    creado_en: datetime = Field(default_factory=ahora_utc)


class ReferidoIAEntrante(BaseModel):
    """Entrada para detección de referido IA desde beacon."""

    ts: Optional[datetime] = None
    path: str
    host: str
    referrer: str
    session: str
    visitor: str
    user_agent: str


class FilaReferidosIA(BaseModel):
    plataforma: str
    sesiones: int
    rutas_top: list[tuple[str, int]]


class PanelAgentesResumen(BaseModel):
    """Resumen para el panel de agentes (6 widgets)."""

    propiedad_id: str
    desde: datetime
    hasta: datetime
    # Widget 1: Peticiones por clase
    peticiones_por_clase: dict[str, int]
    # Widget 2: Top 10 agentes por volumen
    top_agentes: list[tuple[str, int]]
    # Widget 3: Bytes servidos por clase
    bytes_por_clase: dict[str, int]
    # Widget 4: Top rutas rastreadas
    top_rutas: list[tuple[str, int]]
    # Widget 5: Códigos de respuesta servidos a agentes
    status_por_clase: dict[str, dict[str, int]]
    # Widget 6: Serie temporal de peticiones por categoría
    serie_por_categoria: dict[str, list[tuple[datetime, int]]]
    # Referidos de IA
    referidos_ia: list[FilaReferidosIA]
    # Coste estimado
    coste_estimado_por_clase: dict[str, float]
    extraido_en: datetime = Field(default_factory=ahora_utc)


class DecisionAgente(BaseModel):
    """Decisión tomada sobre un agente/categoría."""

    id: str = Field(default_factory=nueva_id)
    propiedad_id: str
    agente_id: Optional[str] = None
    categoria: Optional[str] = None  # si es por categoría completa
    decision: str  # "permitir", "permitir_cache", "limitar", "bloquear", "negociar"
    motivo: str
    rutas_afectadas: list[str] = Field(default_factory=list)
    creado_en: datetime = Field(default_factory=ahora_utc)
    creado_por: str
    efecto_medido: bool = False
    metricas_antes: dict = Field(default_factory=dict)
    metricas_despues: dict = Field(default_factory=dict)


class AnalisisCosteBeneficio(BaseModel):
    """Análisis de coste vs beneficio por agente/categoría."""

    agente_id: Optional[str] = None
    categoria: str
    peticiones: int
    bytes_servidos: int
    coste_estimado_usd: float
    referidos_ia: int
    valor_referido_estimado_usd: float
    ratio_coste_beneficio: float
    recomendacion: str  # "permitir", "limitar", "bloquear", "revisar"