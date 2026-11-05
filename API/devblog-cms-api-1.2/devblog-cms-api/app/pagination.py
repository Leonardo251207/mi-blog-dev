"""Cursor opaco y firmado de paginación (Paso 4, "Estructura del cursor").

El cursor tiene dos partes separadas por un punto:

    <payload_base64url>.<firma_base64url>

`payload` es el JSON compacto documentado en la especificación:

    publicaciones: {"id": "<uuid>", "published_at": "2026-10-15T18:30:00Z"}
    borradores:    {"id": "<uuid>", "updated_at":   "2026-10-16T09:12:40Z"}

La firma es un HMAC-SHA256 con `CMS_CURSOR_SECRET`. Así un cursor alterado no
puede aceptarse solo porque "parezca" JSON válido: la especificación exige 422
para cursores mal formados, alterados o de otro listado. El cliente lo trata
como una cadena opaca; la parte decodificable sigue siendo exactamente el JSON
documentado.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
from datetime import datetime

from .domain import UUID7_PATTERN, iso, parse_iso
from .errors import ApiError

_UUID7_RE = re.compile(UUID7_PATTERN)
_SEPARATOR = "."


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode())


def _sign(payload_b64: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return _b64encode(digest)


def encode_cursor(post_id: str, key: str, ts: datetime, secret: str) -> str:
    """Codifica el par (timestamp, id) y lo firma para que no pueda alterarse."""
    raw = json.dumps({"id": post_id, key: iso(ts)}, separators=(",", ":")).encode()
    payload_b64 = _b64encode(raw)
    return f"{payload_b64}{_SEPARATOR}{_sign(payload_b64, secret)}"


def decode_cursor(cursor: str, key: str, secret: str) -> tuple[datetime, str]:
    """Verifica la firma y devuelve (timestamp, id).

    `key` es "updated_at" o "published_at". Cualquier cursor inválido, alterado
    o perteneciente a otro listado responde 422 INVALID_CURSOR.
    """
    try:
        payload_b64, signature = cursor.split(_SEPARATOR, 1)
        if not payload_b64 or not signature:
            raise ValueError("cursor incompleto")

        expected = _sign(payload_b64, secret)
        if not hmac.compare_digest(signature, expected):
            raise ValueError("firma inválida")

        data = json.loads(_b64decode(payload_b64))
        if not isinstance(data, dict) or set(data) != {"id", key}:
            raise ValueError("estructura inesperada")
        if not isinstance(data["id"], str) or not _UUID7_RE.fullmatch(data["id"]):
            raise ValueError("id inválido")
        return parse_iso(data[key]), data["id"].lower()
    except (binascii.Error, ValueError, TypeError, UnicodeDecodeError, KeyError):
        raise ApiError(422, "INVALID_CURSOR", "El cursor es inválido o pertenece a otro listado.",
                       field="cursor")
