"""Casos de uso de propiedades, dominios, canales y cobertura."""

from __future__ import annotations

import fnmatch
import re
from urllib.parse import urlsplit

from app.modules.navigation.domain.models import Cobertura
from app.modules.properties.domain.models import Canal, Dominio, Propiedad
from app.modules.properties.persistence.repository import (
    CanalRepository,
    DominioRepository,
    PropiedadRepository,
)
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
from app.shared.errors import DomainError, NotFound
from app.shared.ids import (
    ahora_utc,
    detectar_entorno,
    generar_clave_publica,
    hash_clave,
    normalizar_host,
    normalizar_origen,
)

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")

COBERTURA_POR_CANAL: dict[TipoCanal, list[str]] = {
    TipoCanal.BEACON: [
        "pageviews",
        "sessions",
        "unique_visitors",
        "bounce_rate",
        "engagement_seconds",
        "scroll_depth_avg",
        "web_vital_lcp_p75",
        "web_vital_cls_p75",
        "web_vital_inp_p75",
        "ai_referral_sessions",
    ],
    TipoCanal.EDGE: [
        "agent_requests",
        "agent_bytes",
        "agent_verified_share",
        "agent_blocked_requests",
        "crawl_waste_rate",
    ],
    TipoCanal.SINTETICO: ["uptime_ratio", "synthetic_latency_p95"],
}

METRICAS_POR_CANAL: list[tuple[str, TipoCanal]] = [
    ("pageviews", TipoCanal.BEACON),
    ("sessions", TipoCanal.BEACON),
    ("unique_visitors", TipoCanal.BEACON),
    ("bounce_rate", TipoCanal.BEACON),
    ("engagement_seconds", TipoCanal.BEACON),
    ("scroll_depth_avg", TipoCanal.BEACON),
    ("web_vital_lcp_p75", TipoCanal.BEACON),
    ("web_vital_cls_p75", TipoCanal.BEACON),
    ("web_vital_inp_p75", TipoCanal.BEACON),
    ("ai_referral_sessions", TipoCanal.BEACON),
    ("agent_requests", TipoCanal.EDGE),
    ("agent_bytes", TipoCanal.EDGE),
    ("agent_verified_share", TipoCanal.EDGE),
    ("agent_blocked_requests", TipoCanal.EDGE),
    ("crawl_waste_rate", TipoCanal.EDGE),
    ("uptime_ratio", TipoCanal.SINTETICO),
    ("synthetic_latency_p95", TipoCanal.SINTETICO),
]

METRICAS_EXTERNAS = {
    "ga4_sessions": "Sin integración GA4 activa.",
    "gsc_impressions": "Sin integración Search Console activa.",
    "ad_impressions": "Sin integración AdSense activa.",
}


