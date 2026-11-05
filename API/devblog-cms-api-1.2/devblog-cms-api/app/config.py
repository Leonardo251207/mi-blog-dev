"""Configuración del servicio (Paso 5 - reglas transversales).

Todo lo que identifica a la instalación se puede cambiar por variables de
entorno o por un archivo `.env`. Así el mismo código sirve para el DevBlog o
para otro proyecto sin tocar la lógica de negocio.

Variables principales (ver `.env.example`):
    CMS_APP_NAME, CMS_ENV, CMS_DB_PATH
    CMS_CONSOLE_TOKEN, CMS_PUBLIC_TOKEN, CMS_CURSOR_SECRET
    CMS_CORS_ORIGINS, CMS_PUBLIC_SITE_URL, CMS_PUBLIC_ARTICLE_PATH
    CMS_IDEMPOTENCY_TTL_S

Los nombres antiguos `DEVBLOG_*` siguen funcionando como respaldo para no
romper instalaciones existentes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # python-dotenv es opcional: si no está, se usan solo las variables reales.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - depende del entorno de ejecución
    pass

DEFAULT_CONSOLE_TOKEN = "console-dev-token"
DEFAULT_PUBLIC_TOKEN = "public-dev-token"
DEFAULT_CURSOR_SECRET = "dev-cursor-secret-change-me"

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "null",  # páginas abiertas con file:// (el navegador envía Origin: null)
)


@dataclass(frozen=True)
class Principal:
    """Consumidor autenticado: quién es, qué scopes tiene y su límite de tráfico."""

    name: str
    scopes: frozenset[str]
    rate_limit: int        # peticiones permitidas...
    rate_window_s: float   # ...dentro de esta ventana (segundos)


def _env(*names: str, default: str | None = None) -> str | None:
    """Primera variable de entorno no vacía de la lista (permite alias antiguos)."""
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return default


def _env_int(*names: str, default: int) -> int:
    raw = _env(*names)
    return int(raw) if raw is not None else default


def _env_float(*names: str, default: float) -> float:
    raw = _env(*names)
    return float(raw) if raw is not None else default


def _env_list(*names: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = _env(*names)
    if raw is None:
        return default
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Configuración inmutable de una instalación de la API."""

    app_name: str = "DevBlog CMS API"
    app_description: str = (
        "API de Gestión de Contenido del DevBlog (Diseño API-First, v1.2). "
        "Módulos: Borradores (/drafts) y Publicaciones (/posts)."
    )
    app_version: str = "1.2.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    # Persistencia: archivo SQLite. Usa ":memory:" solo para pruebas.
    db_path: str = "data/devblog.db"

    # URL que se devuelve al publicar. Si public_site_url está vacío, es relativa.
    public_site_url: str = ""
    public_article_path: str = "/blog/{slug}"

    # CORS: orígenes permitidos separados por coma. "*" permite todos.
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS

    # Tokens de desarrollo. En producción se deben cambiar.
    console_token: str = DEFAULT_CONSOLE_TOKEN
    public_token: str = DEFAULT_PUBLIC_TOKEN

    # Límites de tráfico del contrato: Consola 60/min, Sitio público 10/s.
    console_rate_limit: int = 60
    console_rate_window_s: float = 60.0
    public_rate_limit: int = 10
    public_rate_window_s: float = 1.0

    idempotency_ttl_s: float = 24 * 60 * 60
    cursor_secret: str = DEFAULT_CURSOR_SECRET
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        if not self.api_prefix.startswith("/"):
            raise ValueError("CMS_API_PREFIX debe empezar con '/'")
        if not self.public_article_path.startswith(("/", "http://", "https://")):
            raise ValueError("CMS_PUBLIC_ARTICLE_PATH debe empezar con '/' o ser una URL absoluta")
        if "{slug}" not in self.public_article_path:
            raise ValueError("CMS_PUBLIC_ARTICLE_PATH debe contener el marcador {slug}")
        if not self.console_token or not self.public_token:
            raise ValueError("Los tokens de consola y público no pueden estar vacíos")
        if self.console_token == self.public_token:
            raise ValueError("CMS_CONSOLE_TOKEN y CMS_PUBLIC_TOKEN deben ser distintos")
        if not self.cursor_secret:
            raise ValueError("CMS_CURSOR_SECRET no puede estar vacío")

    @property
    def tokens(self) -> dict[str, Principal]:
        """Mapa token -> consumidor. Se recalcula para reflejar la configuración."""
        return {
            self.console_token: Principal(
                "consola-administracion",
                frozenset({"cms:write"}),
                self.console_rate_limit,
                self.console_rate_window_s,
            ),
            self.public_token: Principal(
                "sitio-web-publico",
                frozenset({"posts:read", "posts:view"}),
                self.public_rate_limit,
                self.public_rate_window_s,
            ),
        }

    @property
    def using_default_secrets(self) -> bool:
        return (
            self.console_token == DEFAULT_CONSOLE_TOKEN
            or self.public_token == DEFAULT_PUBLIC_TOKEN
            or self.cursor_secret == DEFAULT_CURSOR_SECRET
        )

    def article_url(self, slug: str) -> str:
        """Construye la URL pública del artículo según la configuración."""
        path = self.public_article_path.format(slug=slug)
        if path.startswith(("http://", "https://")):
            return path
        if self.public_site_url:
            return self.public_site_url.rstrip("/") + path
        return path


