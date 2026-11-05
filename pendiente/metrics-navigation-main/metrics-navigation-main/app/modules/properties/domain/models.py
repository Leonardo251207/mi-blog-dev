"""Entidades del contexto de propiedades, dominios y canales."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.enums import (
    Entorno,
    EstadoCanal,
    EstadoDominio,
    EstadoSitio,
    EstadoVerificacion,
    ModoOrigen,
    ModoProvision,
    TipoCanal,
    TipoDominio,
    TipoSitio,
)
from app.shared.ids import ahora_utc, nueva_id


class Propiedad(BaseModel):
    id: str = Field(default_factory=nueva_id)
    slug: str
    nombre: str
    tipo: TipoSitio = TipoSitio.PROPIA
    zona_horaria: str = "UTC"
    estado: EstadoSitio = EstadoSitio.ACTIVO
    estado_verificacion: EstadoVerificacion = EstadoVerificacion.PROVISIONAL
    retencion_eventos_dias: int = 90
    retencion_agregados_meses: int = 25
    dominio_canonico_id: str | None = None
    etiquetas: list[str] = Field(default_factory=list)
    creado_en: datetime = Field(default_factory=ahora_utc)


class Dominio(BaseModel):
    id: str = Field(default_factory=nueva_id)
    propiedad_id: str
    host: str
    tipo: TipoDominio = TipoDominio.PROPIO
    estado: EstadoDominio = EstadoDominio.PENDIENTE
    es_canonico: bool = False
    entorno: Entorno = Entorno.PRODUCTION
    vigente_desde: datetime = Field(default_factory=ahora_utc)
    vigente_hasta: datetime | None = None
    metodo_verificacion: str | None = None
    creado_en: datetime = Field(default_factory=ahora_utc)


class Canal(BaseModel):
    id: str = Field(default_factory=nueva_id)
    propiedad_id: str
    tipo: TipoCanal
    proveedor: str | None = None
    estado: EstadoCanal = EstadoCanal.ACTIVO
    cobertura: list[str] = Field(default_factory=list)
    clave_publica_hash: str | None = None
    clave_publica_prefijo: str | None = None
    modo_origen: ModoOrigen = ModoOrigen.EXACTO
    origenes_permitidos: list[str] = Field(default_factory=list)
    entornos_permitidos: list[Entorno] = Field(default_factory=list)
    path_prefix: str | None = None
    modo_provision: ModoProvision = ModoProvision.REGISTRADO
    ultima_senal_en: datetime | None = None
    creado_en: datetime = Field(default_factory=ahora_utc)
