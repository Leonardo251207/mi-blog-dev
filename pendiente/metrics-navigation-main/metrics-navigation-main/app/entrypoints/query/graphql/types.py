"""Tipos GraphQL de salida y su traducción desde el dominio."""

from __future__ import annotations

import json
from datetime import datetime

import strawberry

from app.modules.agents.application.reports import (
    FilaDimensionAgente,
    PuntoTraficoAgente,
    ProcedenciaAgente,
    TraficoAgente,
)
from app.modules.alerts.application.reports import (
    CanalNotificacionType as AlertCanalNotificacionType,
    NotificacionType as AlertNotificacionType,
    ReglaAlertaType as AlertReglaAlertaType,
)
from app.modules.edge.domain.models import (
    FilaDimensionEdge,
    PuntoTraficoEdge,
    ProcedenciaEdge,
    TraficoEdge,
)
from app.modules.navigation.domain.models import (
    Cobertura,
    FilaDimension,
    PuntoTrafico,
    Procedencia,
    Trafico,
)
from app.modules.properties.domain.models import Canal, Dominio, Propiedad
from app.shared.enums import (
    Completitud,
    Entorno,
    EstadoCanal,
    EstadoDominio,
    EstadoSitio,
    EstadoVerificacion,
    Grano,
    ModoOrigen,
    ModoProvision,
    TipoCanal,
    TipoDominio,
    TipoSitio,
)


@strawberry.type
class PropiedadType:
    id: strawberry.ID
    slug: str
    nombre: str
    tipo: TipoSitio
    zona_horaria: str
    estado: EstadoSitio
    estado_verificacion: EstadoVerificacion
    retencion_eventos_dias: int
    retencion_agregados_meses: int
    dominio_canonico_id: str | None
    etiquetas: list[str]
    creado_en: datetime

    @classmethod
    def desde(cls, propiedad: Propiedad) -> "PropiedadType":
        return cls(
            id=propiedad.id,
            slug=propiedad.slug,
            nombre=propiedad.nombre,
            tipo=propiedad.tipo,
            zona_horaria=propiedad.zona_horaria,
            estado=propiedad.estado,
            estado_verificacion=propiedad.estado_verificacion,
            retencion_eventos_dias=propiedad.retencion_eventos_dias,
            retencion_agregados_meses=propiedad.retencion_agregados_meses,
            dominio_canonico_id=propiedad.dominio_canonico_id,
            etiquetas=propiedad.etiquetas,
            creado_en=propiedad.creado_en,
        )


@strawberry.type
class DominioType:
    id: strawberry.ID
    host: str
    tipo: TipoDominio
    estado: EstadoDominio
    es_canonico: bool
    entorno: Entorno
    vigente_desde: datetime
    vigente_hasta: datetime | None
    metodo_verificacion: str | None
    creado_en: datetime

    @classmethod
    def desde(cls, dominio: Dominio) -> "DominioType":
        return cls(
            id=dominio.id,
            host=dominio.host,
            tipo=dominio.tipo,
            estado=dominio.estado,
            es_canonico=dominio.es_canonico,
            entorno=dominio.entorno,
            vigente_desde=dominio.vigente_desde,
            vigente_hasta=dominio.vigente_hasta,
            metodo_verificacion=dominio.metodo_verificacion,
            creado_en=dominio.creado_en,
        )


@strawberry.type
class CanalType:
    id: strawberry.ID
    tipo: TipoCanal
    proveedor: str | None
    estado: EstadoCanal
    cobertura: list[str]
    clave_publica_prefijo: str | None
    modo_origen: ModoOrigen
    origenes_permitidos: list[str]
    entornos_permitidos: list[Entorno]
    path_prefix: str | None
    modo_provision: ModoProvision
    ultima_senal_en: datetime | None
    creado_en: datetime

    @classmethod
    def desde(cls, canal: Canal) -> "CanalType":
        return cls(
            id=canal.id,
            tipo=canal.tipo,
            proveedor=canal.proveedor,
            estado=canal.estado,
            cobertura=canal.cobertura,
            clave_publica_prefijo=canal.clave_publica_prefijo,
            modo_origen=canal.modo_origen,
            origenes_permitidos=canal.origenes_permitidos,
            entornos_permitidos=canal.entornos_permitidos,
            path_prefix=canal.path_prefix,
            modo_provision=canal.modo_provision,
            ultima_senal_en=canal.ultima_senal_en,
            creado_en=canal.creado_en,
        )


