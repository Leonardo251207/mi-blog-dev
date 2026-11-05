"""Bootstrap declarativo: estado inicial desde `config/bootstrap.yaml`."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml

from app.bootstrap.container import Container
from app.bootstrap.settings import Settings
from app.modules.properties.domain.models import Propiedad
from app.shared.enums import (
    Entorno,
    ModoOrigen,
    TipoCanal,
    TipoDominio,
    TipoSitio,
)
from app.shared.errors import DomainError, NotFound

logger = logging.getLogger(__name__)

TIPOS_SITIO = {
    "propia": TipoSitio.PROPIA,
    "ajena": TipoSitio.AJENA,
    "laboratorio": TipoSitio.LABORATORIO,
}
TIPOS_DOMINIO = {
    "propio": TipoDominio.PROPIO,
    "plataforma": TipoDominio.PLATAFORMA,
    "preview": TipoDominio.PREVIEW,
    "temporal": TipoDominio.TEMPORAL,
}
TIPOS_CANAL = {
    "beacon": TipoCanal.BEACON,
    "edge": TipoCanal.EDGE,
    "sintetico": TipoCanal.SINTETICO,
    "api_externa": TipoCanal.API_EXTERNA,
    "importacion": TipoCanal.IMPORTACION,
}
MODOS_ORIGEN = {
    "exact": ModoOrigen.EXACTO,
    "exacto": ModoOrigen.EXACTO,
    "pattern": ModoOrigen.PATRON,
    "patron": ModoOrigen.PATRON,
    "open_quota": ModoOrigen.ABIERTO_CON_CUOTA,
    "abierto_con_cuota": ModoOrigen.ABIERTO_CON_CUOTA,
}


async def seed_from_yaml(container: Container, settings: Settings) -> list[str]:
    ruta = Path(settings.bootstrap_file)
    if not ruta.exists():
        logger.warning("No existe el archivo de bootstrap: %s", ruta)
        return []
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    mensajes: list[str] = []
    for sitio in datos.get("sites", []):
        mensajes.extend(await _seed_sitio(container, settings, sitio))
    return mensajes


async def _seed_sitio(
    container: Container,
    settings: Settings,
    sitio: dict,
) -> list[str]:
    mensajes: list[str] = []
    slug = str(sitio["slug"]).strip().lower()
    try:
        propiedad = await container.properties_service.obtener_sitio(slug)
    except NotFound:
        propiedad = await container.properties_service.crear_sitio(
            slug=slug,
            nombre=str(sitio.get("name", slug)),
            tipo=TIPOS_SITIO.get(str(sitio.get("type", "propia")).lower(), TipoSitio.PROPIA),
            zona_horaria=str(sitio.get("timezone", "UTC")),
            retencion_eventos_dias=int(sitio.get("retention_events_days", 90)),
            retencion_agregados_meses=int(sitio.get("retention_aggregates_months", 25)),
            etiquetas=list(sitio.get("tags", [])),
        )
        mensajes.append(f"Propiedad creada: {slug}")

    for dominio in sitio.get("domains", []):
        try:
            await container.properties_service.registrar_dominio(
                propiedad=propiedad,
                host=str(dominio["host"]),
                tipo=TIPOS_DOMINIO.get(
                    str(dominio.get("type", "propio")).lower(), TipoDominio.PROPIO
                ),
                entorno=Entorno(str(dominio.get("environment", "production")).lower()),
                es_canonico=bool(dominio.get("canonical", False)),
            )
        except DomainError as exc:
            mensajes.append(f"Dominio omitido ({dominio.get('host')}): {exc.message}")

    for canal in sitio.get("channels", []):
        tipo = TIPOS_CANAL.get(str(canal.get("type", "")).lower())
        if tipo is None:
            mensajes.append(f"Canal omitido: tipo desconocido {canal.get('type')!r}")
            continue
        modo = MODOS_ORIGEN.get(
            str(canal.get("origin_mode", "exact")).lower(), ModoOrigen.EXACTO
        )
        entornos = [
            Entorno(str(valor).lower())
            for valor in canal.get("environments", ["production"])
        ]
        clave = _resolver_ref(canal.get("key_ref"), settings)
        _canal, clave_generada = await container.properties_service.crear_canal(
            propiedad=propiedad,
            tipo=tipo,
            modo_origen=modo,
            origenes=[str(origen) for origen in canal.get("origins", [])],
            entornos=entornos,
            path_prefix=canal.get("path_prefix"),
            clave_publica=clave,
        )
        if clave_generada and settings.es_local:
            mensajes.append(
                f"Canal {tipo.value} de {slug} creado. Clave pública: {clave_generada}"
            )
    return mensajes


def _resolver_ref(ref: str | None, settings: Settings) -> str | None:
    if not ref:
        return None
    if ref.startswith("env:"):
        nombre = ref[4:]
        valor = os.environ.get(nombre)
        if valor:
            return valor
        return getattr(settings, nombre.lower(), None)
    if ref.startswith("literal:"):
        return ref[8:]
    return ref
