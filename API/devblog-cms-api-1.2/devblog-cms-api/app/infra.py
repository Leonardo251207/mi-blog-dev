"""Piezas de infraestructura en memoria: límite de tráfico e idempotencia.

Ambas son de un solo proceso (suficiente para el avance). En producción se
moverían a Redis u otro almacén compartido.
"""
from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Optional

from .errors import ApiError


class RateLimiter:
    """Ventana deslizante por consumidor (Paso 5: 60/min Consola, 10/s Sitio público)."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_s: float) -> Optional[float]:
        """Registra una petición. Devuelve None si pasa, o los segundos de espera si excede."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] >= window_s:
                q.popleft()
            if len(q) >= limit:
                return window_s - (now - q[0])
            q.append(now)
            return None


@dataclass
class _Entry:
    fingerprint: str
    status: int
    payload: dict
    expires_at: float


def fingerprint(method: str, path: str, body: Optional[dict] = None) -> str:
    return json.dumps({"m": method, "p": path, "b": body}, sort_keys=True, default=str)


class IdempotencyStore:
    """`Idempotency-Key` (Paso 5, reglas transversales).

    - Misma clave + misma petición dentro de la ventana -> devuelve el resultado
      ORIGINAL sin volver a ejecutar la operación.
    - Misma clave + petición distinta (otro cuerpo o ruta) -> 422
      IDEMPOTENCY_KEY_REUSED.
    - Solo se guardan resultados exitosos (2xx); un error se reevalúa en cada
      intento.
    - El lock es POR CLAVE: dos peticiones con claves distintas no se bloquean
      entre sí mientras una operación lenta está en curso.
    """

    def __init__(self, ttl_s: float) -> None:
        self._ttl = ttl_s
        self._entries: dict[str, _Entry] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._lock = threading.Lock()

    def _cleanup(self, now: float) -> None:
        expired = [key for key, entry in self._entries.items() if entry.expires_at <= now]
        for key in expired:
            self._entries.pop(key, None)
            # Si otro hilo está usando la clave, conservamos su lock.
            lock = self._locks.get(key)
            if lock is not None and not lock.locked():
                self._locks.pop(key, None)

    def run(self, key: str, fp: str, action: Callable[[], tuple[int, dict]]) -> tuple[int, dict]:
        with self._lock:
            key_lock = self._locks.setdefault(key, threading.Lock())

        with key_lock:      # solo serializa reintentos de la MISMA clave
            now = time.monotonic()
            with self._lock:
                self._cleanup(now)
                entry = self._entries.get(key)
                if entry is not None:
                    if entry.fingerprint != fp:
                        raise ApiError(422, "IDEMPOTENCY_KEY_REUSED",
                                       "La Idempotency-Key ya se usó con una petición distinta.",
                                       field="Idempotency-Key")
                    return entry.status, entry.payload

            # La operación se ejecuta fuera del lock global; otras claves siguen.
            status, payload = action()

            with self._lock:
                self._entries[key] = _Entry(fp, status, payload, time.monotonic() + self._ttl)
            return status, payload
