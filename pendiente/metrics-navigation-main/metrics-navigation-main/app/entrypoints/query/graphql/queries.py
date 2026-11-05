"""Consultas de la superficie GraphQL."""

from __future__ import annotations

from datetime import datetime

import strawberry
from strawberry.types import Info

from app.entrypoints.query.graphql.helpers import ejecutar
from app.entrypoints.query.graphql.types import (
    AgenteType,
    AnalisisCosteBeneficioType,
    CanalNotificacionType,
    CanalType,
    CoberturaType,
    DominioType,
    EjecucionSondaType,
    NotificacionType,
    PanelAgentesResumenType,
    PropiedadType,
    ReglaAlertaType,
    ReporteSondaType,
    SondaType,
    TraficoType,
    TraficoEdgeType,
    TraficoAgenteType,
)
from app.shared.enums import Grano
from app.shared.errors import NotFound


@strawberry.type
class Query:
    @strawberry.field
    async def sitios(self, info: Info) -> list[PropiedadType]:
        container = info.context.container
        propiedades = await container.properties_service.listar_sitios()
        return [PropiedadType.desde(propiedad) for propiedad in propiedades]

    @strawberry.field
    async def sitio(self, info: Info, slug: str) -> PropiedadType | None:
        container = info.context.container
        try:
            propiedad = await container.properties_service.obtener_sitio(slug)
        except NotFound:
            return None
        return PropiedadType.desde(propiedad)

    @strawberry.field
    async def dominios(self, info: Info, sitio_slug: str) -> list[DominioType]:
        container = info.context.container
        propiedad = await ejecutar(container.properties_service.obtener_sitio(sitio_slug))
        dominios = await container.properties_service.dominios_de(propiedad.id)
        return [DominioType.desde(dominio) for dominio in dominios]

    @strawberry.field
    async def canales(self, info: Info, sitio_slug: str) -> list[CanalType]:
        container = info.context.container
        propiedad = await ejecutar(container.properties_service.obtener_sitio(sitio_slug))
        canales = await container.properties_service.canales_de(propiedad.id)
        return [CanalType.desde(canal) for canal in canales]

    @strawberry.field
    async def trafico(
        self,
        info: Info,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.DIA,
        ruta: str | None = None,
    ) -> TraficoType:
        container = info.context.container
        trafico = await ejecutar(
            container.trafico_service.trafico(
                sitio_slug=sitio_slug,
                desde=desde,
                hasta=hasta,
                grano=grano,
                ruta=ruta,
            )
        )
        return TraficoType.desde(trafico)

    @strawberry.field
    async def trafico_edge(
        self,
        info: Info,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.DIA,
        ruta: str | None = None,
        agente_categoria: str | None = None,
    ) -> TraficoEdgeType:
        container = info.context.container
        trafico = await ejecutar(
            container.edge_trafico_service.trafico(
                sitio_slug=sitio_slug,
                desde=desde,
                hasta=hasta,
                grano=grano,
                ruta=ruta,
                agente_categoria=agente_categoria,
            )
        )
        return TraficoEdgeType.desde(trafico)

    @strawberry.field
    async def trafico_agentes(
        self,
        info: Info,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.DIA,
        categoria: str | None = None,
        verificado: bool | None = None,
    ) -> TraficoAgenteType:
        container = info.context.container
        trafico = await ejecutar(
            container.agente_trafico_service.trafico(
                sitio_slug=sitio_slug,
                desde=desde,
                hasta=hasta,
                grano=grano,
                categoria=categoria,
                verificado=verificado,
            )
        )
        return TraficoAgenteType.desde(trafico)

    @strawberry.field
    async def agentes(self, info: Info, activo: bool | None = None) -> list[AgenteType]:
        container = info.context.container
        agentes = await container.agente_admin_service.listar_agentes(activo=activo)
        return [AgenteType.desde(agente) for agente in agentes]

    @strawberry.field
    async def agente(self, info: Info, id: str) -> AgenteType | None:
        container = info.context.container
        agente = await container.agente_admin_service.obtener_agente(id)
        return AgenteType.desde(agente) if agente else None

    # --- Panel queries ---

    @strawberry.field
    async def panel_agentes(
        self,
        info: Info,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.DIA,
    ) -> PanelAgentesResumenType:
        container = info.context.container
        panel = await ejecutar(
            container.panel_agentes_service.panel_resumen(
                sitio_slug=sitio_slug,
                desde=desde,
                hasta=hasta,
                grano=grano,
            )
        )
        return PanelAgentesResumenType.desde(panel)

    @strawberry.field
    async def analisis_coste_beneficio(
        self,
        info: Info,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
    ) -> list[AnalisisCosteBeneficioType]:
        container = info.context.container
        analisis = await ejecutar(
            container.panel_agentes_service.analisis_coste_beneficio(
                sitio_slug=sitio_slug,
                desde=desde,
                hasta=hasta,
            )
        )
        return [
            AnalisisCosteBeneficioType(
                categoria=a.categoria,
                peticiones=a.peticiones,
                bytes_servidos=a.bytes_servidos,
                coste_estimado_usd=a.coste_estimado_usd,
                referidos_ia=a.referidos_ia,
                valor_referido_estimado_usd=a.valor_referido_estimado_usd,
                ratio_coste_beneficio=a.ratio_coste_beneficio,
                recomendacion=a.recomendacion,
            )
            for a in analisis
        ]

    # --- Alerts queries ---

    @strawberry.field
    async def reglas_alerta(self, info: Info, propiedad_id: str, estado: str | None = None) -> list[ReglaAlertaType]:
        container = info.context.container
        reglas = await container.alertas_service.listar_reglas(propiedad_id, estado)
        return [ReglaAlertaType.desde(r) for r in reglas]

    @strawberry.field
    async def regla_alerta(self, info: Info, id: str) -> ReglaAlertaType | None:
        container = info.context.container
        regla = await container.alertas_service.obtener_regla(id)
        return ReglaAlertaType.desde(regla) if regla else None

    @strawberry.field
    async def canales_notificacion(self, info: Info, estado: str | None = None) -> list[CanalNotificacionType]:
        container = info.context.container
        canales = await container.alertas_service.listar_canales(estado)
        return [CanalNotificacionType.desde(c) for c in canales]

    @strawberry.field
    async def canal_notificacion(self, info: Info, id: str) -> CanalNotificacionType | None:
        container = info.context.container
        canal = await container.alertas_service.obtener_canal(id)
        return CanalNotificacionType.desde(canal) if canal else None

    @strawberry.field
    async def historial_notificaciones(self, info: Info, regla_id: str, limite: int = 50) -> list[NotificacionType]:
        container = info.context.container
        notifs = await container.alertas_service.historial_notificaciones(regla_id, limite)
        return [NotificacionType.desde(n) for n in notifs]

    # --- Synthetic queries ---

    @strawberry.field
    async def sondas(self, info: Info, propiedad_id: str, activo: bool | None = None) -> list[SondaType]:
        container = info.context.container
        sondas = await container.synthetic_service.listar_sondas(propiedad_id, activo)
        return [SondaType.desde(s) for s in sondas]

    @strawberry.field
    async def sonda(self, info: Info, id: str) -> SondaType | None:
        container = info.context.container
        sonda = await container.synthetic_service.obtener_sonda(id)
        return SondaType.desde(sonda) if sonda else None

    @strawberry.field
    async def reporte_sondas(
        self,
        info: Info,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: str = "HORA",
    ) -> ReporteSondaType:
        container = info.context.container
        reporte = await container.synthetic_service.reporte(
            sitio_slug=sitio_slug,
            desde=desde,
            hasta=hasta,
            grano=grano,
        )
        return ReporteSondaType.desde(reporte)

    @strawberry.field
    async def ejecutar_sonda(self, info: Info, sonda_id: str) -> EjecucionSondaType:
        container = info.context.container
        ejecucion = await container.synthetic_service.ejecutar_sonda(sonda_id)
        return EjecucionSondaType.desde(ejecucion)

    @strawberry.field
    async def cobertura(self, info: Info, sitio_slug: str) -> list[CoberturaType]:
        container = info.context.container
        propiedad = await ejecutar(container.properties_service.obtener_sitio(sitio_slug))
        cobertura = await container.properties_service.cobertura(propiedad)
        return [CoberturaType.desde(item) for item in cobertura]