@strawberry.type
class CanalCreadoType:
    canal: CanalType
    clave_publica: str | None


@strawberry.type
class FilaDimensionType:
    clave: str
    valor: int

    @classmethod
    def desde(cls, fila: FilaDimension) -> "FilaDimensionType":
        return cls(clave=fila.clave, valor=fila.valor)


@strawberry.type
class PuntoTraficoType:
    cubo: datetime
    pageviews: int
    sesiones: int

    @classmethod
    def desde(cls, punto: PuntoTrafico) -> "PuntoTraficoType":
        return cls(cubo=punto.cubo, pageviews=punto.pageviews, sesiones=punto.sesiones)


@strawberry.type
class ProcedenciaType:
    fuente: str
    canal: str
    grano: Grano
    extraido_en: datetime
    datos_hasta: datetime | None
    completitud: Completitud
    muestreo: float
    zona_horaria: str

    @classmethod
    def desde(cls, procedencia: Procedencia) -> "ProcedenciaType":
        return cls(
            fuente=procedencia.fuente,
            canal=procedencia.canal,
            grano=procedencia.grano,
            extraido_en=procedencia.extraido_en,
            datos_hasta=procedencia.datos_hasta,
            completitud=procedencia.completitud,
            muestreo=procedencia.muestreo,
            zona_horaria=procedencia.zona_horaria,
        )


@strawberry.type
class CoberturaType:
    metrica: str
    observable: bool
    motivo: str | None

    @classmethod
    def desde(cls, cobertura: Cobertura) -> "CoberturaType":
        return cls(
            metrica=cobertura.metrica,
            observable=cobertura.observable,
            motivo=cobertura.motivo,
        )


@strawberry.type
class TraficoType:
    desde: datetime
    hasta: datetime
    grano: Grano
    pageviews: int
    sesiones: int
    visitantes_unicos_estimados: int
    por_ruta: list[FilaDimensionType]
    por_host: list[FilaDimensionType]
    por_referrer: list[FilaDimensionType]
    serie: list[PuntoTraficoType]
    procedencia: ProcedenciaType
    cobertura: list[CoberturaType]

    @classmethod
    def desde(cls, trafico: Trafico) -> "TraficoType":
        return cls(
            desde=trafico.desde,
            hasta=trafico.hasta,
            grano=trafico.grano,
            pageviews=trafico.pageviews,
            sesiones=trafico.sesiones,
            visitantes_unicos_estimados=trafico.visitantes_unicos_estimados,
            por_ruta=[FilaDimensionType.desde(fila) for fila in trafico.por_ruta],
            por_host=[FilaDimensionType.desde(fila) for fila in trafico.por_host],
            por_referrer=[FilaDimensionType.desde(fila) for fila in trafico.por_referrer],
            serie=[PuntoTraficoType.desde(punto) for punto in trafico.serie],
            procedencia=ProcedenciaType.desde(trafico.procedencia),
            cobertura=[CoberturaType.desde(item) for item in trafico.cobertura],
        )


# --- Edge Types ---

@strawberry.type
class FilaDimensionEdgeType:
    clave: str
    valor: int

    @classmethod
    def desde(cls, fila: FilaDimensionEdge) -> "FilaDimensionEdgeType":
        return cls(clave=fila.clave, valor=fila.valor)


@strawberry.type
class PuntoTraficoEdgeType:
    cubo: datetime
    peticiones: int
    bytes_enviados: int
    agentes_unicos: int

    @classmethod
    def desde(cls, punto: PuntoTraficoEdge) -> "PuntoTraficoEdgeType":
        return cls(
            cubo=punto.cubo,
            peticiones=punto.peticiones,
            bytes_enviados=punto.bytes_enviados,
            agentes_unicos=punto.agentes_unicos,
        )


@strawberry.type
class ProcedenciaEdgeType:
    fuente: str
    canal: str
    grano: str
    extraido_en: datetime
    datos_hasta: datetime | None
    completitud: str
    zona_horaria: str

    @classmethod
    def desde(cls, procedencia: ProcedenciaEdge) -> "ProcedenciaEdgeType":
        return cls(
            fuente=procedencia.fuente,
            canal=procedencia.canal,
            grano=procedencia.grano,
            extraido_en=procedencia.extraido_en,
            datos_hasta=procedencia.datos_hasta,
            completitud=procedencia.completitud,
            zona_horaria=procedencia.zona_horaria,
        )


