"""Caché HTTP de las lecturas públicas (v1.2, Paso 5 - reglas transversales).

  - Endpoints 7, 8 y 9: `Cache-Control: public, max-age=60` + `ETag` (hash del cuerpo).
    Si llega `If-None-Match` con el ETag vigente se responde `304 Not Modified` sin cuerpo.
  - TODO lo demás (borradores, métricas, vistas, errores): `Cache-Control: no-store`
    (lo aplica el middleware de `create_app`).

Por qué es seguro cachear: una publicación es inmutable (Invariante 2), así que el
cuerpo solo cambia al publicar o eliminar. Contrapartida aceptada: una publicación
eliminada puede seguir sirviéndose desde caché hasta `max-age` segundos.
"""
import hashlib

from fastapi import Request, Response
from pydantic import BaseModel

PUBLIC_MAX_AGE_S = 60


def _etag_matches(header: str, etag: str) -> bool:
    for candidate in header.split(","):
        candidate = candidate.strip()
        if candidate == "*":
            return True
        if candidate.removeprefix("W/") == etag:   # comparación débil, como indica HTTP para GET
            return True
    return False


def cached_json(request: Request, model: BaseModel) -> Response:
    body = model.model_dump_json(exclude_none=True).encode()
    etag = '"' + hashlib.sha256(body).hexdigest()[:32] + '"'
    headers = {"ETag": etag, "Cache-Control": f"public, max-age={PUBLIC_MAX_AGE_S}"}
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and _etag_matches(if_none_match, etag):
        return Response(status_code=304, headers=headers)         # sin cuerpo
    return Response(content=body, media_type="application/json", headers=headers)
