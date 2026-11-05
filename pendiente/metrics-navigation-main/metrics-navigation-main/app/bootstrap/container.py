"""Composición de dependencias: qué implementación se inyecta en cada puerto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from app.bootstrap.settings import Settings
from app.modules.agents.application.classifier import (
    AgenteClassifier,
    AgenteEnriquecedor,
    AgenteVerificador,
)
from app.modules.agents.application.panel import PanelAgentesService
from app.modules.agents.application.reports import AgenteTraficoService
from app.modules.agents.application.service import AgenteAdminService
from app.modules.agents.persistence.mongo import (
    MongoAgenteRepository,
    MongoEvidenciaRepository,
    MongoIdentidadAgenteRepository,
    MongoVisitaAgenteRepository,
    ensure_indexes as ensure_agents_indexes,
)
from app.modules.alerts.application.dispatcher import NotificationDispatcher
from app.modules.alerts.application.evaluator import AlertEvaluator
from app.modules.alerts.application.service import AlertasService
from app.modules.alerts.persistence.mongo import (
    MongoCanalNotificacionRepository,
    MongoNotificacionRepository,
    MongoReglaAlertaRepository,
    ensure_indexes as ensure_alerts_indexes,
)
from app.modules.integrations.application.service import IntegrationsService
from app.modules.integrations.persistence.mongo import (
    MongoEjecucionSincronizacionRepository,
    MongoIntegracionRepository,
    MongoMetricaIntegracionRepository,
    ensure_indexes as ensure_integrations_indexes,
)
from app.modules.synthetic.application.service import SyntheticService
from app.modules.synthetic.persistence.mongo import (
    MongoEjecucionSondaRepository,
    MongoMetricaSondaRepository,
    MongoSondaRepository,
    ensure_indexes as ensure_synthetic_indexes,
)
from app.modules.edge.application.ingest import EdgeService
from app.modules.edge.application.reports import EdgeTraficoService
from app.modules.edge.persistence.mongo import (
    MongoEdgeVisitRepository,
    ensure_indexes as ensure_edge_indexes,
)
from app.modules.navigation.application.ingest import NavigationService
from app.modules.navigation.application.reports import TraficoService
from app.modules.navigation.persistence.mongo import (
    MongoEventoRepository,
    ensure_indexes as ensure_navigation_indexes,
)
from app.modules.properties.application.services import PropertiesService
from app.modules.properties.persistence.mongo import (
    MongoCanalRepository,
    MongoDominioRepository,
    MongoPropiedadRepository,
    ensure_indexes as ensure_properties_indexes,
)
from app.shared.security import SlidingWindowLimiter


@dataclass
class Container:
    settings: Settings
    client: Any
    db: Any
    propiedades: MongoPropiedadRepository
    dominios: MongoDominioRepository
    canales: MongoCanalRepository
    eventos: MongoEventoRepository
    edge_visitas: MongoEdgeVisitRepository
    agentes: MongoAgenteRepository
    agente_identidades: MongoIdentidadAgenteRepository
    agente_visitas: MongoVisitaAgenteRepository
    agente_evidencias: MongoEvidenciaRepository
    alertas_reglas: MongoReglaAlertaRepository
    alertas_canales: MongoCanalNotificacionRepository
    alertas_notificaciones: MongoNotificacionRepository
    sondas: MongoSondaRepository
    sonda_ejecuciones: MongoEjecucionSondaRepository
    sonda_metricas: MongoMetricaSondaRepository
    integraciones: MongoIntegracionRepository
    integracion_ejecuciones: MongoEjecucionSincronizacionRepository
    integracion_metricas: MongoMetricaIntegracionRepository
    properties_service: PropertiesService
    navigation_service: NavigationService
    trafico_service: TraficoService
    edge_service: EdgeService
    edge_trafico_service: EdgeTraficoService
    agente_classifier: AgenteClassifier
    agente_verificador: AgenteVerificador
    agente_enriquecedor: AgenteEnriquecedor
    agente_admin_service: AgenteAdminService
    agente_trafico_service: AgenteTraficoService
    panel_agentes_service: PanelAgentesService
    alerta_evaluator: AlertEvaluator
    alerta_dispatcher: NotificationDispatcher
    alertas_service: AlertasService
    synthetic_service: SyntheticService
    integrations_service: IntegrationsService
    limiter: SlidingWindowLimiter

    async def close(self) -> None:
        await self.alerta_dispatcher.close()
        await self.synthetic_service.close()
        self.client.close()


async def build_container(settings: Settings) -> Container:
    client = _crear_cliente(settings)
    db = client[settings.mongo_db]

    propiedades = MongoPropiedadRepository(db)
    dominios = MongoDominioRepository(db)
    canales = MongoCanalRepository(db)
    eventos = MongoEventoRepository(db)
    edge_visitas = MongoEdgeVisitRepository(db, settings.ip_hash_salt)
    agentes = MongoAgenteRepository(db)
    agente_identidades = MongoIdentidadAgenteRepository(db)
    agente_visitas = MongoVisitaAgenteRepository(db)
    agente_evidencias = MongoEvidenciaRepository(db)

    await ensure_properties_indexes(db)
    await ensure_navigation_indexes(db)
    await ensure_edge_indexes(db)
    await ensure_agents_indexes(db)
    await ensure_alerts_indexes(db)
    await ensure_synthetic_indexes(db)
    await ensure_integrations_indexes(db)

    properties = PropertiesService(propiedades, dominios, canales)
    limiter = SlidingWindowLimiter(settings.beacon_rate_limit_per_minute)
    navigation = NavigationService(properties, eventos, limiter, settings.ip_hash_salt)
    trafico = TraficoService(properties, eventos)

    agente_classifier = AgenteClassifier(agentes)
    agente_verificador = AgenteVerificador(
        agente_identidades, agente_evidencias, agentes, settings.ip_hash_salt
    )
    agente_enriquecedor = AgenteEnriquecedor(
        agente_classifier, agente_verificador, agente_visitas
    )
    agente_admin_service = AgenteAdminService(agentes)
    agente_trafico_service = AgenteTraficoService(properties, agente_visitas)
    panel_agentes_service = PanelAgentesService(properties, agente_visitas, eventos)

    edge_service = EdgeService(
        properties,
        edge_visitas,
        limiter,
        settings.ip_hash_salt,
        agente_enriquecedor=agente_enriquecedor,
    )
    edge_trafico_service = EdgeTraficoService(properties, edge_visitas)

    sondas = MongoSondaRepository(db)
    sonda_ejecuciones = MongoEjecucionSondaRepository(db)
    sonda_metricas = MongoMetricaSondaRepository(db)
    synthetic_service = SyntheticService(properties, sondas, sonda_ejecuciones, sonda_metricas)

    alertas_reglas = MongoReglaAlertaRepository(db)
    alertas_canales = MongoCanalNotificacionRepository(db)
    alertas_notificaciones = MongoNotificacionRepository(db)
    alerta_evaluator = AlertEvaluator(
        alertas_reglas,
        properties,
        trafico_service=trafico,
        edge_trafico_service=edge_trafico_service,
        agente_trafico_service=agente_trafico_service,
        synthetic_service=synthetic_service,
    )
    alerta_dispatcher = NotificationDispatcher(
        alertas_notificaciones, alertas_canales, settings.model_dump()
    )
    alertas_service = AlertasService(
        alerta_evaluator,
        alerta_dispatcher,
        alertas_reglas,
        alertas_notificaciones,
        alertas_canales,
    )

    integraciones = MongoIntegracionRepository(db)
    integracion_ejecuciones = MongoEjecucionSincronizacionRepository(db)
    integracion_metricas = MongoMetricaIntegracionRepository(db)
    integrations_service = IntegrationsService(properties, integraciones, integracion_ejecuciones, integracion_metricas)

    return Container(
        settings=settings,
        client=client,
        db=db,
        propiedades=propiedades,
        dominios=dominios,
        canales=canales,
        eventos=eventos,
        edge_visitas=edge_visitas,
        agentes=agentes,
        agente_identidades=agente_identidades,
        agente_visitas=agente_visitas,
        agente_evidencias=agente_evidencias,
        alertas_reglas=alertas_reglas,
        alertas_canales=alertas_canales,
        alertas_notificaciones=alertas_notificaciones,
        sondas=sondas,
        sonda_ejecuciones=sonda_ejecuciones,
        sonda_metricas=sonda_metricas,
        integraciones=integraciones,
        integracion_ejecuciones=integracion_ejecuciones,
        integracion_metricas=integracion_metricas,
        properties_service=properties,
        navigation_service=navigation,
        trafico_service=trafico,
        edge_service=edge_service,
        edge_trafico_service=edge_trafico_service,
        agente_classifier=agente_classifier,
        agente_verificador=agente_verificador,
        agente_enriquecedor=agente_enriquecedor,
        agente_admin_service=agente_admin_service,
        agente_trafico_service=agente_trafico_service,
        panel_agentes_service=panel_agentes_service,
        alerta_evaluator=alerta_evaluator,
        alerta_dispatcher=alerta_dispatcher,
        alertas_service=alertas_service,
        synthetic_service=synthetic_service,
        integrations_service=integrations_service,
        limiter=limiter,
    )


def _crear_cliente(settings: Settings):
    if settings.storage == "memory":
        return _cliente_memoria()
    if settings.storage == "mongo":
        if not settings.mongo_uri:
            raise RuntimeError("STORAGE=mongo requiere MONGO_URI.")
        return AsyncIOMotorClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    if settings.storage == "auto":
        if settings.mongo_uri:
            return AsyncIOMotorClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
        if settings.es_local:
            return _cliente_memoria()
        raise RuntimeError("En produccion configura MONGO_URI o STORAGE=mongo.")
    raise RuntimeError(f"STORAGE desconocido: {settings.storage}")


def _cliente_memoria():
    try:
        from mongomock_motor import AsyncMongoMockClient
    except ImportError as exc:  # pragma: no cover - solo en instalaciones sin dev extras
        raise RuntimeError(
            "Para desarrollo local sin MongoDB instala `mongomock-motor` "
            "(pip install -e \".[dev]\") o configura MONGO_URI."
        ) from exc
    return AsyncMongoMockClient()
