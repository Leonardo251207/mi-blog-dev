"""Identificadores, hashing y normalización de hosts, orígenes y rutas."""

from __future__ import annotations

import hashlib
import re
import secrets
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

UUID_RE = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(?=/|$)"
)
HEX_RE = re.compile(r"/[0-9a-fA-F]{16,}(?=/|$)")
NUM_RE = re.compile(r"/\d+(?=/|$)")
SLASH_RE = re.compile(r"/{2,}")


def nueva_id() -> str:
    return uuid.uuid4().hex


def generar_clave_publica(entorno: str = "live") -> str:
    return f"pk_{entorno}_{secrets.token_hex(24)}"


def hash_clave(clave: str) -> str:
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def hash_pseudonimo(valor: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{valor}".encode("utf-8")).hexdigest()


def normalizar_host(valor: str) -> str:
    valor = (valor or "").strip().lower()
    if "://" in valor:
        valor = urlsplit(valor).netloc
    return valor.rstrip(".")


def normalizar_origen(valor: str | None) -> str | None:
    if not valor:
        return None
    valor = valor.strip().lower().rstrip("/")
    if "://" not in valor:
        return valor
    partes = urlsplit(valor)
    return f"{partes.scheme}://{partes.netloc}".lower().rstrip("/")


def origen_de_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    try:
        partes = urlsplit(referer)
    except ValueError:
        return None
    if not partes.scheme or not partes.netloc:
        return None
    return f"{partes.scheme}://{partes.netloc}".lower()


def host_de_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    try:
        partes = urlsplit(referer)
    except ValueError:
        return None
    return normalizar_host(partes.netloc) or None


def normalizar_ruta(path: str | None) -> str:
    if not path:
        return "/"
    try:
        ruta = urlsplit(path).path or "/"
    except ValueError:
        ruta = path
    ruta = SLASH_RE.sub("/", ruta)
    ruta = UUID_RE.sub("/:uuid", ruta)
    ruta = HEX_RE.sub("/:id", ruta)
    ruta = NUM_RE.sub("/:id", ruta)
    if len(ruta) > 1 and ruta.endswith("/"):
        ruta = ruta[:-1]
    return ruta[:512] or "/"


def normalizar_referrer(referrer: str | None) -> str | None:
    if not referrer:
        return None
    return referrer.strip()[:2048] or None


def detectar_entorno(host: str) -> str:
    host = normalizar_host(host)
    if host in {"localhost", "127.0.0.1", "0.0.0.0", "[::1]"} or host.startswith(
        ("localhost:", "127.0.0.1:", "0.0.0.0:", "[::1]:")
    ):
        return "local"
    if host.endswith(".vercel.app") and (host.count(".") > 2 or "-git-" in host or "-preview-" in host):
        return "preview"
    return "production"


def dispositivo_desde_pantalla(pantalla: str | None) -> str:
    if not pantalla or "x" not in pantalla:
        return "desconocido"
    try:
        ancho = int(pantalla.lower().split("x", 1)[0])
    except (TypeError, ValueError):
        return "desconocido"
    if ancho < 768:
        return "movil"
    if ancho < 1024:
        return "tablet"
    return "escritorio"


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)
