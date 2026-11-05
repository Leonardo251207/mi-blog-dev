"""Punto de entrada: monta las puertas de consulta e ingesta."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter

from app.bootstrap.container import Container, build_container
from app.bootstrap.seed import seed_from_yaml
from app.bootstrap.settings import Settings, get_settings
from app.entrypoints.ingest.rest.routes import router as ingest_router
from app.entrypoints.query.rest.document_metrics import router as document_metrics_router
from app.entrypoints.query.graphql.context import Context
from app.entrypoints.query.graphql.schema import schema
from app.shared.errors import DomainError

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    container: Container | None = None,
) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal container
        if container is None:
            container = await build_container(settings)
            app.state.container = container
            if settings.bootstrap_on_start:
                for mensaje in await seed_from_yaml(container, settings):
                    logger.info(mensaje)
        yield
        if container is not None:
            await container.close()

    app = FastAPI(
        title="Metrics Collector & Retriever",
        version="0.1.0",
        description="API privada de observación de sitios.",
        lifespan=lifespan,
        docs_url="/docs" if settings.es_local else None,
        redoc_url="/redoc" if settings.es_local else None,
    )
    app.state.settings = settings
    if container is not None:
        app.state.container = container

    async def get_context(request: Request) -> Context:
        actual = getattr(request.app.state, "container", None)
        if actual is None:
            raise RuntimeError("El contenedor no está inicializado.")
        admin = not settings.admin_api_key or (
            request.headers.get("x-admin-key") == settings.admin_api_key
        )
        return Context(container=actual, admin=admin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.cors_origin_regex or None,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Admin-Key"],
        max_age=600,
    )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.to_dict()})

    @app.get("/health", tags=["ops"])
    async def health() -> dict:
        return {
            "status": "ok",
            "env": settings.app_env,
            "storage": settings.storage,
        }

    graphql_router = GraphQLRouter(
        schema,
        context_getter=get_context,
        graphql_ide="graphiql" if settings.es_local else None,
    )
    app.include_router(graphql_router, prefix="/v1/query")
    app.include_router(ingest_router, prefix="/v1")
    app.include_router(document_metrics_router, prefix="/api/v1")
    return app


app = create_app()
