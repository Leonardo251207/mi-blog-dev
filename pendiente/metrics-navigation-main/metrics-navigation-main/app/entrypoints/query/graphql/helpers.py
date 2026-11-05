"""Traducción de errores de dominio y guardas de autorización."""

from __future__ import annotations

from typing import Awaitable, TypeVar

from graphql import GraphQLError
from strawberry.types import Info

from app.shared.errors import DomainError

T = TypeVar("T")


async def ejecutar(operacion: Awaitable[T]) -> T:
    try:
        return await operacion
    except DomainError as exc:
        raise GraphQLError(
            exc.message,
            extensions={"code": exc.code, "retryable": exc.retryable},
        ) from exc


def requerir_admin(info: Info) -> None:
    if not info.context.admin:
        raise GraphQLError(
            "Se requiere la cabecera X-Admin-Key.",
            extensions={"code": "NO_AUTORIZADO", "retryable": False},
        )