@strawberry.type
class TraficoEdgeType:
    desde: datetime
    hasta: datetime
    grano: str
    total_peticiones: int
    total_bytes_enviados: int
    agentes_unicos_estimados: int
    por_ruta: list[FilaDimensionEdgeType]
    por_status: list[FilaDimensionEdgeType]
    por_agente_categoria: list[FilaDimensionEdgeType]
    por_agente: list[FilaDimensionEdgeType]
    serie: list[PuntoTraficoEdgeType]
    procedencia: ProcedenciaEdgeType

    @classmethod
    def desde(cls, trafico: TraficoEdge) -> "TraficoEdgeType":
        return cls(
            desde=trafico.desde,
            hasta=trafico.hasta,
            grano=trafico.grano,
            total_peticiones=trafico.total_peticiones,
            total_bytes_enviados=trafico.total_bytes_enviados,
            agentes_unicos_estimados=trafico.agentes_unicos_estimados,
            por_ruta=[FilaDimensionEdgeType.desde(fila) for fila in trafico.por_ruta],
            por_status=[FilaDimensionEdgeType.desde(fila) for fila in trafico.por_status],
            por_agente_categoria=[FilaDimensionEdgeType.desde(fila) for fila in trafico.por_agente_categoria],
            por_agente=[FilaDimensionEdgeType.desde(fila) for fila in trafico.por_agente],
            serie=[PuntoTraficoEdgeType.desde(punto) for punto in trafico.serie],
            procedencia=ProcedenciaEdgeType.desde(trafico.procedencia),
        )


# --- Agents Types ---

@strawberry.type
class FilaDimensionAgenteType:
    clave: str
    valor: int

    @classmethod
    def desde(cls, fila: FilaDimensionAgente) -> "FilaDimensionAgenteType":
        return cls(clave=fila.clave, valor=fila.valor)


@strawberry.type
class PuntoTraficoAgenteType:
    cubo: datetime
    peticiones: int
    bytes_enviados: int
    agentes_unicos: int

    @classmethod
    def desde(cls, punto: PuntoTraficoAgente) -> "PuntoTraficoAgenteType":
        return cls(
            cubo=punto.cubo,
            peticiones=punto.peticiones,
            bytes_enviados=punto.bytes_enviados,
            agentes_unicos=punto.agentes_unicos,
        )


@strawberry.type
class ProcedenciaAgenteType:
    fuente: str
    canal: str
    grano: str
    extraido_en: datetime
    datos_hasta: datetime | None
    completitud: str
    zona_horaria: str

    @classmethod
    def desde(cls, procedencia: ProcedenciaAgente) -> "ProcedenciaAgenteType":
        return cls(
            fuente=procedencia.fuente,
            canal=procedencia.canal,
            grano=procedencia.grano,
            extraido_en=procedencia.extraido_en,
            datos_hasta=procedencia.datos_hasta,
            completitud=procedencia.completitud,
            zona_horaria=procedencia.zona_horaria,
        )


@strawberry.type
class TraficoAgenteType:
    desde: datetime
    hasta: datetime
    grano: str
    total_peticiones: int
    total_bytes_enviados: int
    agentes_unicos_estimados: int
    por_categoria: list[FilaDimensionAgenteType]
    por_agente: list[FilaDimensionAgenteType]
    por_ruta: list[FilaDimensionAgenteType]
    por_status: list[FilaDimensionAgenteType]
    por_verificacion: list[FilaDimensionAgenteType]
    serie: list[PuntoTraficoAgenteType]
    procedencia: ProcedenciaAgenteType

    @classmethod
    def desde(cls, trafico: TraficoAgente) -> "TraficoAgenteType":
        return cls(
            desde=trafico.desde,
            hasta=trafico.hasta,
            grano=trafico.grano,
            total_peticiones=trafico.total_peticiones,
            total_bytes_enviados=trafico.total_bytes_enviados,
            agentes_unicos_estimados=trafico.agentes_unicos_estimados,
            por_categoria=[FilaDimensionAgenteType.desde(fila) for fila in trafico.por_categoria],
            por_agente=[FilaDimensionAgenteType.desde(fila) for fila in trafico.por_agente],
            por_ruta=[FilaDimensionAgenteType.desde(fila) for fila in trafico.por_ruta],
            por_status=[FilaDimensionAgenteType.desde(fila) for fila in trafico.por_status],
            por_verificacion=[FilaDimensionAgenteType.desde(fila) for fila in trafico.por_verificacion],
            serie=[PuntoTraficoAgenteType.desde(punto) for punto in trafico.serie],
            procedencia=ProcedenciaAgenteType.desde(trafico.procedencia),
        )


