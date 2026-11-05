"""Mutaciones de administración de la superficie GraphQL."""

from __future__ import annotations

import json
import strawberry
from strawberry.types import Info

from app.entrypoints.query.graphql.helpers import ejecutar, requerir_admin
from app.entrypoints.query.graphql.types import (
    AgenteType,
    CanalCreadoType,
    CanalNotificacionType,
    CanalType,
    DominioType,
    EjecucionSondaType,
    NotificacionType,
    PropiedadType,
    ReglaAlertaType,
    SondaType,
)
from app.modules.alerts.domain.models import CanalNotificacion, ReglaAlerta
from app.modules.synthetic.domain.models import Sonda
from app.shared.enums import (
    Entorno,
    ModoOrigen,
    TipoCanal,
    TipoDominio,
    TipoSitio,
)


@strawberry.input
class CrearSitioInput:
    slug: str
    nombre: str
    tipo: TipoSitio = TipoSitio.PROPIA
    zona_horaria: str = "UTC"
    retencion_eventos_dias: int = 90
    retencion_agregados_meses: int = 25
    etiquetas: list[str] | None = None


@strawberry.input
class RegistrarDominioInput:
    sitio_slug: str
    host: str
    tipo: TipoDominio = TipoDominio.PROPIO
    entorno: Entorno = Entorno.PRODUCTION
    es_canonico: bool = False
    metodo_verificacion: str | None = None


@strawberry.input
class CrearCanalInput:
    sitio_slug: str
    tipo: TipoCanal = TipoCanal.BEACON
    modo_origen: ModoOrigen = ModoOrigen.EXACTO
    origenes: list[str] | None = None
    entornos: list[Entorno] | None = None
    path_prefix: str | None = None


@strawberry.input
class DominioIdInput:
    dominio_id: str


@strawberry.input
class AgenteInput:
    nombre: str
    categoria: str
    patrones_ua: list[str] | None = None
    rangos_ip: list[str] | None = None
    dns_sufijos: list[str] | None = None
    verifica_firma: bool = False
    notas: str = ""


@strawberry.input
class AgenteIdInput:
    agente_id: str


# --- Alerts inputs ---

@strawberry.input
class CrearReglaAlertaInput:
    propiedad_id: str
    nombre: str
    tipo: str
    metrica: str
    condicion: str
    ventana: str
    agregacion: str = "sum"
    severidad: str = "AVISO"
    canales_notificacion: list[str] | None = None
    silencio_minutos: int = 30


@strawberry.input
class ActualizarReglaAlertaInput:
    nombre: str | None = None
    condicion: str | None = None
    ventana: str | None = None
    severidad: str | None = None
    canales_notificacion: list[str] | None = None
    silencio_minutos: int | None = None
    estado: str | None = None


@strawberry.input
class CrearCanalNotificacionInput:
    tipo: str
    nombre: str
    config: str
    estado: str = "ACTIVO"


@strawberry.input
class ReglaAlertaIdInput:
    regla_id: str


@strawberry.input
class CanalNotificacionIdInput:
    canal_id: str


@strawberry.input
class ProbarNotificacionInput:
    canal_id: str
    titulo: str = "Prueba de notificación"
    cuerpo: str = "Esta es una notificación de prueba desde Metrics Collector."
    severidad: str = "INFO"


# --- Synthetic inputs ---

@strawberry.input
class CrearSondaInput:
    propiedad_id: str
    nombre: str
    tipo: str
    objetivo: str
    metodo: str = "GET"
    headers: str = "{}"
    cuerpo: str | None = None
    esperado_status: int = 200
    esperado_contiene: str | None = None
    verificar_certificado: bool = True
    dias_alerta_expiracion: int = 30
    intervalo_segundos: int = 300
    timeout_segundos: int = 10
    regiones: list[str] | None = None
    activo: bool = True


@strawberry.input
class SondaIdInput:
    sonda_id: str


