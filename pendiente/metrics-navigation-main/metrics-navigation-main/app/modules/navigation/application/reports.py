"""Reporte de tráfico de navegación a partir de eventos crudos.

En F1 se calcula sobre los eventos; el rollup materializado llega con el worker de agregados.
Así el contrato de consulta queda estable desde el primer día.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from app.modules.navigation.domain.models import (
    FilaDimension,
    PuntoTrafico,
    Procedencia,
    Trafico,
)
from app.modules.navigation.persistence.repository import EventoRepository
from app.modules.properties.application.services import PropertiesService
from app.shared.enums import Completitud, EstadoCanal, Grano, TipoCanal, TipoEvento
from app.shared.errors import DomainError
from app.shared.ids import ahora_utc, host_de_referer
from app.shared.time import cubos, inicio_cubo, validar_rango

LIMITE_DIMENSIONES = 50


class TraficoService:
    def __init__(self, properties: PropertiesService, eventos: EventoRepository) -> None:
        self.properties = properties
        self.eventos = eventos

    async def trafico(
        self,
        *,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.DIA,
        ruta: str | None = None,
    ) -> Trafico:
        propiedad = await self.properties.obtener_sitio(sitio_slug)
        desde, hasta = validar_rango(desde, hasta, grano)
        canales = await self.properties.canales_de(propiedad.id)
        beacon = next(
            (
                canal
                for canal in canales
                if canal.tipo == TipoCanal.BEACON and canal.estado != EstadoCanal.INACTIVO
            ),
            None,
        )
        if beacon is None:
            raise DomainError(
                "COBERTURA_INSUFICIENTE",
                "La propiedad no tiene un canal beacon activo; el tráfico no es observable.",
                status_code=422,
            )

        eventos = await self.eventos.list(propiedad.id, desde, hasta, ruta)
        pageviews = [evento for evento in eventos if evento.tipo == TipoEvento.PAGEVIEW]
        sesiones = {evento.clave_sesion for evento in pageviews}
        visitantes = {evento.clave_visitante for evento in pageviews}

        por_ruta = Counter(evento.ruta_patron for evento in pageviews)
        por_host = Counter(evento.host for evento in pageviews)
        por_referrer = Counter(
            host_de_referer(evento.referrer) or "(directo)" for evento in pageviews
        )

        agrupados: dict[datetime, list] = defaultdict(list)
        for evento in pageviews:
            agrupados[inicio_cubo(evento.ocurrio_en, grano, propiedad.zona_horaria)].append(evento)
        serie: list[PuntoTrafico] = []
        for cubo in cubos(desde, hasta, grano, propiedad.zona_horaria):
            del_cubo = agrupados.get(cubo, [])
            serie.append(
                PuntoTrafico(
                    cubo=cubo,
                    pageviews=len(del_cubo),
                    sesiones=len({evento.clave_sesion for evento in del_cubo}),
                )
            )

        ultimo = max((evento.ocurrio_en for evento in eventos), default=None)
        completitud = Completitud.COMPLETA if eventos else Completitud.PARCIAL
        if beacon.estado == EstadoCanal.DEGRADADO:
            completitud = Completitud.OBSOLETA

        return Trafico(
            desde=desde,
            hasta=hasta,
            grano=grano,
            pageviews=len(pageviews),
            sesiones=len(sesiones),
            visitantes_unicos_estimados=len(visitantes),
            por_ruta=self._filas(por_ruta),
            por_host=self._filas(por_host),
            por_referrer=self._filas(por_referrer),
            serie=serie,
            procedencia=Procedencia(
                fuente="beacon",
                canal="BEACON",
                grano=grano,
                extraido_en=ahora_utc(),
                datos_hasta=ultimo,
                completitud=completitud,
                muestreo=1.0,
                zona_horaria=propiedad.zona_horaria,
            ),
            cobertura=await self.properties.cobertura(propiedad),
        )

    @staticmethod
    def _filas(contador: Counter) -> list[FilaDimension]:
        return [
            FilaDimension(clave=clave, valor=valor)
            for clave, valor in contador.most_common(LIMITE_DIMENSIONES)
        ]