class PropertiesService:
    def __init__(
        self,
        propiedades: PropiedadRepository,
        dominios: DominioRepository,
        canales: CanalRepository,
    ) -> None:
        self.propiedades = propiedades
        self.dominios = dominios
        self.canales = canales

    async def crear_sitio(
        self,
        *,
        slug: str,
        nombre: str,
        tipo: TipoSitio = TipoSitio.PROPIA,
        zona_horaria: str = "UTC",
        retencion_eventos_dias: int = 90,
        retencion_agregados_meses: int = 25,
        etiquetas: list[str] | None = None,
    ) -> Propiedad:
        slug = slug.strip().lower()
        if not SLUG_RE.match(slug):
            raise DomainError(
                "SLUG_INVALIDO",
                "El slug debe tener entre 2 y 63 caracteres, minúsculas, números o guiones.",
                status_code=422,
            )
        if await self.propiedades.get_by_slug(slug):
            raise DomainError("SLUG_DUPLICADO", f"Ya existe una propiedad con slug `{slug}`.", status_code=409)
        if retencion_eventos_dias < 30:
            raise DomainError("RETENCION_INVALIDA", "La retención mínima de eventos es 30 días.", status_code=422)
        if retencion_agregados_meses < 13:
            raise DomainError("RETENCION_INVALIDA", "La retención mínima de agregados es 13 meses.", status_code=422)
        propiedad = Propiedad(
            slug=slug,
            nombre=nombre.strip() or slug,
            tipo=tipo,
            zona_horaria=zona_horaria,
            retencion_eventos_dias=retencion_eventos_dias,
            retencion_agregados_meses=retencion_agregados_meses,
            etiquetas=etiquetas or [],
        )
        await self.propiedades.add(propiedad)
        return propiedad

    async def obtener_sitio(self, slug: str) -> Propiedad:
        propiedad = await self.propiedades.get_by_slug(slug.strip().lower())
        if not propiedad:
            raise NotFound("SITIO_NO_ENCONTRADO", f"No existe la propiedad `{slug}`.")
        return propiedad

    async def obtener_por_id(self, id: str) -> Propiedad:
        propiedad = await self.propiedades.get(id)
        if not propiedad:
            raise NotFound("SITIO_NO_ENCONTRADO", "La propiedad del canal no existe.")
        return propiedad

    async def listar_sitios(self) -> list[Propiedad]:
        return await self.propiedades.list()

    async def registrar_dominio(
        self,
        *,
        propiedad: Propiedad,
        host: str,
        tipo: TipoDominio = TipoDominio.PROPIO,
        entorno: Entorno = Entorno.PRODUCTION,
        es_canonico: bool = False,
        metodo_verificacion: str | None = None,
    ) -> Dominio:
        host = normalizar_host(host)
        if not host:
            raise DomainError("DOMINIO_INVALIDO", "El host no puede estar vacío.", status_code=422)
        if tipo == TipoDominio.PREVIEW and es_canonico:
            raise DomainError(
                "DOMINIO_INVALIDO",
                "Un dominio de preview no puede ser canónico.",
                status_code=422,
            )
        existente = await self.dominios.get_by_host(propiedad.id, host)
        if existente:
            return existente

        dominios = await self.dominios.list_by_propiedad(propiedad.id)
        if es_canonico:
            await self.dominios.quitar_canonico(propiedad.id)
        elif not any(dominio.es_canonico for dominio in dominios) and tipo != TipoDominio.PREVIEW:
            es_canonico = True

        dominio = Dominio(
            propiedad_id=propiedad.id,
            host=host,
            tipo=tipo,
            entorno=entorno,
            es_canonico=es_canonico,
            metodo_verificacion=metodo_verificacion,
        )
        await self.dominios.add(dominio)
        if es_canonico:
            propiedad.dominio_canonico_id = dominio.id
            await self.propiedades.update(propiedad)
        return dominio

    async def verificar_dominio(self, dominio_id: str) -> Dominio:
        dominio = await self.dominios.get(dominio_id)
        if not dominio:
            raise NotFound("DOMINIO_NO_ENCONTRADO", "El dominio no existe.")
        if dominio.estado == EstadoDominio.RETIRADO:
            raise DomainError("DOMINIO_RETIRADO", "Un dominio retirado no se puede verificar.", status_code=409)
        dominio.estado = EstadoDominio.VERIFICADO
        dominio.vigente_hasta = None
        dominio.metodo_verificacion = dominio.metodo_verificacion or "ADMIN"
        await self.dominios.update(dominio)

        propiedad = await self.obtener_por_id(dominio.propiedad_id)
        if propiedad.estado_verificacion != EstadoVerificacion.VERIFICADO:
            propiedad.estado_verificacion = EstadoVerificacion.VERIFICADO
        if not propiedad.dominio_canonico_id:
            propiedad.dominio_canonico_id = dominio.id
            dominio.es_canonico = True
            await self.dominios.update(dominio)
        await self.propiedades.update(propiedad)
        return dominio

    async def retirar_dominio(self, dominio_id: str) -> Dominio:
        dominio = await self.dominios.get(dominio_id)
        if not dominio:
            raise NotFound("DOMINIO_NO_ENCONTRADO", "El dominio no existe.")
        dominio.estado = EstadoDominio.RETIRADO
        dominio.es_canonico = False
        dominio.vigente_hasta = ahora_utc()
        await self.dominios.update(dominio)
        propiedad = await self.obtener_por_id(dominio.propiedad_id)
        if propiedad.dominio_canonico_id == dominio.id:
            propiedad.dominio_canonico_id = None
            await self.propiedades.update(propiedad)
        return dominio

    async def crear_canal(
        self,
        *,
        propiedad: Propiedad,
        tipo: TipoCanal,
        modo_origen: ModoOrigen = ModoOrigen.EXACTO,
        origenes: list[str] | None = None,
        entornos: list[Entorno] | None = None,
        path_prefix: str | None = None,
        clave_publica: str | None = None,
    ) -> tuple[Canal, str | None]:
        existente = await self.canales.get_by_tipo(propiedad.id, tipo.value)
        if existente:
            return existente, None
        if tipo == TipoCanal.BEACON and not clave_publica:
            clave_publica = generar_clave_publica("live")
        canal = Canal(
            propiedad_id=propiedad.id,
            tipo=tipo,
            cobertura=COBERTURA_POR_CANAL.get(tipo, []),
            clave_publica_hash=hash_clave(clave_publica) if clave_publica else None,
            clave_publica_prefijo=clave_publica[:12] if clave_publica else None,
            modo_origen=modo_origen,
            origenes_permitidos=[
                normalizar_origen(origen) or "" for origen in (origenes or [])
            ],
            entornos_permitidos=entornos or [Entorno.PRODUCTION],
            path_prefix=path_prefix,
            modo_provision=ModoProvision.REGISTRADO,
        )
        await self.canales.add(canal)
        return canal, clave_publica

    async def resolver_canal(self, clave: str) -> Canal:
        canal = await self.canales.get_by_key_hash(hash_clave(clave))
        if not canal:
            raise DomainError("CLAVE_INVALIDA", "La clave pública no existe.", status_code=401)
        if canal.estado == EstadoCanal.INACTIVO:
            raise DomainError("CANAL_INACTIVO", "El canal está inactivo.", status_code=409)
        return canal

    async def marcar_senal(self, canal: Canal, cuando) -> None:
        canal.ultima_senal_en = cuando
        if canal.estado == EstadoCanal.DEGRADADO:
            canal.estado = EstadoCanal.ACTIVO
        await self.canales.update(canal)

    async def validar_origen(
        self,
        canal: Canal,
        *,
        origin: str | None,
        referer: str | None,
        host: str,
    ) -> bool:
        if canal.modo_origen == ModoOrigen.ABIERTO_CON_CUOTA:
            return True
        if canal.tipo == TipoCanal.EDGE and not origin:
            # Peticiones máquina a máquina de edge (Cloudflare/Fastly/Vercel Middleware) no envían Origin
            if canal.entornos_permitidos:
                entorno = detectar_entorno(host)
                permitidos_entorno = {entorno_permitido.value for entorno_permitido in canal.entornos_permitidos}
                if entorno not in permitidos_entorno:
                    return False
            return True
        origen = normalizar_origen(origin)
        if not origen:
            return False
        permitidos = [normalizar_origen(item) or "" for item in canal.origenes_permitidos]
        if canal.modo_origen == ModoOrigen.EXACTO:
            coincide = origen in permitidos
        else:
            coincide = any(fnmatch.fnmatch(origen, patron) for patron in permitidos if patron)
        if not coincide:
            return False
        if canal.entornos_permitidos:
            entorno = detectar_entorno(host)
            permitidos_entorno = {entorno_permitido.value for entorno_permitido in canal.entornos_permitidos}
            if entorno not in permitidos_entorno:
                return False
        if canal.path_prefix and referer:
            try:
                ruta = urlsplit(referer).path or "/"
            except ValueError:
                ruta = "/"
            if not ruta.startswith(canal.path_prefix):
                return False
        return True

    async def dominios_de(self, propiedad_id: str) -> list[Dominio]:
        return await self.dominios.list_by_propiedad(propiedad_id)

    async def canales_de(self, propiedad_id: str) -> list[Canal]:
        return await self.canales.list_by_propiedad(propiedad_id)

    async def cobertura(self, propiedad: Propiedad) -> list[Cobertura]:
        canales = await self.canales_de(propiedad.id)
        activos = {
            canal.tipo
            for canal in canales
            if canal.estado != EstadoCanal.INACTIVO and propiedad.estado == EstadoSitio.ACTIVO
        }
        salida: list[Cobertura] = []
        for metrica, tipo in METRICAS_POR_CANAL:
            if tipo in activos:
                salida.append(Cobertura(metrica=metrica, observable=True))
            else:
                salida.append(
                    Cobertura(
                        metrica=metrica,
                        observable=False,
                        motivo=f"Sin canal {tipo.value} activo.",
                    )
                )
        for metrica, motivo in METRICAS_EXTERNAS.items():
            salida.append(Cobertura(metrica=metrica, observable=False, motivo=motivo))
        return salida
