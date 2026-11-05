"""DevBlog CMS API (`devblog-cms-api`) v1.2 — punto de entrada.

Arranque:  uvicorn app.main:app --reload
Docs:      http://127.0.0.1:8000/docs
Salud:     http://127.0.0.1:8000/health
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, load_settings
from .errors import register_error_handlers
from .infra import IdempotencyStore, RateLimiter
from .repository import PostRepository
from .routers import drafts, health, posts
from .services import PostService
from .sqlite_repository import SqlitePostRepository

logger = logging.getLogger("devblog.api")


def create_app(settings: Settings | None = None,
               repository: PostRepository | None = None) -> FastAPI:
    """Crea una instancia de la API.

    `settings` y `repository` son inyectables para las pruebas: cada test puede
    usar una base SQLite en memoria y tokens propios sin tocar el entorno.
    """
    settings = settings or load_settings()
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    repo = repository or SqlitePostRepository(settings.db_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Iniciando %s v%s (entorno=%s)",
                    settings.app_name, settings.app_version, settings.environment)
        if settings.environment.lower() == "production" and settings.using_default_secrets:
            logger.warning(
                "Estás en producción con tokens o secreto de cursor por defecto. "
                "Configura CMS_CONSOLE_TOKEN, CMS_PUBLIC_TOKEN y CMS_CURSOR_SECRET."
            )
        try:
            yield
        finally:
            repo.close()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        lifespan=lifespan,
    )

    # Estado por aplicación: facilita las pruebas (cada test crea su propia app limpia).
    app.state.settings = settings
    app.state.repository = repo
    app.state.tokens = settings.tokens
    app.state.limiter = RateLimiter()
    app.state.idempotency = IdempotencyStore(settings.idempotency_ttl_s)
    # Para usar otra base de datos, cambia SOLO el repositorio que se pasa aquí.
    app.state.service = PostService(repo, settings.cursor_secret)

    register_error_handlers(app)

    @app.middleware("http")
    async def default_no_store(request: Request, call_next):
        """Regla de caché (v1.2): todo lo que no declare su propia política es `no-store`.

        Solo las lecturas públicas (endpoints 7, 8 y 9) fijan Cache-Control por su cuenta.
        """
        response = await call_next(request)
        if "cache-control" not in response.headers:
            response.headers["Cache-Control"] = "no-store"
        return response

    # CORS se añade al final para que envuelva al resto de middleware y aplique
    # también a las respuestas de error. El frontend está en otro origen.
    allow_origins = ["*"] if "*" in settings.cors_origins else list(settings.cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["ETag", "Retry-After", "Location", "Cache-Control"],
        max_age=600,
    )

    app.include_router(health.router)
    app.include_router(drafts.router, prefix=settings.api_prefix)
    app.include_router(posts.router, prefix=settings.api_prefix)
    return app


app = create_app()