@strawberry.type
class AgenteType:
    id: strawberry.ID
    nombre: str
    categoria: str
    patrones_ua: list[str]
    rangos_ip: list[str]
    dns_sufijos: list[str]
    verifica_firma: bool
    notas: str
    activo: bool
    creado_en: str
    actualizado_en: str

    @classmethod
    def desde(cls, agente) -> "AgenteType":
        return cls(
            id=agente.id,
            nombre=agente.nombre,
            categoria=agente.categoria,
            patrones_ua=agente.patrones_ua,
            rangos_ip=agente.rangos_ip,
            dns_sufijos=agente.dns_sufijos,
            verifica_firma=agente.verifica_firma,
            notas=agente.notas,
            activo=agente.activo,
            creado_en=agente.creado_en.isoformat(),
            actualizado_en=agente.actualizado_en.isoformat(),
        )


# --- Panel Types ---

@strawberry.type
class FilaReferidosIAType:
    plataforma: str
    sesiones: int
    rutas_top: list[FilaDimensionType]


@strawberry.type
class PanelAgentesResumenType:
    propiedad_id: str
    desde: datetime
    hasta: datetime
    peticiones_por_clase: list[FilaDimensionType]
    top_agentes: list[FilaDimensionType]
    bytes_por_clase: list[FilaDimensionType]
    top_rutas: list[FilaDimensionType]
    status_por_clase: list[FilaDimensionType]
    serie_por_categoria: list[FilaDimensionType]
    referidos_ia: list[FilaReferidosIAType]
    coste_estimado_por_clase: list[FilaDimensionType]
    extraido_en: datetime

    @classmethod
    def desde(cls, panel) -> "PanelAgentesResumenType":
        return cls(
            propiedad_id=panel.propiedad_id,
            desde=panel.desde,
            hasta=panel.hasta,
            peticiones_por_clase=[FilaDimensionType(clave=k, valor=v) for k, v in panel.peticiones_por_clase.items()],
            top_agentes=[FilaDimensionType(clave=k, valor=v) for k, v in panel.top_agentes],
            bytes_por_clase=[FilaDimensionType(clave=k, valor=v) for k, v in panel.bytes_por_clase.items()],
            top_rutas=[FilaDimensionType(clave=k, valor=v) for k, v in panel.top_rutas],
            status_por_clase=[FilaDimensionType(clave=k, valor=v) for k, v in panel.status_por_clase.items()],
            serie_por_categoria=[FilaDimensionType(clave=k, valor=v) for k, v in panel.serie_por_categoria.items()],
            referidos_ia=[
                FilaReferidosIAType(
                    plataforma=r.plataforma,
                    sesiones=r.sesiones,
                    rutas_top=[FilaDimensionType(clave=k, valor=v) for k, v in r.rutas_top],
                )
                for r in panel.referidos_ia
            ],
            coste_estimado_por_clase=[FilaDimensionType(clave=k, valor=int(v * 10000)) for k, v in panel.coste_estimado_por_clase.items()],
            extraido_en=panel.extraido_en,
        )


@strawberry.type
class AnalisisCosteBeneficioType:
    categoria: str
    peticiones: int
    bytes_servidos: int
    coste_estimado_usd: float
    referidos_ia: int
    valor_referido_estimado_usd: float
    ratio_coste_beneficio: float
    recomendacion: str


@strawberry.type
class DecisionAgenteType:
    id: strawberry.ID
    propiedad_id: str
    agente_id: str | None
    categoria: str | None
    decision: str
    motivo: str
    rutas_afectadas: list[str]
    creado_en: datetime
    creado_por: str
    efecto_medido: bool
    metricas_antes: str
    metricas_despues: str


# --- Alerts Types ---

