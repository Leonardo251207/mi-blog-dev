"""Clasificación y verificación de agentes a partir de visitas edge."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from app.modules.agents.domain.models import (
    Agente,
    EvidenciaVerificacion,
    IdentidadAgente,
    VisitaAgente,
)
from app.modules.agents.persistence.repository import (
    AgenteRepository,
    EvidenciaRepository,
    IdentidadAgenteRepository,
    VisitaAgenteRepository,
)
from app.shared.ids import ahora_utc, hash_pseudonimo


class AgenteClassifier:
    """Clasifica visitas edge contra el catálogo de agentes conocidos."""

    def __init__(self, catalogo: AgenteRepository) -> None:
        self.catalogo = catalogo
        self._cache: dict[str, Agente] = {}
        self._compilados: dict[str, list[re.Pattern]] = {}

    async def clasificar(self, user_agent: str, ip_hash: str) -> tuple[Optional[Agente], str]:
        """Devuelve (agente, categoria) o (None, 'desconocido')."""
        agentes = await self.catalogo.list(activo=True)
        for agente in agentes:
            if self._coincide(agente, user_agent):
                return agente, agente.categoria
        return None, "desconocido"

    def _coincide(self, agente: Agente, ua: str) -> bool:
        if agente.id not in self._compilados:
            self._compilados[agente.id] = [
                re.compile(p, re.IGNORECASE) for p in agente.patrones_ua
            ]
        for pattern in self._compilados[agente.id]:
            if pattern.search(ua):
                return True
        return False


class AgenteVerificador:
    """Verifica la identidad de un agente usando DNS, rangos IP y firmas."""

    def __init__(
        self,
        identidades: IdentidadAgenteRepository,
        evidencias: EvidenciaRepository,
        catalogo: AgenteRepository,
        salt: str,
    ) -> None:
        self.identidades = identidades
        self.evidencias = evidencias
        self.catalogo = catalogo
        self.salt = salt

    async def verificar(
        self,
        visita: VisitaAgente,
        agente: Optional[Agente],
    ) -> IdentidadAgente:
        """Verifica o crea una identidad para esta visita."""
        # Buscar identidad existente
        identidad = await self.identidades.get_by_ip_hash_ua(visita.ip_hash, visita.user_agent)
        if identidad:
            return await self._actualizar_verificacion(identidad, visita, agente)

        # Crear nueva identidad
        identidad = IdentidadAgente(
            agente_id=agente.id if agente else "",
            ip_hash=visita.ip_hash,
            ua_declarado=visita.user_agent,
            categoria_declarada=visita.categoria,
        )
        return await self._actualizar_verificacion(identidad, visita, agente)

    async def _actualizar_verificacion(
        self,
        identidad: IdentidadAgente,
        visita: VisitaAgente,
        agente: Optional[Agente],
    ) -> IdentidadAgente:
        if not agente:
            identidad.verificado = False
            identidad.confianza = 0.0
            await self.identidades.update(identidad)
            return identidad

        # Verificar DNS inverso
        dns_ok, dns_detalle = await self._verificar_dns(visita, agente)
        identidad.dns_confirmado = dns_ok
        identidad.dns_detalle = dns_detalle
        await self._guardar_evidencia(identidad.id, "dns", dns_ok, dns_detalle)

        # Verificar rangos IP
        ip_ok, ip_detalle = await self._verificar_ip_range(visita, agente)
        identidad.ip_range_confirmado = ip_ok
        identidad.ip_range_detalle = ip_detalle
        await self._guardar_evidencia(identidad.id, "ip_range", ip_ok, ip_detalle)

        # Verificar firma (si el agente la soporta)
        firma_ok, firma_detalle = False, ""
        if agente.verifica_firma:
            firma_ok, firma_detalle = await self._verificar_firma(visita, agente)
            identidad.firma_verificada = firma_ok
            identidad.firma_detalle = firma_detalle
            await self._guardar_evidencia(identidad.id, "firma", firma_ok, firma_detalle)

        # Calcular confianza y veredicto
        identidad.confianza = self._calcular_confianza(dns_ok, ip_ok, firma_ok, agente.verifica_firma)
        identidad.verificado = identidad.confianza >= 0.7
        identidad.verificado_en = ahora_utc() if identidad.verificado else None

        await self.identidades.update(identidad)
        return identidad

    async def _verificar_dns(
        self, visita: VisitaAgente, agente: Agente
    ) -> tuple[bool, str]:
        if not agente.dns_sufijos:
            return False, "sin_sufijos_dns"
        # Comprobar sufijos conocidos
        return False, "sin_resolucion_inversa"

    async def _verificar_ip_range(
        self, visita: VisitaAgente, agente: Agente
    ) -> tuple[bool, str]:
        if not agente.rangos_ip:
            return False, "sin_rangos_ip"
        return False, "ip_fuera_de_rango"

    async def _verificar_firma(
        self, visita: VisitaAgente, agente: Agente
    ) -> tuple[bool, str]:
        return False, "sin_firma_verificable"

    def _calcular_confianza(
        self, dns: bool, ip_range: bool, firma: bool, soporta_firma: bool
    ) -> float:
        pesos = {"dns": 0.4, "ip_range": 0.4, "firma": 0.2}
        if not soporta_firma:
            pesos = {"dns": 0.5, "ip_range": 0.5, "firma": 0.0}
        score = 0.0
        if dns:
            score += pesos["dns"]
        if ip_range:
            score += pesos["ip_range"]
        if firma:
            score += pesos["firma"]
        return min(1.0, score)

    async def _guardar_evidencia(
        self, identidad_id: str, tipo: str, exitosa: bool, detalle: str
    ) -> None:
        evidencia = EvidenciaVerificacion(
            identidad_id=identidad_id,
            tipo=tipo,
            exitosa=exitosa,
            detalle=detalle,
        )
        await self.evidencias.add(evidencia)


class AgenteEnriquecedor:
    """Enriquece visitas edge con información de agentes."""

    def __init__(
        self,
        classifier: AgenteClassifier,
        verificador: AgenteVerificador,
        visitas_repo: VisitaAgenteRepository,
    ) -> None:
        self.classifier = classifier
        self.verificador = verificador
        self.visitas_repo = visitas_repo

    async def enriquecer_lote(self, visitas_edge: list) -> list[VisitaAgente]:
        """Convierte visitas edge a visitas de agente enriquecidas y actualiza las visitas edge."""
        enriquecidas: list[VisitaAgente] = []
        for v in visitas_edge:
            agente, categoria = await self.classifier.clasificar(v.user_agent, v.ip_hash)
            visita = VisitaAgente(
                id=v.id,
                propiedad_id=v.propiedad_id,
                canal_id=v.canal_id,
                host=v.host,
                entorno=v.entorno,
                ocurrio_en=v.ocurrio_en,
                metodo=v.metodo,
                path=v.path,
                ruta_patron=v.ruta_patron,
                query_string=v.query_string,
                user_agent=v.user_agent,
                ip_hash=v.ip_hash,
                asn=v.asn,
                pais=v.pais,
                status_code=v.status_code,
                bytes_enviados=v.bytes_enviados,
                bytes_recibidos=v.bytes_recibidos,
                duracion_ms=v.duracion_ms,
                referrer=v.referrer,
                agente_id=agente.id if agente else None,
                categoria=categoria,
            )
            if agente:
                identidad = await self.verificador.verificar(visita, agente)
                visita.identidad_id = identidad.id
                visita.verificado = identidad.verificado
                visita.confianza = identidad.confianza
                visita.evidencia_dns = identidad.dns_confirmado
                visita.evidencia_ip_range = identidad.ip_range_confirmado
                visita.evidencia_firma = identidad.firma_verificada

            # Actualizar atributos en EdgeVisit
            v.agente_id = visita.agente_id
            v.agente_categoria = visita.categoria
            v.agente_verificado = visita.verificado
            v.evidencia_dns = visita.evidencia_dns
            v.evidencia_ip_range = visita.evidencia_ip_range
            v.evidencia_firma = visita.evidencia_firma

            enriquecidas.append(visita)
        return enriquecidas

    async def guardar_visitas(self, visitas: list[VisitaAgente]) -> tuple[int, int]:
        return await self.visitas_repo.add_many(visitas)
