"""Reporte de tráfico edge a partir de visitas de servidor."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from app.modules.edge.domain.models import (
    FilaDimensionEdge,
    PuntoTraficoEdge,
    ProcedenciaEdge,
    TraficoEdge,
)
from app.modules.edge.persistence.repository import EdgeVisitRepository
from app.modules.properties.application.services import PropertiesService
from app.shared.enums import Completitud, EstadoCanal, Grano, TipoCanal
from app.shared.errors import DomainError
from app.shared.ids import ahora_utc
from app.shared.time import cubos, inicio_cubo, validar_rango

LIMITE_DIMENSIONES = 50


class EdgeTraficoService:
    def __init__(self, properties: PropertiesService, visitas: EdgeVisitRepository) -> None:
        self.properties = properties
        self.visitas = visitas

    async def trafico(
        self,
        *,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.DIA,
        ruta: str | None = None,
        agente_categoria: str | None = None,
    ) -> TraficoEdge:
        propiedad = await self.properties.obtener_sitio(sitio_slug)
        desde, hasta = validar_rango(desde, hasta, grano)
        canales = await self.properties.canales_de(propiedad.id)
        edge = next(
            (
                canal
                for canal in canales
                if canal.tipo == TipoCanal.EDGE and canal.estado != EstadoCanal.INACTIVO
            ),
            None,
        )
        if edge is None:
            raise DomainError(
                "COBERTURA_INSUFICIENTE",
                "La propiedad no tiene un canal edge activo; el tráfico edge no es observable.",
                status_code=422,
            )

        visitas = await self.visitas.list(propiedad.id, desde, hasta, ruta, agente_categoria)

        total_peticiones = len(visitas)
        total_bytes = sum(v.bytes_enviados for v in visitas)
        agentes_unicos = len({v.agente_id for v in visitas if v.agente_id})

        por_ruta = Counter(v.ruta_patron for v in visitas)
        por_status = Counter(str(v.status_code) for v in visitas)
        por_agente_cat = Counter(v.agente_categoria or "desconocido" for v in visitas)
        por_agente = Counter(v.agente_id or "desconocido" for v in visitas)

        agrupados: dict[datetime, list] = defaultdict(list)
        for v in visitas:
            agrupados[inicio_cubo(v.ocurrio_en, grano, propiedad.zona_horaria)].append(v)
        serie: list[PuntoTraficoEdge] = []
        for cubo in cubos(desde, hasta, grano, propiedad.zona_horaria):
            del_cubo = agrupados.get(cubo, [])
            serie.append(
                PuntoTraficoEdge(
                    cubo=cubo,
                    peticiones=len(del_cubo),
                    bytes_enviados=sum(v.bytes_enviados for v in del_cubo),
                    agentes_unicos=len({v.agente_id for v in del_cubo if v.agente_id}),
                )
            )

        ultimo = max((v.ocurrio_en for v in visitas), default=None)
        completitud = Completitud.COMPLETA if visitas else Completitud.PARCIAL
        if edge.estado == EstadoCanal.DEGRADADO:
            completitud = Completitud.OBSOLETA

        return TraficoEdge(
            desde=desde,
            hasta=hasta,
            grano=grano.value,
            total_peticiones=total_peticiones,
            total_bytes_enviados=total_bytes,
            agentes_unicos_estimados=agentes_unicos,
            por_ruta=self._filas(por_ruta),
            por_status=self._filas(por_status),
            por_agente_categoria=self._filas(por_agente_cat),
            por_agente=self._filas(por_agente),
            serie=serie,
            procedencia=ProcedenciaEdge(
                fuente="edge",
                canal="EDGE",
                grano=grano.value,
                extraido_en=ahora_utc(),
                datos_hasta=ultimo,
                completitud=completitud.value,
                zona_horaria=propiedad.zona_horaria,
            ),
        )

    @staticmethod
    def _filas(contador: Counter) -> list[FilaDimensionEdge]:
        return [
            FilaDimensionEdge(clave=clave, valor=valor)
            for clave, valor in contador.most_common(LIMITE_DIMENSIONES)
        ]