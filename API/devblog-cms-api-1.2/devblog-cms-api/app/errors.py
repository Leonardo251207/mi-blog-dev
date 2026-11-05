"""Formato de error único del contrato (Paso 4, objeto `error`).

Toda respuesta de error tiene la forma:
    {"error": {"code": "SLUG_DUPLICATED", "message": "...", "field": "slug"}}
`field` es opcional. ApiError hereda de HTTPException, así que en el código
de negocio se levanta como cualquier HTTPException de FastAPI.

También se captura cualquier excepción no controlada para no filtrar trazas al
cliente y mantener el mismo formato en los 500.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("devblog.api")


class ApiError(StarletteHTTPException):
    def __init__(self, status_code: int, code: str, message: str,
                 field: str | None = None, headers: dict[str, str] | None = None):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.code = code
        self.field = field


def _body(code: str, message: str, field: str | None = None) -> dict:
    error = {"code": code, "message": message}
    if field:
        error["field"] = field
    return {"error": error}


_DEFAULT_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    406: "NOT_ACCEPTABLE",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT",
}


async def _http_error_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc, ApiError):
        code, field = exc.code, exc.field
    else:  # rutas inexistentes, método no permitido, etc.
        code, field = _DEFAULT_CODES.get(exc.status_code, "HTTP_ERROR"), None
    return JSONResponse(_body(code, str(exc.detail), field),
                        status_code=exc.status_code, headers=exc.headers)


async def _validation_error_handler(request: Request, exc: RequestValidationError):
    """Reemplaza el 422 por defecto de FastAPI por el objeto `error` del contrato."""
    first = exc.errors()[0]
    loc = [str(p) for p in first["loc"] if p not in ("body", "query", "path", "header")]
    message = first["msg"].removeprefix("Value error, ")
    return JSONResponse(_body("VALIDATION_ERROR", message, ".".join(loc) or None),
                        status_code=422)


async def _unhandled_error_handler(request: Request, exc: Exception):
    """Errores inesperados: se registran y el cliente recibe el formato del contrato."""
    logger.error(
        "Error no controlado en %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    headers: dict[str, str] = {"Cache-Control": "no-store"}
    # El handler de Exception vive fuera del middleware CORS; añadimos la
    # cabecera para que el navegador pueda leer el error en vez de reportar
    # un fallo de CORS.
    try:
        settings = request.app.state.settings
        origin = request.headers.get("origin")
        if origin and ("*" in settings.cors_origins or origin in settings.cors_origins):
            headers["Access-Control-Allow-Origin"] = (
                "*" if "*" in settings.cors_origins else origin
            )
            headers["Vary"] = "Origin"
    except Exception:  # pragma: no cover - la app siempre tiene settings
        pass
    return JSONResponse(
        _body("INTERNAL_ERROR", "Error interno del servidor."),
        status_code=500,
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
