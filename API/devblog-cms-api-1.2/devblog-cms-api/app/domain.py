"""Dominio: entidad Post, estados y utilidades puras (Pasos 2, 3 y 4).

Un "borrador" y una "publicación" NO son entidades distintas: son el mismo Post
con distinto `status` (glosario, Paso 2). Por eso hay un solo dataclass.
"""
import math
import re
import secrets
import threading
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

# --- Reglas del diccionario de datos (Paso 4) -------------------------------
SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
TAG_PATTERN = r"^[a-z0-9-]{2,30}$"
UUID7_PATTERN = (r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-7[0-9a-fA-F]{3}-"
                 r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
SLUG_RE = re.compile(SLUG_PATTERN)
TAG_RE = re.compile(TAG_PATTERN)

TITLE_MIN, TITLE_MAX = 5, 120
SLUG_MIN, SLUG_MAX = 3, 100
CONTENT_MIN, CONTENT_MAX = 1, 100_000
CONTENT_MIN_TO_PUBLISH = 100          # Invariante 4
MAX_TAGS = 5                          # Invariante 8
WORDS_PER_MINUTE = 200


class PostStatus(str, Enum):
    BORRADOR = "BORRADOR"
    PUBLICADO = "PUBLICADO"


@dataclass
class Post:
    post_id: str                       # !#@  UUIDv7 (Invariante 9)
    title: str                         # !
    slug: str                          # !    único global (Invariante 3)
    content: str                       # !
    tags: list[str]                    # ?
    status: PostStatus                 # !#
    created_at: datetime               # !#@
    updated_at: datetime               # !#
    published_at: datetime | None = None   # ?#@
    views_total: int = 0               # !#   (Invariante 5)


# --- Utilidades --------------------------------------------------------------
def utcnow() -> datetime:
    """Fecha UTC con precisión de segundos.

    El contrato usa ISO 8601 sin fracciones (ej. 2026-10-15T18:30:00Z). Guardar
    la misma precisión que se expone mantiene consistente el cursor de paginación.
    """
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


_uuid_lock = threading.Lock()
_last_ms = 0
_seq = 0


def uuid7() -> str:
    """Genera un UUIDv7 (48 bits de ms Unix + versión 7 + contador + aleatorio).

    Es monótono dentro del proceso: dos ids creados en el mismo milisegundo
    siguen ordenados, lo que sirve de desempate estable en la paginación.
    (Python 3.14 trae uuid.uuid7(); esta versión funciona desde 3.10.)
    """
    global _last_ms, _seq
    with _uuid_lock:
        ms = time.time_ns() // 1_000_000
        if ms > _last_ms:
            _seq = secrets.randbits(11)       # margen para incrementos
        else:
            ms = _last_ms
            _seq += 1
            if _seq > 0xFFF:                  # desbordó el contador de 12 bits
                ms += 1
                _seq = 0
        _last_ms = ms
        value = (ms << 80) | (0x7 << 76) | (_seq << 64) | (0b10 << 62) | secrets.randbits(62)
        return str(uuid.UUID(int=value))


def slugify(title: str) -> str:
    """minúsculas, sin acentos, espacios/símbolos a guiones (endpoint 1)."""
    ascii_text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:SLUG_MAX].strip("-")


def reading_time_min(content: str) -> int:
    """Atributo derivado `#`: ⌈palabras / 200⌉, mínimo 1. No se persiste."""
    return max(1, math.ceil(len(content.split()) / WORDS_PER_MINUTE))
