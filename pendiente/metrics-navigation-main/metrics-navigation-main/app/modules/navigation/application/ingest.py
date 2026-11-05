"""Ingesta de navegación: validación, normalización, deduplicación y cuota."""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlsplit

from app.modules.navigation.domain.models import (
    EventoNavegacion,
    LoteEventos,
    ResultadoIngesta,
)
from app.modules.navigation.persistence.repository import EventoRepository
from app.modules.properties.application.services import PropertiesService
from app.modules.properties.domain.models import Propiedad
from app.shared.enums import Entorno, EstadoSitio
from app.shared.errors import DomainError
from app.shared.ids import (
    ahora_utc,
    detectar_entorno,
    dispositivo_desde_pantalla,
    hash_pseudonimo,
    normalizar_host,
    normalizar_referrer,
    normalizar_ruta,
    nueva_id,
)
from app.shared.security import SlidingWindowLimiter

VITALES_PERMITIDOS = {"lcp", "cls", "inp", "ttfb", "fcp"}
UTM_PERMITIDOS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}


class NavigationService:
    def __init__(
        self,
        properties: PropertiesService,
        eventos: EventoRepository,
        limiter: SlidingWindowLimiter,
        salt: str,
    ) -> None:
        self.properties = properties
        self.eventos = eventos
        self.limiter = limiter
        self.salt = salt

    async def ingerir(
        self,
        lote: LoteEventos,
        *,
        origin: str | None,
        referer: str | None,
    ) -> ResultadoIngesta:
        canal = await self.properties.resolver_canal(lote.key)
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
        eventos: list[EventoNavegacion] = []
        for entrada in lote.events:
            evento = self._normalizar_evento(
                entrada,
                propiedad=propiedad,
                canal_id=canal.id,
                host_lote=host_lote,
                ahora=ahora,
            )
            if evento is not None:
                eventos.append(evento)

        if not eventos:
            raise DomainError(
                "EVENTO_INVALIDO",
                "Ningún evento del lote es válido.",
                status_code=422,
            )

        insertados, duplicados = await self.eventos.add_many(eventos)
        if insertados:
            await self.properties.marcar_senal(canal, ahora)
        return ResultadoIngesta(
            aceptados=insertados,
            duplicados=duplicados,
            rechazados=len(lote.events) - len(eventos),
        )

    def _host_de_lote(
        self,
        lote: LoteEventos,
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

    def _normalizar_evento(
        self,
        entrada,
        *,
        propiedad: Propiedad,
        canal_id: str,
        host_lote: str,
        ahora,
    ) -> EventoNavegacion | None:
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
        sesion = (entrada.session or entrada.id or nueva_id())[:256]
        visitante = (entrada.visitor or sesion)[:256]
        dispositivos = dispositivo_desde_pantalla(entrada.screen)
        metadatos: dict[str, str] = {}
        if entrada.screen:
            metadatos["pantalla"] = entrada.screen[:64]
        if entrada.language:
            metadatos["idioma"] = entrada.language[:32]
        utm = {
            clave: valor[:200]
            for clave, valor in (entrada.utm or {}).items()
            if clave in UTM_PERMITIDOS and isinstance(valor, str)
        }
        vitales = {
            clave: float(valor)
            for clave, valor in (entrada.vitals or {}).items()
            if clave in VITALES_PERMITIDOS and isinstance(valor, (int, float))
        }
        duracion = None
        if entrada.duration_ms is not None:
            duracion = max(0, min(int(entrada.duration_ms), 86_400_000))
        scroll = None
        if entrada.scroll is not None:
            scroll = max(0.0, min(float(entrada.scroll), 1.0))

        return EventoNavegacion(
            id_evento=entrada.id or nueva_id(),
            propiedad_id=propiedad.id,
            canal_id=canal_id,
            host=host,
            entorno=Entorno(detectar_entorno(host)),
            tipo=entrada.type,
            ocurrio_en=ocurrio,
            ruta_patron=normalizar_ruta(path),
            path=path,
            referrer=normalizar_referrer(entrada.referrer),
            utm=utm,
            dispositivo=dispositivos,
            clave_sesion=hash_pseudonimo(sesion, self.salt),
            clave_visitante=hash_pseudonimo(visitante, self.salt),
            duracion_ms=duracion,
            profundidad_scroll=scroll,
            web_vitals=vitales,
            metadatos=metadatos,
        )