@strawberry.type
class ReglaAlertaType:
    id: strawberry.ID
    propiedad_id: str
    nombre: str
    tipo: str
    metrica: str
    condicion: str
    ventana: str
    agregacion: str
    severidad: str
    canales_notificacion: list[str]
    silencio_minutos: int
    estado: str
    ultima_evaluacion_en: datetime | None
    ultima_disparo_en: datetime | None
    creado_en: datetime
    actualizado_en: datetime

    @classmethod
    def desde(cls, regla) -> "ReglaAlertaType":
        return cls(
            id=regla.id,
            propiedad_id=regla.propiedad_id,
            nombre=regla.nombre,
            tipo=regla.tipo,
            metrica=regla.metrica,
            condicion=regla.condicion,
            ventana=regla.ventana,
            agregacion=regla.agregacion,
            severidad=regla.severidad,
            canales_notificacion=regla.canales_notificacion,
            silencio_minutos=regla.silencio_minutos,
            estado=regla.estado,
            ultima_evaluacion_en=regla.ultima_evaluacion_en,
            ultima_disparo_en=regla.ultima_disparo_en,
            creado_en=regla.creado_en,
            actualizado_en=regla.actualizado_en,
        )


@strawberry.type
class CanalNotificacionType:
    id: strawberry.ID
    tipo: str
    nombre: str
    config: str
    estado: str
    ultima_entrega_en: datetime | None
    creado_en: datetime

    @classmethod
    def desde(cls, canal) -> "CanalNotificacionType":
        return cls(
            id=canal.id,
            tipo=canal.tipo,
            nombre=canal.nombre,
            config=json.dumps(canal.config) if isinstance(canal.config, dict) else str(canal.config),
            estado=canal.estado,
            ultima_entrega_en=canal.ultima_entrega_en,
            creado_en=canal.creado_en,
        )


@strawberry.type
class NotificacionType:
    id: strawberry.ID
    regla_id: str
    canal_id: str
    ocurrio_en: datetime
    titulo: str
    cuerpo: str
    severidad: str
    estado: str
    intentos: int
    proximo_intento_en: datetime | None
    error_ultimo_intento: str | None
    creado_en: datetime

    @classmethod
    def desde(cls, notif) -> "NotificacionType":
        return cls(
            id=notif.id,
            regla_id=notif.regla_id,
            canal_id=notif.canal_id,
            ocurrio_en=notif.ocurrio_en,
            titulo=notif.titulo,
            cuerpo=notif.cuerpo,
            severidad=notif.severidad,
            estado=notif.estado,
            intentos=notif.intentos,
            proximo_intento_en=notif.proximo_intento_en,
            error_ultimo_intento=notif.error_ultimo_intento,
            creado_en=notif.creado_en,
        )


# --- Synthetic Types ---

@strawberry.type
class SondaType:
    id: strawberry.ID
    propiedad_id: str
    nombre: str
    tipo: str
    objetivo: str
    metodo: str
    headers: str
    cuerpo: str | None
    esperado_status: int
    esperado_contiene: str | None
    verificar_certificado: bool
    dias_alerta_expiracion: int
    intervalo_segundos: int
    timeout_segundos: int
    regiones: list[str]
    activo: bool
    creado_en: datetime
    actualizado_en: datetime

    @classmethod
    def desde(cls, sonda) -> "SondaType":
        return cls(
            id=sonda.id,
            propiedad_id=sonda.propiedad_id,
            nombre=sonda.nombre,
            tipo=sonda.tipo,
            objetivo=sonda.objetivo,
            metodo=sonda.metodo,
            headers=json.dumps(sonda.headers) if isinstance(sonda.headers, dict) else str(sonda.headers),
            cuerpo=sonda.cuerpo,
            esperado_status=sonda.esperado_status,
            esperado_contiene=sonda.esperado_contiene,
            verificar_certificado=sonda.verificar_certificado,
            dias_alerta_expiracion=sonda.dias_alerta_expiracion,
            intervalo_segundos=sonda.intervalo_segundos,
            timeout_segundos=sonda.timeout_segundos,
            regiones=sonda.regiones,
            activo=sonda.activo,
            creado_en=sonda.creado_en,
            actualizado_en=sonda.actualizado_en,
        )