@strawberry.input
class EjecutarSondaInput:
    sonda_id: str


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def crear_sitio(self, info: Info, input: CrearSitioInput) -> PropiedadType:
        requerir_admin(info)
        container = info.context.container
        propiedad = await ejecutar(
            container.properties_service.crear_sitio(
                slug=input.slug,
                nombre=input.nombre,
                tipo=input.tipo,
                zona_horaria=input.zona_horaria,
                retencion_eventos_dias=input.retencion_eventos_dias,
                retencion_agregados_meses=input.retencion_agregados_meses,
                etiquetas=input.etiquetas,
            )
        )
        return PropiedadType.desde(propiedad)

    @strawberry.mutation
    async def registrar_dominio(
        self, info: Info, input: RegistrarDominioInput
    ) -> DominioType:
        requerir_admin(info)
        container = info.context.container
        propiedad = await ejecutar(
            container.properties_service.obtener_sitio(input.sitio_slug)
        )
        dominio = await ejecutar(
            container.properties_service.registrar_dominio(
                propiedad=propiedad,
                host=input.host,
                tipo=input.tipo,
                entorno=input.entorno,
                es_canonico=input.es_canonico,
                metodo_verificacion=input.metodo_verificacion,
            )
        )
        return DominioType.desde(dominio)

    @strawberry.mutation
    async def crear_canal(self, info: Info, input: CrearCanalInput) -> CanalCreadoType:
        requerir_admin(info)
        container = info.context.container
        propiedad = await ejecutar(
            container.properties_service.obtener_sitio(input.sitio_slug)
        )
        canal, clave = await ejecutar(
            container.properties_service.crear_canal(
                propiedad=propiedad,
                tipo=input.tipo,
                modo_origen=input.modo_origen,
                origenes=input.origenes,
                entornos=input.entornos,
                path_prefix=input.path_prefix,
            )
        )
        return CanalCreadoType(canal=CanalType.desde(canal), clave_publica=clave)

    @strawberry.mutation
    async def verificar_dominio(self, info: Info, input: DominioIdInput) -> DominioType:
        requerir_admin(info)
        container = info.context.container
        dominio = await ejecutar(
            container.properties_service.verificar_dominio(input.dominio_id)
        )
        return DominioType.desde(dominio)

    @strawberry.mutation
    async def retirar_dominio(self, info: Info, input: DominioIdInput) -> DominioType:
        requerir_admin(info)
        container = info.context.container
        dominio = await ejecutar(
            container.properties_service.retirar_dominio(input.dominio_id)
        )
        return DominioType.desde(dominio)

    # --- Agents mutations ---

    @strawberry.mutation
    async def crear_agente(self, info: Info, input: AgenteInput) -> AgenteType:
        requerir_admin(info)
        container = info.context.container
        agente = await container.agente_admin_service.crear_agente(
            nombre=input.nombre,
            categoria=input.categoria,
            patrones_ua=input.patrones_ua,
            rangos_ip=input.rangos_ip,
            dns_sufijos=input.dns_sufijos,
            verifica_firma=input.verifica_firma,
            notas=input.notas,
        )
        return AgenteType.desde(agente)

    @strawberry.mutation
    async def actualizar_agente(self, info: Info, input: AgenteInput, agente_id: str) -> AgenteType:
        requerir_admin(info)
        container = info.context.container
        agente = await container.agente_admin_service.actualizar_agente(
            agente_id,
            nombre=input.nombre,
            categoria=input.categoria,
            patrones_ua=input.patrones_ua,
            rangos_ip=input.rangos_ip,
            dns_sufijos=input.dns_sufijos,
            verifica_firma=input.verifica_firma,
            notas=input.notas,
        )
        return AgenteType.desde(agente)

    @strawberry.mutation
    async def eliminar_agente(self, info: Info, input: AgenteIdInput) -> bool:
        requerir_admin(info)
        container = info.context.container
        await container.agente_admin_service.eliminar_agente(input.agente_id)
        return True

    @strawberry.mutation
    async def activar_agente(self, info: Info, input: AgenteIdInput) -> AgenteType:
        requerir_admin(info)
        container = info.context.container
        agente = await container.agente_admin_service.activar_agente(input.agente_id)
        return AgenteType.desde(agente)

    @strawberry.mutation
    async def desactivar_agente(self, info: Info, input: AgenteIdInput) -> AgenteType:
        requerir_admin(info)
        container = info.context.container
        agente = await container.agente_admin_service.desactivar_agente(input.agente_id)
        return AgenteType.desde(agente)

    # --- Alerts mutations ---

    @strawberry.mutation
    async def crear_regla_alerta(self, info: Info, input: CrearReglaAlertaInput) -> ReglaAlertaType:
        requerir_admin(info)
        container = info.context.container
        regla = ReglaAlerta(
            propiedad_id=input.propiedad_id,
            nombre=input.nombre,
            tipo=input.tipo,
            metrica=input.metrica,
            condicion=input.condicion,
            ventana=input.ventana,
            agregacion=input.agregacion,
            severidad=input.severidad,
            canales_notificacion=input.canales_notificacion or [],
            silencio_minutos=input.silencio_minutos,
        )
        await container.alertas_service.crear_regla(regla)
        return ReglaAlertaType.desde(regla)

    @strawberry.mutation
    async def actualizar_regla_alerta(self, info: Info, input: ActualizarReglaAlertaInput, regla_id: str) -> ReglaAlertaType:
        requerir_admin(info)
        container = info.context.container
        regla = await container.alertas_service.obtener_regla(regla_id)
        if not regla:
            raise ValueError("Regla no encontrada")
        if input.nombre is not None:
            regla.nombre = input.nombre
        if input.condicion is not None:
            regla.condicion = input.condicion
        if input.ventana is not None:
            regla.ventana = input.ventana
        if input.severidad is not None:
            regla.severidad = input.severidad
        if input.canales_notificacion is not None:
            regla.canales_notificacion = input.canales_notificacion
        if input.silencio_minutos is not None:
            regla.silencio_minutos = input.silencio_minutos
        if input.estado is not None:
            regla.estado = input.estado
        await container.alertas_service.actualizar_regla(regla)
        return ReglaAlertaType.desde(regla)

    @strawberry.mutation
    async def eliminar_regla_alerta(self, info: Info, input: ReglaAlertaIdInput) -> bool:
        requerir_admin(info)
        container = info.context.container
        await container.alertas_service.eliminar_regla(input.regla_id)
        return True

    @strawberry.mutation
    async def crear_canal_notificacion(self, info: Info, input: CrearCanalNotificacionInput) -> CanalNotificacionType:
        requerir_admin(info)
        container = info.context.container
        canal = CanalNotificacion(
            tipo=input.tipo,
            nombre=input.nombre,
            config=json.loads(input.config),
            estado=input.estado,
        )
        await container.alertas_service.crear_canal(canal)
        return CanalNotificacionType.desde(canal)

    @strawberry.mutation
    async def actualizar_canal_notificacion(self, info: Info, input: CrearCanalNotificacionInput, canal_id: str) -> CanalNotificacionType:
        requerir_admin(info)
        container = info.context.container
        canal = await container.alertas_service.obtener_canal(canal_id)
        if not canal:
            raise ValueError("Canal no encontrado")
        canal.tipo = input.tipo
        canal.nombre = input.nombre
        canal.config = json.loads(input.config)
        canal.estado = input.estado
        await container.alertas_service.actualizar_canal(canal)
        return CanalNotificacionType.desde(canal)

    @strawberry.mutation
    async def eliminar_canal_notificacion(self, info: Info, input: CanalNotificacionIdInput) -> bool:
        requerir_admin(info)
        container = info.context.container
        await container.alertas_service.eliminar_canal(input.canal_id)
        return True

    @strawberry.mutation
    async def probar_notificacion(self, info: Info, input: ProbarNotificacionInput) -> NotificacionType:
        requerir_admin(info)
        container = info.context.container
        notif = await container.alertas_service.probar_notificacion(
            canal_id=input.canal_id,
            titulo=input.titulo,
            cuerpo=input.cuerpo,
            severidad=input.severidad,
        )
        return NotificacionType.desde(notif)

    # --- Synthetic mutations ---

    @strawberry.mutation
    async def crear_sonda(self, info: Info, input: CrearSondaInput) -> SondaType:
        requerir_admin(info)
        container = info.context.container
        sonda = Sonda(
            propiedad_id=input.propiedad_id,
            nombre=input.nombre,
            tipo=input.tipo,
            objetivo=input.objetivo,
            metodo=input.metodo,
            headers=json.loads(input.headers),
            cuerpo=input.cuerpo,
            esperado_status=input.esperado_status,
            esperado_contiene=input.esperado_contiene,
            verificar_certificado=input.verificar_certificado,
            dias_alerta_expiracion=input.dias_alerta_expiracion,
            intervalo_segundos=input.intervalo_segundos,
            timeout_segundos=input.timeout_segundos,
            regiones=input.regiones or ["default"],
            activo=input.activo,
        )
        await container.synthetic_service.crear_sonda(sonda)
        return SondaType.desde(sonda)

    @strawberry.mutation
    async def actualizar_sonda(self, info: Info, input: CrearSondaInput, sonda_id: str) -> SondaType:
        requerir_admin(info)
        container = info.context.container
        sonda = await container.synthetic_service.obtener_sonda(sonda_id)
        if not sonda:
            raise ValueError("Sonda no encontrada")
        sonda.nombre = input.nombre
        sonda.tipo = input.tipo
        sonda.objetivo = input.objetivo
        sonda.metodo = input.metodo
        sonda.headers = json.loads(input.headers)
        sonda.cuerpo = input.cuerpo
        sonda.esperado_status = input.esperado_status
        sonda.esperado_contiene = input.esperado_contiene
        sonda.verificar_certificado = input.verificar_certificado
        sonda.dias_alerta_expiracion = input.dias_alerta_expiracion
        sonda.intervalo_segundos = input.intervalo_segundos
        sonda.timeout_segundos = input.timeout_segundos
        sonda.regiones = input.regiones or ["default"]
        sonda.activo = input.activo
        await container.synthetic_service.actualizar_sonda(sonda)
        return SondaType.desde(sonda)

    @strawberry.mutation
    async def eliminar_sonda(self, info: Info, input: SondaIdInput) -> bool:
        requerir_admin(info)
        container = info.context.container
        await container.synthetic_service.eliminar_sonda(input.sonda_id)
        return True

    @strawberry.mutation
    async def ejecutar_sonda(self, info: Info, input: EjecutarSondaInput) -> EjecucionSondaType:
        requerir_admin(info)
        container = info.context.container
        ejecucion = await container.synthetic_service.ejecutar_sonda(input.sonda_id)
        return EjecucionSondaType.desde(ejecucion)
