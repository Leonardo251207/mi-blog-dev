"""Ingesta de visitas edge: validación, normalización, enriquecimiento y deduplicación."""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlsplit

from app.modules.edge.domain.models import (
    EdgeVisit,
    EdgeVisitEntrante,
    LoteEdgeVisitas,
    ResultadoIngestaEdge,
)
from app.modules.edge.persistence.repository import EdgeVisitRepository
from app.modules.properties.application.services import PropertiesService
from app.modules.properties.domain.models import Propiedad
from app.shared.enums import Entorno, EstadoCanal, EstadoSitio, TipoCanal
from app.shared.errors import DomainError
from app.shared.ids import (
    ahora_utc,
    detectar_entorno,
    hash_pseudonimo,
    normalizar_host,
    normalizar_ruta,
    nueva_id,
)
from app.shared.security import SlidingWindowLimiter


class EdgeService:
    def __init__(
        self,
        properties: PropertiesService,
        visitas: EdgeVisitRepository,
        limiter: SlidingWindowLimiter,
        salt: str,
        agente_enriquecedor: Any = None,
    ) -> None:
        self.properties = properties
        self.visitas = visitas
        self.limiter = limiter
        self.salt = salt
        self.agente_enriquecedor = agente_enriquecedor

    async def ingerir(
        self,
        lote: LoteEdgeVisitas,
        *,
        origin: str | None,
        referer: str | None,
    ) -> ResultadoIngestaEdge:
        canal = await self.properties.resolver_canal(lote.key)
        if canal.tipo != TipoCanal.EDGE:
            raise DomainError(
                "CANAL_NO_EDGE",
                "La clave no corresponde a un canal edge.",
                status_code=403,
            )
        propiedad = await self.properties.obtener_por_id(canal.propiedad_id)
        if propiedad.estado != EstadoSitio.ACTIVO:
            raise DomainError("SITIO_PAUSADO", "La propiedad no está activa.", status_code=409)
        if lote.site and lote.site not in {"auto", propiedad.slug}:
            raise DomainError(
                "SITIO_NO_COINCIDE",
                "La clave no pertenece al sitio indicado.",
                status_code=403,
            )

        host_lote = self._host_de_lote(lote, origin, referer)
        if not await self.properties.validar_origen(
            canal, origin=origin, referer=referer, host=host_lote
        ):
            raise DomainError(
                "ORIGEN_NO_PERMITIDO",
                "El origen no está permitido para este canal.",
                status_code=403,
            )

        if not await self.limiter.permitir(canal.id):
            raise DomainError(
                "CUOTA_AGOTADA",
                "Demasiadas peticiones para esta clave. Inténtalo más tarde.",
                status_code=429,
                retryable=True,
            )

        ahora = ahora_utc()
        visitas: list[EdgeVisit] = []
        for entrada in lote.events:
            visita = self._normalizar_visita(
                entrada,
                propiedad=propiedad,
                canal_id=canal.id,
                host_lote=host_lote,
                ahora=ahora,
            )
            if visita is not None:
                visitas.append(visita)

        if not visitas:
            raise DomainError(
                "VISITA_INVALIDA",
                "Ninguna visita del lote es válida.",
                status_code=422,
            )

        # Enriquecer visitas con clasificación de agentes si el enriquecedor está configurado
        if self.agente_enriquecedor:
            enriquecidas = await self.agente_enriquecedor.enriquecer_lote(visitas)
            await self.agente_enriquecedor.guardar_visitas(enriquecidas)

        insertados, duplicados = await self.visitas.add_many(visitas)
        if insertados:
            await self.properties.marcar_senal(canal, ahora)
        return ResultadoIngestaEdge(
            aceptados=insertados,
            duplicados=duplicados,
            rechazados=len(lote.events) - len(visitas),
        )

    def _host_de_lote(
        self,
        lote: LoteEdgeVisitas,
        origin: str | None,
        referer: str | None,
    ) -> str:
        for entrada in lote.events:
            if entrada.host:
                return normalizar_host(entrada.host)
        if origin:
            return normalizar_host(origin)
        if referer:
            try:
                return normalizar_host(urlsplit(referer).netloc)
            except ValueError:
                pass
        return "desconocido"

    def _normalizar_visita(
        self,
        entrada: EdgeVisitEntrante,
        *,
        propiedad: Propiedad,
        canal_id: str,
        host_lote: str,
        ahora,
    ) -> EdgeVisit | None:
        host = normalizar_host(entrada.host or host_lote)
        if not host:
            return None
        ocurrio = entrada.ts or ahora
        if ocurrio.tzinfo is None:
            ocurrio = ocurrio.replace(tzinfo=ahora.tzinfo)
        if ocurrio > ahora + timedelta(minutes=5):
            return None
        if ocurrio < ahora - timedelta(days=30):
            return None

        path = (entrada.path or "/").strip()[:2048] or "/"
        ruta_patron = normalizar_ruta(path)
        ip_hash = hash_pseudonimo(entrada.ip, self.salt)

        return EdgeVisit(
            id=nueva_id(),
            propiedad_id=propiedad.id,
            canal_id=canal_id,
            host=host,
            entorno=Entorno(detectar_entorno(host)),
            ocurrio_en=ocurrio,
            metodo=entrada.method.upper()[:16],
            path=path,
            ruta_patron=ruta_patron,
            query_string=entrada.query_string[:2048],
            user_agent=entrada.user_agent[:512],
            ip_hash=ip_hash,
            asn=entrada.asn[:64] if entrada.asn else None,
            pais=entrada.country[:2] if entrada.country else None,
            status_code=entrada.status_code,
            bytes_enviados=max(0, entrada.bytes_sent),
            bytes_recibidos=max(0, entrada.bytes_received),
            duracion_ms=entrada.duration_ms,
            referrer=entrada.referrer[:2048] if entrada.referrer else None,
        )