@strawberry.type
class EjecucionSondaType:
    id: strawberry.ID
    sonda_id: str
    propiedad_id: str
    region: str
    iniciado_en: datetime
    finalizado_en: datetime | None
    exito: bool
    status_code: int | None
    latencia_ms: int | None
    dns_resuelto: bool
    dns_latencia_ms: int | None
    ips_resueltas: list[str]
    tcp_conectado: bool
    tcp_latencia_ms: int | None
    tls_establecido: bool
    tls_latencia_ms: int | None
    tls_version: str | None
    cert_expira_en: datetime | None
    cert_dias_restantes: int | None
    error: str | None
    error_tipo: str | None
    respuesta_tamano: int | None
    respuesta_headers: str
    creado_en: datetime

    @classmethod
    def desde(cls, ejecucion) -> "EjecucionSondaType":
        return cls(
            id=ejecucion.id,
            sonda_id=ejecucion.sonda_id,
            propiedad_id=ejecucion.propiedad_id,
            region=ejecucion.region,
            iniciado_en=ejecucion.iniciado_en,
            finalizado_en=ejecucion.finalizado_en,
            exito=ejecucion.exito,
            status_code=ejecucion.status_code,
            latencia_ms=ejecucion.latencia_ms,
            dns_resuelto=ejecucion.dns_resuelto,
            dns_latencia_ms=ejecucion.dns_latencia_ms,
            ips_resueltas=ejecucion.ips_resueltas,
            tcp_conectado=ejecucion.tcp_conectado,
            tcp_latencia_ms=ejecucion.tcp_latencia_ms,
            tls_establecido=ejecucion.tls_establecido,
            tls_latencia_ms=ejecucion.tls_latencia_ms,
            tls_version=ejecucion.tls_version,
            cert_expira_en=ejecucion.cert_expira_en,
            cert_dias_restantes=ejecucion.cert_dias_restantes,
            error=ejecucion.error,
            error_tipo=ejecucion.error_tipo,
            respuesta_tamano=ejecucion.respuesta_tamano,
            respuesta_headers=json.dumps(ejecucion.respuesta_headers) if isinstance(ejecucion.respuesta_headers, dict) else str(ejecucion.respuesta_headers),
            creado_en=ejecucion.creado_en,
        )


@strawberry.type
class ResumenSondaType:
    sonda_id: str
    nombre: str
    tipo: str
    objetivo: str
    disponibilidad: float
    latencia_p50: float | None
    latencia_p95: float | None
    total_ejecuciones: int
    exitosas: int
    fallidas: int
    cert_expira_en: datetime | None
    cert_dias_restantes: int | None
    ultima_ejecucion: EjecucionSondaType | None


@strawberry.type
class ProcedenciaSondaType:
    fuente: str
    canal: str
    grano: str
    extraido_en: datetime
    datos_hasta: datetime | None
    completitud: str
    zona_horaria: str


@strawberry.type
class ReporteSondaType:
    desde: datetime
    hasta: datetime
    grano: str
    sondas: list[ResumenSondaType]
    procedencia: ProcedenciaSondaType

    @classmethod
    def desde(cls, reporte) -> "ReporteSondaType":
        return cls(
            desde=reporte.desde,
            hasta=reporte.hasta,
            grano=reporte.grano,
            sondas=[
                ResumenSondaType(
                    sonda_id=s.sonda_id,
                    nombre=s.nombre,
                    tipo=s.tipo,
                    objetivo=s.objetivo,
                    disponibilidad=s.disponibilidad,
                    latencia_p50=s.latencia_p50,
                    latencia_p95=s.latencia_p95,
                    total_ejecuciones=s.total_ejecuciones,
                    exitosas=s.exitosas,
                    fallidas=s.fallidas,
                    cert_expira_en=s.cert_expira_en,
                    cert_dias_restantes=s.cert_dias_restantes,
                    ultima_ejecucion=EjecucionSondaType.desde(s.ultima_ejecucion) if s.ultima_ejecucion else None,
                )
                for s in reporte.sondas
            ],
            procedencia=ProcedenciaSondaType(
                fuente=reporte.procedencia.fuente,
                canal=reporte.procedencia.canal,
                grano=reporte.procedencia.grano,
                extraido_en=reporte.procedencia.extraido_en,
                datos_hasta=reporte.procedencia.datos_hasta,
                completitud=reporte.procedencia.completitud,
                zona_horaria=reporte.procedencia.zona_horaria,
            ),
        )
