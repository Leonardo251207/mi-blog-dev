"""Módulo de contenido del sitio: landing y publicidad.

La landing es el documento editable de la portada. Tiene borrador y versión
publicada: el sitio público solo ve la publicada, así el CMS puede preparar
cambios sin romper lo que ya está en línea.

La publicidad es una entidad independiente con diseño configurable (tema,
layout, imagen y CTA) y un interruptor `active`.
"""
from typing import Annotated

from fastapi import APIRouter, Path, Request, Response

from .. import schemas
from ..caching import cached_json
from ..dependencies import (ConsolePrincipal, ContentServiceDep, ReadPrincipal)
from ..domain import UUID7_PATTERN, utcnow

router = APIRouter(tags=["Contenido del sitio"])

_ERR = {"model": schemas.ErrorResponse}
_COMMON = {401: _ERR, 403: _ERR, 429: _ERR}
AdId = Annotated[str, Path(pattern=UUID7_PATTERN, description="UUIDv7 de la publicidad")]


def _draft_out(content: schemas.LandingContent, landing) -> schemas.LandingDraftOut:
    return schemas.LandingDraftOut(
        content=content,
        updated_at=landing.updated_at if landing is not None else utcnow(),
        published_at=landing.published_at if landing is not None else None,
        has_published=bool(landing is not None and landing.published is not None),
    )


# ================================ LANDING ===================================
@router.get("/landing", response_model=schemas.PublicLanding,
            response_model_exclude_none=True,
            summary="Landing publicada + publicidad activa",
            responses={**_COMMON, 304: {"description": "Not Modified"}})
def get_landing(request: Request, service: ContentServiceDep, principal: ReadPrincipal):
    """Contenido que consume el sitio público. Si no hay publicación, usa el borrador."""
    content, ads = service.get_public_landing()
    ads_out = [schemas.AdOut.from_ad(ad) for ad in ads]
    return cached_json(request, schemas.PublicLanding(
        content=content,
        ads=ads_out,
        ad=ads_out[0] if ads_out else None,
    ))


@router.get("/landing/draft", response_model=schemas.LandingDraftOut,
            summary="Borrador de la landing (consola)",
            responses={**_COMMON})
def get_landing_draft(service: ContentServiceDep, principal: ConsolePrincipal):
    content, landing = service.get_draft_landing()
    return _draft_out(content, landing)


@router.put("/landing/draft", response_model=schemas.LandingDraftOut,
            summary="Guardar borrador de la landing",
            responses={**_COMMON, 422: _ERR})
def save_landing_draft(data: schemas.LandingContent,
                       service: ContentServiceDep, principal: ConsolePrincipal):
    content, landing = service.save_landing(data)
    return _draft_out(content, landing)


@router.post("/landing/publish", response_model=schemas.LandingDraftOut,
             summary="Publicar la landing",
             responses={**_COMMON, 404: _ERR})
def publish_landing(service: ContentServiceDep, principal: ConsolePrincipal):
    content, landing = service.publish_landing()
    return _draft_out(content, landing)


# =============================== PUBLICIDAD =================================
@router.get("/ads", response_model=list[schemas.AdOut],
            summary="Publicidad activa (sitio público)", responses={**_COMMON})
def list_public_ads(service: ContentServiceDep, principal: ReadPrincipal):
    return [schemas.AdOut.from_ad(ad) for ad in service.list_ads(only_active=True)]


@router.get("/ads/admin", response_model=list[schemas.AdOut],
            summary="Todas las publicidades (consola)", responses={**_COMMON})
def list_all_ads(service: ContentServiceDep, principal: ConsolePrincipal):
    return [schemas.AdOut.from_ad(ad) for ad in service.list_ads(only_active=False)]


@router.post("/ads", status_code=201, response_model=schemas.AdOut,
             summary="Crear publicidad", responses={**_COMMON, 422: _ERR})
def create_ad(data: schemas.AdCreate, service: ContentServiceDep,
              principal: ConsolePrincipal):
    return schemas.AdOut.from_ad(service.create_ad(data))


@router.get("/ads/{ad_id}", response_model=schemas.AdOut,
            summary="Publicidad activa por id", responses={**_COMMON, 404: _ERR, 422: _ERR})
def get_public_ad(ad_id: AdId, service: ContentServiceDep, principal: ReadPrincipal):
    return schemas.AdOut.from_ad(service.get_public_ad(ad_id))


@router.put("/ads/{ad_id}", response_model=schemas.AdOut,
            summary="Actualizar publicidad y su diseño",
            responses={**_COMMON, 404: _ERR, 422: _ERR})
def update_ad(ad_id: AdId, data: schemas.AdUpdate, service: ContentServiceDep,
              principal: ConsolePrincipal):
    return schemas.AdOut.from_ad(service.update_ad(ad_id, data))


@router.delete("/ads/{ad_id}", status_code=204,
               summary="Eliminar publicidad",
               responses={**_COMMON, 404: _ERR, 422: _ERR})
def delete_ad(ad_id: AdId, service: ContentServiceDep, principal: ConsolePrincipal):
    service.delete_ad(ad_id)
    return Response(status_code=204)
