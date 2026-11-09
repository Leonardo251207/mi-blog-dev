"""Endpoint de salud para saber si la API y la base de datos responden.

No requiere token: no expone contenido, solo el estado del servicio. Es útil
para el frontend, para el hosting y para comprobar la conexión antes de abrir
la consola CMS.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Salud"])


@router.get("/health", summary="Estado del servicio")
def health(request: Request):
    settings = request.app.state.settings
    repo = request.app.state.repository
    content_repo = request.app.state.content_repository
    ok = repo.ping() and content_repo.ping()
    return JSONResponse(
        {
            "status": "ok" if ok else "degraded",
            "service": settings.app_name,
            "version": settings.app_version,
            "database": "ok" if ok else "error",
            "content": "ok" if content_repo.ping() else "error",
            "environment": settings.environment,
        },
        status_code=200 if ok else 503,
    )
