"""Límites de tasa en memoria para la ingesta.

No sustituye a un limitador distribuido (Redis) en producción, pero evita que una clave
pública copiada inunde el colector en el primer corte de F1.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self, limite: int, ventana_segundos: int = 60) -> None:
        self.limite = max(1, limite)
        self.ventana = max(1, ventana_segundos)
        self._eventos: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def permitir(self, clave: str) -> bool:
        ahora = time.monotonic()
        async with self._lock:
            cola = self._eventos[clave]
            while cola and ahora - cola[0] > self.ventana:
                cola.popleft()
            if len(cola) >= self.limite:
                return False
            cola.append(ahora)
            if len(self._eventos) > 10_000:
                self._limpiar(ahora)
            return True

    def _limpiar(self, ahora: float) -> None:
        vacias = [
            clave
            for clave, cola in self._eventos.items()
            if not cola or ahora - cola[-1] > self.ventana
        ]
        for clave in vacias:
            self._eventos.pop(clave, None)
