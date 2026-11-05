"""Eventos de navegación, lotes de ingesta y modelos de reporte."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.enums import Completitud, Entorno, Grano, TipoEvento
from app.shared.ids import ahora_utc


class EventoNavegacion(BaseModel):
    id_evento: str
    propiedad_id: str
    canal_id: str
    host: str
    entorno: Entorno
    tipo: TipoEvento
    ocurrio_en: datetime
    ruta_patron: str
    path: str
    referrer: str | None = None
    utm: dict[str, str] = Field(default_factory=dict)
    dispositivo: str = "desconocido"
    clave_sesion: str
    clave_visitante: str
    duracion_ms: int | None = None
    profundidad_scroll: float | None = None
    web_vitals: dict[str, float] = Field(default_factory=dict)
    metadatos: dict[str, str] = Field(default_factory=dict)
    creado_en: datetime = Field(default_factory=ahora_utc)


class EventoEntrante(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str | None = None
    type: TipoEvento = TipoEvento.PAGEVIEW
    ts: datetime | None = None
    path: str
    host: str | None = None
    referrer: str | None = None
    session: str | None = None
    visitor: str | None = None
    screen: str | None = None
    language: str | None = None
    duration_ms: int | None = Field(default=None, alias="durationMs")
    scroll: float | None = None
    vitals: dict[str, float] = Field(default_factory=dict)
    utm: dict[str, str] = Field(default_factory=dict)


class LoteEventos(BaseModel):
    key: str = Field(min_length=8, max_length=256)
    site: str | None = None
    events: list[EventoEntrante] = Field(min_length=1, max_length=50)


class ResultadoIngesta(BaseModel):
    aceptados: int
    duplicados: int
    rechazados: int = 0


class FilaDimension(BaseModel):
    clave: str
    valor: int


class PuntoTrafico(BaseModel):
    cubo: datetime
    pageviews: int
    sesiones: int


class Procedencia(BaseModel):
    fuente: str
    canal: str
    grano: Grano
    extraido_en: datetime
    datos_hasta: datetime | None
    completitud: Completitud
    muestreo: float = 1.0
    zona_horaria: str


class Cobertura(BaseModel):
    metrica: str
    observable: bool
    motivo: str | None = None


class Trafico(BaseModel):
    desde: datetime
    hasta: datetime
    grano: Grano
    pageviews: int
    sesiones: int
    visitantes_unicos_estimados: int
    por_ruta: list[FilaDimension]
    por_host: list[FilaDimension]
    por_referrer: list[FilaDimension]
    serie: list[PuntoTrafico]
    procedencia: Procedencia
    cobertura: list[Cobertura]
