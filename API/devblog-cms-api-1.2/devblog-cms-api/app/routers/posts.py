"""Módulo Publicaciones (Posts): endpoints 7 a 12 del Paso 5.

Lectura: Consola (cms:write) o Sitio Web Público (posts:read).
Vistas: solo el Sitio Web Público (posts:view).

Cada endpoint declara su `Principal` como parámetro para que la autenticación,
el scope y el límite de tráfico se ejecuten exactamente una vez.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Path, Query, Request, Response

from .. import schemas
from ..caching import cached_json
from ..dependencies import (
    ConsolePrincipal,
    PostId,
    ReadPrincipal,
    ServiceDep,
    ViewPrincipal,
)
from ..domain import SLUG_MAX, SLUG_MIN, SLUG_PATTERN, TAG_PATTERN

router = APIRouter(prefix="/posts", tags=["Publicaciones (Posts)"])

_ERR = {"model": schemas.ErrorResponse}
_COMMON = {401: _ERR, 403: _ERR, 429: _ERR}


@router.get("", response_model=schemas.PostList, response_model_exclude_none=True,
            summary="7. Listado de Publicaciones",
            responses={**_COMMON, 304: {"description": "Not Modified (If-None-Match coincide con el ETag)"}, 422: _ERR})
def list_posts(request: Request, service: ServiceDep, principal: ReadPrincipal,
               cursor: Annotated[Optional[str], Query(max_length=512)] = None,
               limit: Annotated[int, Query(ge=1, le=50)] = 20,
               tag: Annotated[Optional[str], Query(pattern=TAG_PATTERN)] = None):
    """Solo PUBLICADOS, orden `published_at` DESC (+ `post_id`). Sin `content`."""
    page = service.list_posts(limit, cursor, tag)
    return cached_json(request, schemas.PostList(
        items=[schemas.PostListItem.from_post(p) for p in page.items], next_cursor=page.next_cursor))


# IMPORTANTE: esta ruta se registra ANTES de /{post_id}/metrics y /{post_id}/views.
# Así GET /posts/slug/metrics se interpreta como "el artículo cuyo slug es 'metrics'"
# y no como "métricas del post_id 'slug'".
@router.get("/slug/{slug}", response_model=schemas.PostDetail, summary="9. Obtención de una Publicación por slug",
            responses={**_COMMON, 304: {"description": "Not Modified"}, 404: _ERR, 422: _ERR})
def get_post_by_slug(request: Request, service: ServiceDep, principal: ReadPrincipal,
                     slug: Annotated[str, Path(min_length=SLUG_MIN, max_length=SLUG_MAX,
                                               pattern=SLUG_PATTERN)]):
    """Artículo completo en UNA sola petición (incluye `post_id` para registrar la vista)."""
    return cached_json(request, schemas.PostDetail.from_post(service.get_post_by_slug(slug)))


@router.get("/{post_id}", response_model=schemas.PostDetail,
            summary="8. Obtención de una Publicación por identificador",
            responses={**_COMMON, 304: {"description": "Not Modified"}, 404: _ERR, 422: _ERR})
def get_post(request: Request, post_id: PostId, service: ServiceDep, principal: ReadPrincipal):
    """404 si no existe O si es un BORRADOR (no se revela que hay contenido sin publicar)."""
    return cached_json(request, schemas.PostDetail.from_post(service.get_post(post_id)))


@router.delete("/{post_id}", status_code=204, summary="10. Eliminación de Publicación",
               responses={**_COMMON, 404: _ERR, 409: _ERR, 422: _ERR})
def delete_post(post_id: PostId, service: ServiceDep, principal: ConsolePrincipal,
                confirm: Annotated[bool, Query(description="Debe ser true.")]):
    """Borrado físico e irreversible; exige `?confirm=true`."""
    service.delete_post(post_id, confirm)
    return Response(status_code=204)


@router.get("/{post_id}/metrics", response_model=schemas.PostMetrics,
            summary="11. Métricas de una Publicación",
            responses={**_COMMON, 404: _ERR, 409: _ERR, 422: _ERR})
def get_metrics(post_id: PostId, service: ServiceDep, principal: ConsolePrincipal):
    """409 si es BORRADOR: solo las publicaciones tienen métricas."""
    return schemas.PostMetrics.from_post(service.get_metrics(post_id))


@router.post("/{post_id}/views", status_code=204, summary="12. Registro de Vista",
             responses={**_COMMON, 404: _ERR, 422: _ERR})
def register_view(post_id: PostId, service: ServiceDep, principal: ViewPrincipal):
    """Incrementa `views_total` en 1. Sin Idempotency-Key: el conteo es aproximado."""
    service.register_view(post_id)
    return Response(status_code=204)
