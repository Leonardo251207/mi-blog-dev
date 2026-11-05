"""Módulo Borradores (Drafts): endpoints 1 a 6 del Paso 5.

Solo la Consola de Administración (scope `cms:write`). La autenticación se
declara como parámetro `ConsolePrincipal` en cada endpoint para que FastAPI
ejecute el dependency UNA vez (autenticación + scope + límite de tráfico).
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse

from .. import schemas
from ..dependencies import (
    ConsolePrincipal,
    IdempotencyDep,
    IdempotencyKey,
    PostId,
    ServiceDep,
    SettingsDep,
)
from ..infra import fingerprint

router = APIRouter(prefix="/drafts", tags=["Borradores (Drafts)"])

_ERR = {"model": schemas.ErrorResponse}
_COMMON = {401: _ERR, 403: _ERR, 429: _ERR}


@router.post("", status_code=201, response_model=schemas.DraftCreated,
             summary="1. Creación de Borrador",
             responses={**_COMMON, 409: _ERR, 422: _ERR})
def create_draft(request: Request, data: schemas.DraftCreate, key: IdempotencyKey,
                 service: ServiceDep, principal: ConsolePrincipal,
                 idem: IdempotencyDep, settings: SettingsDep):
    """Crea un Post en BORRADOR. Idempotency-Key (24 h). 409 si el slug ya existe."""
    def action():
        post = service.create_draft(data)
        return 201, schemas.DraftCreated.from_post(post).model_dump(mode="json")

    status, payload = idem.run(
        f"{principal.name}:{key}",
        fingerprint("POST", request.url.path, data.model_dump()),
        action,
    )
    location = f"{settings.api_prefix}/drafts/{payload['post_id']}"
    return JSONResponse(payload, status_code=status, headers={"Location": location})


@router.get("", response_model=schemas.DraftList, response_model_exclude_none=True,
            summary="2. Listado de Borradores", responses={**_COMMON, 422: _ERR})
def list_drafts(service: ServiceDep, principal: ConsolePrincipal,
                cursor: Annotated[Optional[str], Query(max_length=512)] = None,
                limit: Annotated[int, Query(ge=1, le=50)] = 20):
    """Solo BORRADORES, orden `updated_at` DESC (+ `post_id` como desempate)."""
    page = service.list_drafts(limit, cursor)
    return schemas.DraftList(items=[schemas.DraftListItem.from_post(p) for p in page.items],
                             next_cursor=page.next_cursor)


@router.get("/{post_id}", response_model=schemas.DraftDetail, summary="3. Obtención de un Borrador",
            responses={**_COMMON, 404: _ERR, 409: _ERR, 422: _ERR})
def get_draft(post_id: PostId, service: ServiceDep, principal: ConsolePrincipal):
    """404 si no existe; 409 si ya está PUBLICADO (se lee en /posts/{post_id})."""
    return schemas.DraftDetail.from_post(service.get_draft(post_id))


@router.put("/{post_id}", response_model=schemas.DraftUpdated, summary="4. Actualización de Borrador",
            responses={**_COMMON, 404: _ERR, 409: _ERR, 422: _ERR})
def update_draft(post_id: PostId, data: schemas.DraftUpdate, service: ServiceDep,
                 principal: ConsolePrincipal):
    """404 / 409 (PUBLICADO o slug de otro Post) / 422."""
    return schemas.DraftUpdated.from_post(service.update_draft(post_id, data))


@router.delete("/{post_id}", status_code=204, summary="5. Eliminación de Borrador",
               responses={**_COMMON, 404: _ERR, 409: _ERR, 422: _ERR})
def delete_draft(post_id: PostId, service: ServiceDep, principal: ConsolePrincipal):
    """Eliminación física. 409 si ya está PUBLICADO (usa DELETE /posts/{post_id})."""
    service.delete_draft(post_id)
    return Response(status_code=204)


@router.post("/{post_id}/publish", response_model=schemas.PublishResult,
             summary="6. Publicación de Borrador",
             responses={**_COMMON, 404: _ERR, 409: _ERR, 422: _ERR})
def publish_draft(request: Request, post_id: PostId, key: IdempotencyKey,
                  service: ServiceDep, principal: ConsolePrincipal,
                  idem: IdempotencyDep, settings: SettingsDep):
    """BORRADOR -> PUBLICADO (único punto que cambia `status`).

    Con la misma Idempotency-Key dentro de 24 h devuelve el resultado original
    en lugar de 409. Sin cuerpo: el id viaja en la ruta.
    """
    def action():
        post = service.publish(post_id)
        return 200, schemas.PublishResult.from_post(
            post, settings.article_url(post.slug)
        ).model_dump(mode="json")

    status, payload = idem.run(
        f"{principal.name}:{key}",
        fingerprint("POST", request.url.path),
        action,
    )
    return JSONResponse(payload, status_code=status)
