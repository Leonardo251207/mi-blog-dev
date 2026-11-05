"""Errores de negocio con código estable.

La misma excepción se traduce a JSON en REST y a `GraphQLError` en GraphQL, para que el
consumidor reciba siempre un código y no un texto que cambie con el tiempo.
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class NotFound(DomainError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, status_code=404)


class Unauthorized(DomainError):
    def __init__(self, message: str = "Falta autenticación") -> None:
        super().__init__("NO_AUTORIZADO", message, status_code=401)


class Forbidden(DomainError):
    def __init__(self, message: str = "No autorizado") -> None:
        super().__init__("NO_AUTORIZADO", message, status_code=403)
