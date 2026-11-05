"""Ejecutor de sondas sintéticas."""

from __future__ import annotations

import asyncio
import email.utils
import socket
import ssl
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.modules.synthetic.domain.models import EjecucionSonda, Sonda
from app.modules.synthetic.persistence.repository import EjecucionSondaRepository, SondaRepository
from app.shared.ids import ahora_utc, nueva_id


class SondaRunner:
    """Ejecuta sondas sintéticas y registra resultados."""

    def __init__(
        self,
        sondas: SondaRepository,
        ejecuciones: EjecucionSondaRepository,
    ) -> None:
        self.sondas = sondas
        self.ejecuciones = ejecuciones
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        await self.client.aclose()

    async def ejecutar_todas(self) -> int:
        """Ejecuta todas las sondas activas que toca según su intervalo."""
        sondas = await self.sondas.list_activas()
        ejecutadas = 0
        for sonda in sondas:
            if await self._debe_ejecutar(sonda):
                await self.ejecutar(sonda)
                ejecutadas += 1
        return ejecutadas

    async def _debe_ejecutar(self, sonda: Sonda) -> bool:
        """Verifica si la sonda debe ejecutarse según su intervalo."""
        ultima = await self.ejecuciones.ultima(sonda.id)
        if not ultima:
            return True
        transcurrido = (ahora_utc() - ultima.iniciado_en).total_seconds()
        return transcurrido >= sonda.intervalo_segundos

    async def ejecutar(self, sonda: Sonda) -> EjecucionSonda:
        """Ejecuta una sonda individual."""
        inicio = ahora_utc()
        ejecucion = EjecucionSonda(
            id=nueva_id(),
            sonda_id=sonda.id,
            propiedad_id=sonda.propiedad_id,
            region="default",
            iniciado_en=inicio,
        )

        try:
            if sonda.tipo in ("HTTP", "HTTPS"):
                await self._ejecutar_http(sonda, ejecucion)
            elif sonda.tipo == "TCP":
                await self._ejecutar_tcp(sonda, ejecucion)
            elif sonda.tipo == "DNS":
                await self._ejecutar_dns(sonda, ejecucion)
            elif sonda.tipo == "TLS":
                await self._ejecutar_tls(sonda, ejecucion)
        except Exception as e:
            ejecucion.exito = False
            ejecucion.error = str(e)
            ejecucion.error_tipo = type(e).__name__

        ejecucion.finalizado_en = ahora_utc()
        if ejecucion.latencia_ms is None and ejecucion.finalizado_en:
            ejecucion.latencia_ms = int((ejecucion.finalizado_en - ejecucion.iniciado_en).total_seconds() * 1000)

        await self.ejecuciones.add(ejecucion)
        return ejecucion

    async def _ejecutar_http(self, sonda: Sonda, ejecucion: EjecucionSonda) -> None:
        """Ejecuta sonda HTTP/HTTPS."""
        inicio_req = time.perf_counter()
        try:
            resp = await self.client.request(
                method=sonda.metodo,
                url=sonda.objetivo,
                headers=sonda.headers,
                content=sonda.cuerpo,
                timeout=sonda.timeout_segundos,
            )
            ejecucion.latencia_ms = int((time.perf_counter() - inicio_req) * 1000)
            ejecucion.status_code = resp.status_code
            ejecucion.respuesta_tamano = len(resp.content)
            ejecucion.respuesta_headers = dict(resp.headers)
            ejecucion.exito = (
                resp.status_code == sonda.esperado_status
                and (sonda.esperado_contiene is None or sonda.esperado_contiene in resp.text)
            )
            if not ejecucion.exito:
                ejecucion.error = f"Status {resp.status_code} != {sonda.esperado_status}"
                ejecucion.error_tipo = "HTTP_STATUS"
        except httpx.TimeoutException:
            ejecucion.exito = False
            ejecucion.error = "Timeout"
            ejecucion.error_tipo = "TIMEOUT"
        except httpx.ConnectError as e:
            ejecucion.exito = False
            ejecucion.error = str(e)
            ejecucion.error_tipo = "CONNECT_ERROR"
        except Exception as e:
            ejecucion.exito = False
            ejecucion.error = str(e)
            ejecucion.error_tipo = type(e).__name__

    async def _ejecutar_tcp(self, sonda: Sonda, ejecucion: EjecucionSonda) -> None:
        """Ejecuta sonda TCP."""
        parsed = urlparse(f"//{sonda.objetivo}")
        host = parsed.hostname or sonda.objetivo.split(":")[0]
        port = parsed.port or 80

        inicio_tcp = time.perf_counter()
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=sonda.timeout_segundos,
            )
            ejecucion.tcp_latencia_ms = int((time.perf_counter() - inicio_tcp) * 1000)
            ejecucion.tcp_conectado = True
            writer.close()
            await writer.wait_closed()
            ejecucion.exito = True
        except asyncio.TimeoutError:
            ejecucion.exito = False
            ejecucion.error = "TCP Timeout"
            ejecucion.error_tipo = "TIMEOUT"
        except Exception as e:
            ejecucion.exito = False
            ejecucion.error = str(e)
            ejecucion.error_tipo = type(e).__name__

    async def _ejecutar_dns(self, sonda: Sonda, ejecucion: EjecucionSonda) -> None:
        """Ejecuta sonda DNS."""
        host = sonda.objetivo
        inicio_dns = time.perf_counter()
        try:
            ips = await asyncio.get_event_loop().getaddrinfo(host, None)
            ejecucion.dns_latencia_ms = int((time.perf_counter() - inicio_dns) * 1000)
            ejecucion.dns_resuelto = True
            ejecucion.ips_resueltas = list(set(ip[4][0] for ip in ips))
            ejecucion.exito = True
        except Exception as e:
            ejecucion.exito = False
            ejecucion.error = str(e)
            ejecucion.error_tipo = type(e).__name__

    async def _ejecutar_tls(self, sonda: Sonda, ejecucion: EjecucionSonda) -> None:
        """Ejecuta sonda TLS (verifica certificado) en hilo separado para no bloquear event loop."""
        parsed = urlparse(f"//{sonda.objetivo}")
        host = parsed.hostname or sonda.objetivo.split(":")[0]
        port = parsed.port or 443

        def _tls_check_sync() -> tuple[bool, int, str | None, datetime | None, int | None, str | None, str | None]:
            inicio_tls = time.perf_counter()
            try:
                context = ssl.create_default_context()
                if not sonda.verificar_certificado:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE

                with socket.create_connection((host, port), timeout=sonda.timeout_segundos) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        latencia_ms = int((time.perf_counter() - inicio_tls) * 1000)
                        tls_version = ssock.version()
                        cert_exp = None
                        dias_rest = None

                        cert = ssock.getpeercert()
                        if cert:
                            exp_str = cert.get("notAfter")
                            if exp_str:
                                exp_ts = email.utils.parsedate_to_datetime(exp_str)
                                if exp_ts.tzinfo is None:
                                    exp_ts = exp_ts.replace(tzinfo=timezone.utc)
                                cert_exp = exp_ts
                                dias = (exp_ts - ahora_utc()).days
                                dias_rest = max(0, dias)

                        return True, latencia_ms, tls_version, cert_exp, dias_rest, None, None
            except ssl.SSLError as e:
                return False, int((time.perf_counter() - inicio_tls) * 1000), None, None, None, f"SSL Error: {e}", "SSL_ERROR"
            except Exception as e:
                return False, int((time.perf_counter() - inicio_tls) * 1000), None, None, None, str(e), type(e).__name__

        exito, lat, ver, cert_exp, dias_rest, err, err_tipo = await asyncio.to_thread(_tls_check_sync)
        ejecucion.exito = exito
        ejecucion.tls_latencia_ms = lat
        ejecucion.tls_establecido = exito
        ejecucion.tls_version = ver
        ejecucion.cert_expira_en = cert_exp
        ejecucion.cert_dias_restantes = dias_rest
        ejecucion.error = err
        ejecucion.error_tipo = err_tipo
