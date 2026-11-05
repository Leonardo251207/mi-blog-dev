"""Reporte de tráfico de agentes a partir de visitas enriquecidas."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from pydantic import BaseModel

from app.modules.agents.domain.models import VisitaAgente
from app.modules.agents.persistence.repository import VisitaAgenteRepository
from app.modules.properties.application.services import PropertiesService
from app.shared.enums import Completitud, EstadoCanal, Grano, TipoCanal
from app.shared.errors import DomainError
from app.shared.ids import ahora_utc
from app.shared.time import cubos, inicio_cubo, validar_rango

LIMITE_DIMENSIONES = 50


class FilaDimensionAgente(BaseModel):
    clave: str
    valor: int


class PuntoTraficoAgente(BaseModel):
    cubo: datetime
    peticiones: int
    bytes_enviados: int
    agentes_unicos: int


class ProcedenciaAgente(BaseModel):
    fuente: str
    canal: str
    grano: str
    extraido_en: datetime
    datos_hasta: datetime | None
    completitud: str
    zona_horaria: str


class TraficoAgente(BaseModel):
    desde: datetime
    hasta: datetime
    grano: str
    total_peticiones: int
    total_bytes_enviados: int
    agentes_unicos_estimados: int
    por_categoria: list[FilaDimensionAgente]
    por_agente: list[FilaDimensionAgente]
    por_ruta: list[FilaDimensionAgente]
    por_status: list[FilaDimensionAgente]
    por_verificacion: list[FilaDimensionAgente]
    serie: list[PuntoTraficoAgente]
    procedencia: ProcedenciaAgente


class AgenteTraficoService:
    def __init__(
        self, properties: PropertiesService, visitas: VisitaAgenteRepository
    ) -> None:
        self.properties = properties
        self.visitas = visitas

    async def trafico(
        self,
        *,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.DIA,
        categoria: str | None = None,
        verificado: bool | None = None,
    ) -> TraficoAgente:
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
                "La propiedad no tiene un canal edge activo; el tráfico de agentes no es observable.",
                status_code=422,
            )

        visitas = await self.visitas.list(
            propiedad.id, desde, hasta, agente_id=None, categoria=categoria, verificado=verificado
        )

        total_peticiones = len(visitas)
        total_bytes = sum(v.bytes_enviados for v in visitas)
        agentes_unicos = len({v.agente_id for v in visitas if v.agente_id})

        por_categoria = Counter(v.categoria for v in visitas)
        por_agente = Counter(v.agente_id or "desconocido" for v in visitas)
        por_ruta = Counter(v.ruta_patron for v in visitas)
        por_status = Counter(str(v.status_code) for v in visitas)
        por_verificacion = Counter("verificado" if v.verificado else "no_verificado" for v in visitas)

        agrupados: dict[datetime, list] = defaultdict(list)
        for v in visitas:
            agrupados[inicio_cubo(v.ocurrio_en, grano, propiedad.zona_horaria)].append(v)
        serie: list[PuntoTraficoAgente] = []
        for cubo in cubos(desde, hasta, grano, propiedad.zona_horaria):
            del_cubo = agrupados.get(cubo, [])
            serie.append(
                PuntoTraficoAgente(
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

        return TraficoAgente(
            desde=desde,
            hasta=hasta,
            grano=grano.value,
            total_peticiones=total_peticiones,
            total_bytes_enviados=total_bytes,
            agentes_unicos_estimados=agentes_unicos,
            por_categoria=self._filas(por_categoria),
            por_agente=self._filas(por_agente),
            por_ruta=self._filas(por_ruta),
            por_status=self._filas(por_status),
            por_verificacion=self._filas(por_verificacion),
            serie=serie,
            procedencia=ProcedenciaAgente(
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
    def _filas(contador: Counter) -> list[FilaDimensionAgente]:
        return [
            FilaDimensionAgente(clave=clave, valor=valor)
            for clave, valor in contador.most_common(LIMITE_DIMENSIONES)
        ]