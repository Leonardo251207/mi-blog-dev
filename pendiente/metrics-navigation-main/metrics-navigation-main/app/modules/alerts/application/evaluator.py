"""Evaluador de reglas de alerta."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from app.modules.alerts.domain.models import EvaluacionRegla, ReglaAlerta
from app.modules.alerts.persistence.repository import ReglaAlertaRepository
from app.modules.properties.application.services import PropertiesService
from app.shared.ids import ahora_utc


class AlertEvaluator:
    """Evalúa reglas de alerta contra métricas agregadas."""

    def __init__(
        self,
        reglas: ReglaAlertaRepository,
        properties: PropertiesService,
        trafico_service: Any = None,
        edge_trafico_service: Any = None,
        agente_trafico_service: Any = None,
        synthetic_service: Any = None,
    ) -> None:
        self.reglas = reglas
        self.properties = properties
        self.trafico_service = trafico_service
        self.edge_trafico_service = edge_trafico_service
        self.agente_trafico_service = agente_trafico_service
        self.synthetic_service = synthetic_service

    async def evaluar_todas(self) -> list[EvaluacionRegla]:
        """Evalúa todas las reglas activas."""
        reglas = await self.reglas.list_activas()
        resultados = []
        for regla in reglas:
            resultado = await self.evaluar(regla)
            resultados.append(resultado)
            # Actualizar timestamp de evaluación
            regla.ultima_evaluacion_en = ahora_utc()
            if resultado.disparo:
                regla.ultima_disparo_en = ahora_utc()
            await self.reglas.update(regla)
        return resultados

    async def evaluar(self, regla: ReglaAlerta) -> EvaluacionRegla:
        """Evalúa una regla individual."""
        # Verificar silencio
        if regla.ultima_disparo_en:
            silencio_hasta = regla.ultima_disparo_en + timedelta(minutes=regla.silencio_minutos)
            if ahora_utc() < silencio_hasta:
                return EvaluacionRegla(
                    regla_id=regla.id,
                    disparo=False,
                    valor_actual=0,
                    mensaje=f"En silencio hasta {silencio_hasta.isoformat()}",
                )

        # Obtener valor actual según tipo de regla
        if regla.tipo == "UMBRAL":
            return await self._evaluar_umbral(regla)
        elif regla.tipo == "AUSENCIA":
            return await self._evaluar_ausencia(regla)
        elif regla.tipo == "ANOMALIA":
            return await self._evaluar_anomalia(regla)
        elif regla.tipo == "ESTADO":
            return await self._evaluar_estado(regla)
        elif regla.tipo == "AGENTE_NUEVO":
            return await self._evaluar_agente_nuevo(regla)
        else:
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=False,
                valor_actual=0,
                mensaje=f"Tipo de regla desconocido: {regla.tipo}",
            )

    async def _evaluar_umbral(self, regla: ReglaAlerta) -> EvaluacionRegla:
        """Evalúa regla de umbral: metrica >/< valor."""
        valor = await self._obtener_metrica(regla)
        if valor is None:
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=False,
                valor_actual=0,
                mensaje="No hay datos para la métrica",
            )

        match = re.match(r"([<>]=?|==|!=)\s*([\d.]+)", regla.condicion.strip())
        if not match:
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=False,
                valor_actual=valor,
                mensaje=f"Condición inválida: {regla.condicion}",
            )

        operador, umbral_str = match.groups()
        umbral = float(umbral_str)

        disparo = self._comparar(valor, operador, umbral)
        return EvaluacionRegla(
            regla_id=regla.id,
            disparo=disparo,
            valor_actual=valor,
            umbral=umbral,
            mensaje=f"{regla.metrica} {operador} {umbral} (actual: {valor})" if disparo else f"{regla.metrica} = {valor}, no cruza {operador} {umbral}",
        )

    async def _evaluar_ausencia(self, regla: ReglaAlerta) -> EvaluacionRegla:
        """Evalúa regla de ausencia: sin señal en ventana."""
        ventana = self._parsear_ventana(regla.ventana)
        desde = ahora_utc() - ventana

        valor = await self._obtener_metrica(regla, desde=desde)

        if valor is None or valor == 0:
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=True,
                valor_actual=valor or 0,
                mensaje=f"Sin {regla.metrica} en los últimos {regla.ventana}",
            )

        return EvaluacionRegla(
            regla_id=regla.id,
            disparo=False,
            valor_actual=valor,
            mensaje=f"Hay {valor} {regla.metrica} en la ventana",
        )

    async def _evaluar_anomalia(self, regla: ReglaAlerta) -> EvaluacionRegla:
        """Evalúa regla de anomalía: desviación de baseline."""
        ventana_baseline = timedelta(days=7)
        desde_baseline = ahora_utc() - ventana_baseline
        ventana_actual = self._parsear_ventana(regla.ventana)
        desde_actual = ahora_utc() - ventana_actual

        valor_actual = await self._obtener_metrica(regla, desde=desde_actual)
        valor_baseline = await self._obtener_metrica(regla, desde=desde_baseline, agregacion="avg")

        if valor_actual is None or valor_baseline is None or valor_baseline == 0:
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=False,
                valor_actual=valor_actual or 0,
                mensaje="Datos insuficientes para baseline",
            )

        match = re.match(r"([<>]=?)\s*(?:p50|p95|baseline)\s*\*\s*([\d.]+)", regla.condicion.strip())
        if not match:
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=False,
                valor_actual=valor_actual,
                mensaje=f"Condición de anomalía inválida: {regla.condicion}",
            )

        operador, factor_str = match.groups()
        factor = float(factor_str)
        umbral = valor_baseline * factor

        disparo = self._comparar(valor_actual, operador, umbral)
        return EvaluacionRegla(
            regla_id=regla.id,
            disparo=disparo,
            valor_actual=valor_actual,
            umbral=umbral,
            mensaje=f"Anomalía: {regla.metrica}={valor_actual} vs baseline={valor_baseline}*{factor}={umbral}" if disparo else f"Normal: {regla.metrica}={valor_actual} vs baseline={valor_baseline}",
        )

    async def _evaluar_estado(self, regla: ReglaAlerta) -> EvaluacionRegla:
        """Evalúa cambio de estado: canal DEGRADADO, integración ERROR, propiedad PAUSADA, etc."""
        match = re.match(r"==\s*(\w+)", regla.condicion.strip())
        if not match:
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=False,
                valor_actual=0,
                mensaje=f"Condición de estado inválida: {regla.condicion}",
            )

        estado_objetivo = match.group(1).upper()
        try:
            propiedad = await self.properties.obtener_por_id(regla.propiedad_id)
        except Exception:
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=False,
                valor_actual=0,
                mensaje=f"Propiedad {regla.propiedad_id} no encontrada",
            )

        if regla.metrica in ("sitio_estado", "propiedad_estado"):
            disparo = (propiedad.estado.value.upper() == estado_objetivo)
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=disparo,
                valor_actual=1 if disparo else 0,
                mensaje=f"Propiedad en estado {propiedad.estado.value}" if disparo else f"Propiedad en estado {propiedad.estado.value} (esperaba {estado_objetivo})",
            )

        canales = await self.properties.canales_de(propiedad.id)
        canal_coincide = any(c.estado.value.upper() == estado_objetivo for c in canales)
        return EvaluacionRegla(
            regla_id=regla.id,
            disparo=canal_coincide,
            valor_actual=1 if canal_coincide else 0,
            mensaje=f"Canal en estado {estado_objetivo} detectado" if canal_coincide else f"Ningún canal en estado {estado_objetivo}",
        )

    async def _evaluar_agente_nuevo(self, regla: ReglaAlerta) -> EvaluacionRegla:
        """Evalúa agente no clasificado o desconocido agresivo."""
        match = re.match(r">\s*(\d+)", regla.condicion.strip())
        if not match:
            return EvaluacionRegla(
                regla_id=regla.id,
                disparo=False,
                valor_actual=0,
                mensaje=f"Condición de agente nuevo inválida: {regla.condicion}",
            )

        umbral = int(match.group(1))
        ventana = self._parsear_ventana(regla.ventana)
        desde = ahora_utc() - ventana

        propiedad = await self.properties.obtener_por_id(regla.propiedad_id)
        peticiones_desconocidas = 0
        if self.edge_trafico_service:
            try:
                t = await self.edge_trafico_service.trafico(
                    sitio_slug=propiedad.slug,
                    desde=desde,
                    hasta=ahora_utc(),
                    agente_categoria="desconocido",
                )
                peticiones_desconocidas = t.total_peticiones
            except Exception:
                pass

        disparo = peticiones_desconocidas > umbral
        return EvaluacionRegla(
            regla_id=regla.id,
            disparo=disparo,
            valor_actual=float(peticiones_desconocidas),
            umbral=float(umbral),
            mensaje=f"Agente nuevo/desconocido con {peticiones_desconocidas} reqs > {umbral}" if disparo else f"Tráfico desconocido ({peticiones_desconocidas}) bajo umbral {umbral}",
        )

    async def _obtener_metrica(
        self,
        regla: ReglaAlerta,
        desde: datetime | None = None,
        agregacion: str | None = None,
    ) -> float | None:
        """Obtiene el valor de una métrica para una propiedad en la ventana dada."""
        try:
            propiedad = await self.properties.obtener_por_id(regla.propiedad_id)
        except Exception:
            return None

        ahora = ahora_utc()
        if desde is None:
            ventana = self._parsear_ventana(regla.ventana)
            desde = ahora - ventana

        metrica = regla.metrica.lower()

        # Métricas de navegación (beacon)
        if metrica in ("pageviews", "sessions", "sesiones", "unique_visitors", "visitantes_unicos"):
            if not self.trafico_service:
                return None
            try:
                t = await self.trafico_service.trafico(
                    sitio_slug=propiedad.slug,
                    desde=desde,
                    hasta=ahora,
                )
                if metrica == "pageviews":
                    return float(t.pageviews)
                elif metrica in ("sessions", "sesiones"):
                    return float(t.sesiones)
                elif metrica in ("unique_visitors", "visitantes_unicos"):
                    return float(t.visitantes_unicos_estimados)
            except Exception:
                return 0.0

        # Métricas de Edge
        if metrica in ("agent_requests", "agent_bytes", "peticiones_edge", "bytes_edge"):
            if not self.edge_trafico_service:
                return None
            try:
                t = await self.edge_trafico_service.trafico(
                    sitio_slug=propiedad.slug,
                    desde=desde,
                    hasta=ahora,
                )
                if metrica in ("agent_requests", "peticiones_edge"):
                    return float(t.total_peticiones)
                elif metrica in ("agent_bytes", "bytes_edge"):
                    return float(t.total_bytes_enviados)
            except Exception:
                return 0.0

        # Métricas de Sondas Sintéticas
        if metrica in ("uptime_ratio", "disponibilidad", "synthetic_latency_p95", "latencia_p95"):
            if not self.synthetic_service:
                return None
            try:
                reporte = await self.synthetic_service.reporte(
                    sitio_slug=propiedad.slug,
                    desde=desde,
                    hasta=ahora,
                )
                if not reporte.sondas:
                    return 0.0
                if metrica in ("uptime_ratio", "disponibilidad"):
                    avg_disp = sum(s.disponibilidad for s in reporte.sondas) / len(reporte.sondas)
                    return float(avg_disp)
                elif metrica in ("synthetic_latency_p95", "latencia_p95"):
                    p95_vals = [s.latencia_p95 for s in reporte.sondas if s.latencia_p95 is not None]
                    return float(max(p95_vals)) if p95_vals else 0.0
            except Exception:
                return 0.0

        return 0.0

    def _parsear_ventana(self, ventana: str) -> timedelta:
        """Parsea ventana tipo '30m', '1h', '24h', '7d'."""
        match = re.match(r"(\d+)([mhd])", ventana.lower())
        if not match:
            return timedelta(minutes=30)
        valor, unidad = match.groups()
        valor = int(valor)
        if unidad == "m":
            return timedelta(minutes=valor)
        elif unidad == "h":
            return timedelta(hours=valor)
        elif unidad == "d":
            return timedelta(days=valor)
        return timedelta(minutes=30)

    def _comparar(self, valor: float, operador: str, umbral: float) -> bool:
        if operador == ">":
            return valor > umbral
        elif operador == ">=":
            return valor >= umbral
        elif operador == "<":
            return valor < umbral
        elif operador == "<=":
            return valor <= umbral
        elif operador == "==":
            return valor == umbral
        elif operador == "!=":
            return valor != umbral
        return False
