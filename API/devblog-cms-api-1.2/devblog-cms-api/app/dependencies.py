"""Dependencias de FastAPI: autenticación por scopes, límite de tráfico e idempotencia.

Los dependencies de autenticación se crean UNA sola vez a nivel de módulo. Si
se llamara `require_scopes(...)` dentro de cada endpoint se crearían funciones
distintas y FastAPI no podría reutilizar el resultado: el límite de tráfico se
contaría dos veces por petición.
"""
from __future__ import annotations

import math
from typing import Annotated, Optional

from fastapi import Depends, Header, Path, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Principal, Settings
from .domain import UUID7_PATTERN
from .errors import ApiError
from .infra import IdempotencyStore
from .services import PostService

# auto_error=False: el contrato exige 401 (no el 403 que FastAPI usaría por defecto).
_bearer = HTTPBearer(auto_error=False, description="Token Bearer con el scope del consumidor.")


def require_scopes(*accepted: str):
    """Autentica (401), autoriza por scope (403) y aplica el límite de tráfico (429)."""
    def dependency(request: Request,
                   creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)]) -> Principal:
        principal = request.app.state.tokens.get(creds.credentials) if creds else None
        if principal is None:
            raise ApiError(401, "UNAUTHORIZED", "Token ausente o inválido.",
                           headers={"WWW-Authenticate": "Bearer"})
        if not principal.scopes & set(accepted):
            raise ApiError(403, "FORBIDDEN",
                           f"Scope insuficiente; se requiere alguno de: {', '.join(accepted)}.")
        wait = request.app.state.limiter.hit(principal.name, principal.rate_limit, principal.rate_window_s)
        if wait is not None:
            raise ApiError(429, "RATE_LIMITED", "Límite de peticiones excedido.",
                           headers={"Retry-After": str(max(1, math.ceil(wait)))})
        return principal
    return dependency


# Dependencies compartidos: una instancia por tipo de actor.
console_auth = require_scopes("cms:write")
posts_read_auth = require_scopes("cms:write", "posts:read")
posts_view_auth = require_scopes("posts:view")


def get_service(request: Request) -> PostService:
    return request.app.state.service


def get_idempotency(request: Request) -> IdempotencyStore:
    return request.app.state.idempotency


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def post_id_path(post_id: Annotated[str, Path(pattern=UUID7_PATTERN,
                                              description="UUIDv7 del Post")]) -> str:
    """Un post_id que no sea UUIDv7 responde 422 (Paso 5) antes de tocar la lógica."""
    return post_id.lower()


ServiceDep = Annotated[PostService, Depends(get_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
IdempotencyDep = Annotated[IdempotencyStore, Depends(get_idempotency)]
PostId = Annotated[str, Depends(post_id_path)]
IdempotencyKey = Annotated[str, Header(
    alias="Idempotency-Key", min_length=16, max_length=64, pattern=r"^[!-~]+$",
    description="16-64 caracteres ASCII; se recomienda UUID v4.")]

# Principals ya autenticados, reutilizables como parámetro de cada endpoint.
ConsolePrincipal = Annotated[Principal, Depends(console_auth)]
ReadPrincipal = Annotated[Principal, Depends(posts_read_auth)]
ViewPrincipal = Annotated[Principal, Depends(posts_view_auth)]
