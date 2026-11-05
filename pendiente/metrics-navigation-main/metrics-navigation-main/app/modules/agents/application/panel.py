"""Servicio de panel: consultas agregadas para dashboards de agentes y referidos IA."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Optional

from app.modules.agents.domain.models import VisitaAgente
from app.modules.agents.domain.panel import (
    AnalisisCosteBeneficio,
    DecisionAgente,
    FilaReferidosIA,
    PanelAgentesResumen,
    ReferidoIA,
)
from app.modules.agents.persistence.repository import VisitaAgenteRepository
from app.modules.navigation.persistence.repository import EventoRepository
from app.modules.properties.application.services import PropertiesService
from app.shared.enums import Completitud, EstadoCanal, Grano, TipoCanal
from app.shared.errors import DomainError
from app.shared.ids import ahora_utc, host_de_referer
from app.shared.time import cubos, inicio_cubo, validar_rango

# Plataformas de IA conocidas para detectar referidos
PLATAFORMAS_IA = {
    "chatgpt.com": "chatgpt",
    "perplexity.ai": "perplexity",
    "copilot.microsoft.com": "copilot",
    "gemini.google.com": "gemini",
    "claude.ai": "claude",
    "you.com": "you",
    "phind.com": "phind",
    "poe.com": "poe",
}


def detectar_plataforma_ia(referrer: str) -> Optional[str]:
    """Detecta si un referrer viene de una plataforma de IA."""
    host = host_de_referer(referrer) or ""
    for dominio, plataforma in PLATAFORMAS_IA.items():
        if dominio in host:
            return plataforma
    return None


class PanelAgentesService:
    def __init__(
        self,
        properties: PropertiesService,
        visitas_agente: VisitaAgenteRepository,
        eventos_navegacion: EventoRepository,
    ) -> None:
        self.properties = properties
        self.visitas_agente = visitas_agente
        self.eventos_navegacion = eventos_navegacion

    async def panel_resumen(
        self,
        *,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
        grano: Grano = Grano.DIA,
    ) -> PanelAgentesResumen:
        """Genera el resumen completo para el panel de agentes (6 widgets + referidos)."""
        propiedad = await self.properties.obtener_sitio(sitio_slug)
        desde, hasta = validar_rango(desde, hasta, grano)

        # Obtener visitas de agentes (edge)
        visitas = await self.visitas_agente.list(propiedad.id, desde, hasta)

        # Widget 1: Peticiones por clase
        peticiones_por_clase = Counter(v.categoria for v in visitas)

        # Widget 2: Top 10 agentes por volumen
        top_agentes = Counter(v.agente_id or "desconocido" for v in visitas).most_common(10)

        # Widget 3: Bytes servidos por clase
        bytes_por_clase: dict[str, int] = defaultdict(int)
        for v in visitas:
            bytes_por_clase[v.categoria] += v.bytes_enviados

        # Widget 4: Top rutas rastreadas
        top_rutas = Counter(v.ruta_patron for v in visitas).most_common(10)

        # Widget 5: Códigos de respuesta por clase
        status_por_clase: dict[str, Counter] = defaultdict(Counter)
        for v in visitas:
            status_por_clase[v.categoria][str(v.status_code)] += 1
        status_por_clase_dict = {k: dict(v) for k, v in status_por_clase.items()}

        # Widget 6: Serie temporal por categoría
        serie_por_categoria: dict[str, list[tuple[datetime, int]]] = defaultdict(list)
        agrupados: dict[tuple[datetime, str], int] = defaultdict(int)
        for v in visitas:
            cubo = inicio_cubo(v.ocurrio_en, grano, propiedad.zona_horaria)
            agrupados[(cubo, v.categoria)] += 1
        for cubo in cubos(desde, hasta, grano, propiedad.zona_horaria):
            for cat in peticiones_por_clase.keys():
                count = agrupados.get((cubo, cat), 0)
                serie_por_categoria[cat].append((cubo, count))

        # Referidos de IA (desde beacon/navegación)
        referidos = await self._obtener_referidos_ia(propiedad.id, desde, hasta)

        # Coste estimado (muy aproximado: $0.10/GB egress)
        coste_estimado = {}
        for cat, bytes_cat in bytes_por_clase.items():
            gb = bytes_cat / (1024 ** 3)
            coste_estimado[cat] = round(gb * 0.10, 4)

        return PanelAgentesResumen(
            propiedad_id=propiedad.id,
            desde=desde,
            hasta=hasta,
            peticiones_por_clase=dict(peticiones_por_clase),
            top_agentes=top_agentes,
            bytes_por_clase=dict(bytes_por_clase),
            top_rutas=top_rutas,
            status_por_clase=status_por_clase_dict,
            serie_por_categoria=serie_por_categoria,
            referidos_ia=referidos,
            coste_estimado_por_clase=coste_estimado,
        )

    async def _obtener_referidos_ia(
        self, propiedad_id: str, desde: datetime, hasta: datetime
    ) -> list[FilaReferidosIA]:
        """Obtiene referidos de IA desde eventos de navegación (beacon)."""
        eventos = await self.eventos_navegacion.list(propiedad_id, desde, hasta)
        referidos_por_plataforma: dict[str, Counter] = defaultdict(Counter)
        rutas_por_plataforma: dict[str, Counter] = defaultdict(Counter)

        for ev in eventos:
            if ev.referrer:
                plataforma = detectar_plataforma_ia(ev.referrer)
                if plataforma:
                    referidos_por_plataforma[plataforma][ev.clave_sesion] += 1
                    rutas_por_plataforma[plataforma][ev.ruta_patron] += 1

        resultado = []
        for plataforma, sesiones in referidos_por_plataforma.items():
            resultado.append(
                FilaReferidosIA(
                    plataforma=plataforma,
                    sesiones=len(sesiones),
                    rutas_top=rutas_por_plataforma[plataforma].most_common(5),
                )
            )
        return resultado

    async def analisis_coste_beneficio(
        self,
        *,
        sitio_slug: str,
        desde: datetime,
        hasta: datetime,
    ) -> list[AnalisisCosteBeneficio]:
        """Analiza coste vs beneficio por categoría de agente."""
        propiedad = await self.properties.obtener_sitio(sitio_slug)
        desde, hasta = validar_rango(desde, hasta, Grano.DIA)

        visitas = await self.visitas_agente.list(propiedad.id, desde, hasta)
        referidos = await self._obtener_referidos_ia(propiedad.id, desde, hasta)

        # Agrupar por categoría
        por_categoria: dict[str, dict] = defaultdict(
            lambda: {"peticiones": 0, "bytes": 0, "referidos": 0}
        )
        for v in visitas:
            cat = v.categoria
            por_categoria[cat]["peticiones"] += 1
            por_categoria[cat]["bytes"] += v.bytes_enviados

        for ref in referidos:
            por_categoria[ref.plataforma]["referidos"] += ref.sesiones

        resultado = []
        for cat, datos in por_categoria.items():
            peticiones = datos["peticiones"]
            bytes_servidos = datos["bytes"]
            referidos_cat = datos["referidos"]

            # Coste estimado: $0.10/GB
            gb = bytes_servidos / (1024 ** 3)
            coste = round(gb * 0.10, 4)

            # Valor estimado por referido: $0.50 (muy aproximado)
            valor_referido = referidos_cat * 0.50

            ratio = valor_referido / coste if coste > 0 else float("inf")

            if ratio > 5:
                recomendacion = "permitir"
            elif ratio > 1:
                recomendacion = "permitir_cache"
            elif ratio > 0.2:
                recomendacion = "limitar"
            else:
                recomendacion = "bloquear"

            resultado.append(
                AnalisisCosteBeneficio(
                    categoria=cat,
                    peticiones=peticiones,
                    bytes_servidos=bytes_servidos,
                    coste_estimado_usd=coste,
                    referidos_ia=referidos_cat,
                    valor_referido_estimado_usd=round(valor_referido, 2),
                    ratio_coste_beneficio=round(ratio, 2),
                    recomendacion=recomendacion,
                )
            )

        return sorted(resultado, key=lambda x: x.ratio_coste_beneficio, reverse=True)

    async def registrar_decision(
        self,
        *,
        propiedad_id: str,
        agente_id: Optional[str],
        categoria: Optional[str],
        decision: str,
        motivo: str,
        rutas_afectadas: list[str],
        creado_por: str,
    ) -> DecisionAgente:
        """Registra una decisión sobre un agente/categoría."""
        decision_obj = DecisionAgente(
            propiedad_id=propiedad_id,
            agente_id=agente_id,
            categoria=categoria,
            decision=decision,
            motivo=motivo,
            rutas_afectadas=rutas_afectadas,
            creado_por=creado_por,
        )
        # TODO: Persistir en base de datos
        return decision_obj