def load_settings() -> Settings:
    """Lee la configuración desde el entorno (y `.env` si existe)."""
    public_site_url = _env("CMS_PUBLIC_SITE_URL", "DEVBLOG_PUBLIC_SITE_URL", default="") or ""
    return Settings(
        app_name=_env("CMS_APP_NAME", "DEVBLOG_APP_NAME", default="DevBlog CMS API") or "DevBlog CMS API",
        app_description=_env(
            "CMS_APP_DESCRIPTION",
            "DEVBLOG_APP_DESCRIPTION",
            default=Settings.app_description,
        ) or Settings.app_description,
        app_version=_env("CMS_APP_VERSION", "DEVBLOG_APP_VERSION", default="1.2.0") or "1.2.0",
        environment=_env("CMS_ENV", "DEVBLOG_ENV", default="development") or "development",
        api_prefix=_env("CMS_API_PREFIX", "DEVBLOG_API_PREFIX", default="/api/v1") or "/api/v1",
        db_path=_env("CMS_DB_PATH", "DEVBLOG_DB_PATH", default="data/devblog.db") or "data/devblog.db",
        public_site_url=public_site_url,
        public_article_path=_env(
            "CMS_PUBLIC_ARTICLE_PATH",
            "DEVBLOG_PUBLIC_ARTICLE_PATH",
            default="/blog/{slug}",
        ) or "/blog/{slug}",
        cors_origins=_env_list(
            "CMS_CORS_ORIGINS",
            "DEVBLOG_CORS_ORIGINS",
            default=DEFAULT_CORS_ORIGINS,
        ),
        console_token=_env(
            "CMS_CONSOLE_TOKEN",
            "DEVBLOG_CONSOLE_TOKEN",
            default=DEFAULT_CONSOLE_TOKEN,
        ) or DEFAULT_CONSOLE_TOKEN,
        public_token=_env(
            "CMS_PUBLIC_TOKEN",
            "DEVBLOG_PUBLIC_TOKEN",
            default=DEFAULT_PUBLIC_TOKEN,
        ) or DEFAULT_PUBLIC_TOKEN,
        console_rate_limit=_env_int(
            "CMS_CONSOLE_RATE_LIMIT",
            "DEVBLOG_CONSOLE_RATE_LIMIT",
            default=60,
        ),
        console_rate_window_s=_env_float(
            "CMS_CONSOLE_RATE_WINDOW_S",
            "DEVBLOG_CONSOLE_RATE_WINDOW_S",
            default=60.0,
        ),
        public_rate_limit=_env_int(
            "CMS_PUBLIC_RATE_LIMIT",
            "DEVBLOG_PUBLIC_RATE_LIMIT",
            default=10,
        ),
        public_rate_window_s=_env_float(
            "CMS_PUBLIC_RATE_WINDOW_S",
            "DEVBLOG_PUBLIC_RATE_WINDOW_S",
            default=1.0,
        ),
        idempotency_ttl_s=_env_float(
            "CMS_IDEMPOTENCY_TTL_S",
            "DEVBLOG_IDEMPOTENCY_TTL_S",
            default=24 * 60 * 60,
        ),
        cursor_secret=_env(
            "CMS_CURSOR_SECRET",
            "DEVBLOG_CURSOR_SECRET",
            default=DEFAULT_CURSOR_SECRET,
        ) or DEFAULT_CURSOR_SECRET,
        log_level=_env("CMS_LOG_LEVEL", "DEVBLOG_LOG_LEVEL", default="INFO") or "INFO",
    )


def project_root() -> Path:
    """Raíz del proyecto (carpeta que contiene `app/`)."""
    return Path(__file__).resolve().parent.parent
