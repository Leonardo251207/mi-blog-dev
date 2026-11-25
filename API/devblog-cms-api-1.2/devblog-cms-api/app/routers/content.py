"""Módulo de contenido del sitio: landing y publicidad.

La landing es el documento editable de la portada. Tiene borrador y versión
publicada: el sitio público solo ve la publicada, así el CMS puede preparar
cambios sin romper lo que ya está en línea.

La publicidad es una entidad independiente con diseño configurable (tema,
layout, imagen y CTA) y un interruptor `active`.
"""
from typing import Annotated

from fastapi import APIRouter, File, Path, Request, Response, UploadFile

from .. import schemas
from ..caching import cached_json
from ..content_repository import LANDING_ID
from ..dependencies import (ConsolePrincipal, ContentServiceDep, ReadPrincipal)
from ..domain import SLUG_PATTERN, UUID7_PATTERN, utcnow
from ..errors import ApiError

router = APIRouter(tags=["Contenido del sitio"])

_ERR = {"model": schemas.ErrorResponse}
_COMMON = {401: _ERR, 403: _ERR, 429: _ERR}
AdId = Annotated[str, Path(pattern=UUID7_PATTERN, description="UUIDv7 de la publicidad")]
SiteId = Annotated[str, Path(min_length=3, max_length=100, pattern=SLUG_PATTERN,
                             description="Slug del sitio")]
MediaId = Annotated[str, Path(min_length=10, max_length=64, description="ID del archivo")]
MAX_MEDIA_BYTES = 25 * 1024 * 1024
ALLOWED_MEDIA_TYPES = {
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
    "video/x-m4v",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


def _draft_out(content: schemas.LandingContent, landing) -> schemas.LandingDraftOut:
    return schemas.LandingDraftOut(
        content=content,
        updated_at=landing.updated_at if landing is not None else utcnow(),
        published_at=landing.published_at if landing is not None else None,
        has_published=bool(landing is not None and landing.published is not None),
    )


# ================================== MEDIA ===================================
@router.post("/media", status_code=201, response_model=schemas.MediaOut,
             summary="Subir video o imagen para una landing",
             responses={**_COMMON, 413: _ERR, 422: _ERR})
async def upload_media(request: Request, service: ContentServiceDep,
                       principal: ConsolePrincipal,
                       file: UploadFile = File(...)):
    content_type = (file.content_type or "").lower()
    if content_type in {"", "application/octet-stream"}:
        name = (file.filename or "").lower()
        content_type = next(
            (media for ext, media in {
                ".mp4": "video/mp4",
                ".webm": "video/webm",
                ".mov": "video/quicktime",
                ".m4v": "video/x-m4v",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
                ".gif": "image/gif",
            }.items() if name.endswith(ext)),
            content_type,
        )
    if content_type not in ALLOWED_MEDIA_TYPES:
        raise ApiError(422, "MEDIA_TYPE_NOT_ALLOWED",
                       "Solo se permiten videos MP4/WebM/MOV o imágenes JPG/PNG/WebP/GIF.",
                       field="file")
    data = await file.read(MAX_MEDIA_BYTES + 1)
    if len(data) > MAX_MEDIA_BYTES:
        raise ApiError(413, "MEDIA_TOO_LARGE", "El archivo supera el límite de 25 MB.",
                       field="file")
    if not data:
        raise ApiError(422, "MEDIA_EMPTY", "El archivo está vacío.", field="file")

    media_id = service.save_media(file.filename or "media", content_type, data)
    base = str(request.base_url).rstrip("/")
    if base.startswith("http://") and "127.0.0.1" not in base and "localhost" not in base:
        base = "https://" + base[len("http://"):]
    return schemas.MediaOut(
        media_id=media_id,
        url=f"{base}/api/v1/media/{media_id}",
        content_type=content_type,
        size=len(data),
        filename=file.filename or "media",
    )


@router.get("/media/{media_id}", summary="Servir un archivo multimedia",
            responses={404: _ERR, 416: _ERR})
def get_media(request: Request, media_id: MediaId, service: ContentServiceDep):
    result = service.get_media(media_id)
    if result is None:
        raise ApiError(404, "MEDIA_NOT_FOUND", "El archivo no existe.", field="media_id")
    filename, content_type, data = result
    safe_name = "".join(
        char for char in str(filename) if char.isascii() and char not in {'"', "\\"}
    ) or "media"
    headers = {
        "Cache-Control": "public, max-age=31536000, immutable",
        "Content-Disposition": f'inline; filename="{safe_name}"',
        "Accept-Ranges": "bytes",
    }

    range_header = request.headers.get("range", "")
    if range_header.lower().startswith("bytes="):
        try:
            start_raw, end_raw = range_header[6:].split("-", 1)
            start = int(start_raw) if start_raw else 0
            end = int(end_raw) if end_raw else len(data) - 1
            end = min(end, len(data) - 1)
            if start < 0 or start >= len(data) or end < start:
                raise ValueError
            chunk = data[start:end + 1]
            headers["Content-Range"] = f"bytes {start}-{end}/{len(data)}"
            headers["Content-Length"] = str(len(chunk))
            return Response(content=chunk, status_code=206,
                            media_type=content_type, headers=headers)
        except ValueError:
            raise ApiError(416, "MEDIA_RANGE_INVALID", "Rango de bytes inválido.",
                           field="Range")

    headers["Content-Length"] = str(len(data))
    return Response(content=data, media_type=content_type, headers=headers)


# ================================= SITIOS ===================================
@router.get("/sites", response_model=list[schemas.SiteOut],
            summary="Sitios públicos activos", responses={**_COMMON})
def list_public_sites(service: ContentServiceDep, principal: ReadPrincipal):
    return [
        schemas.SiteOut.from_site(site)
        for site in service.list_sites()
        if site.status == "active"
    ]


@router.get("/sites/admin", response_model=list[schemas.SiteOut],
            summary="Todos los sitios (consola)", responses={**_COMMON})
def list_admin_sites(service: ContentServiceDep, principal: ConsolePrincipal):
    return [schemas.SiteOut.from_site(site) for site in service.list_sites(include_archived=True)]


@router.post("/sites", status_code=201, response_model=schemas.SiteOut,
             summary="Crear sitio", responses={**_COMMON, 409: _ERR, 422: _ERR})
def create_site(data: schemas.SiteCreate, service: ContentServiceDep,
                principal: ConsolePrincipal):
    return schemas.SiteOut.from_site(service.create_site(data))


@router.get("/sites/{site_id}", response_model=schemas.SiteOut,
            summary="Sitio público", responses={**_COMMON, 404: _ERR})
def get_site(site_id: SiteId, service: ContentServiceDep, principal: ReadPrincipal):
    site = service.get_site(site_id)
    if site.status != "active":
        raise ApiError(404, "SITE_NOT_FOUND", "El sitio no está publicado.", field="site_id")
    return schemas.SiteOut.from_site(site)


@router.put("/sites/{site_id}", response_model=schemas.SiteOut,
            summary="Actualizar sitio", responses={**_COMMON, 404: _ERR, 422: _ERR})
def update_site(site_id: SiteId, data: schemas.SiteUpdate,
                service: ContentServiceDep, principal: ConsolePrincipal):
    return schemas.SiteOut.from_site(service.update_site(site_id, data))


@router.delete("/sites/{site_id}", status_code=204,
               summary="Eliminar sitio", responses={**_COMMON, 404: _ERR, 409: _ERR})
def delete_site(site_id: SiteId, service: ContentServiceDep,
                principal: ConsolePrincipal):
    service.delete_site(site_id)
    return Response(status_code=204)


@router.get("/sites/{site_id}/landing", response_model=schemas.PublicSiteLanding,
            response_model_exclude_none=True,
            summary="Landing publicada de un sitio",
            responses={**_COMMON, 404: _ERR, 304: {"description": "Not Modified"}})
def get_site_landing(request: Request, site_id: SiteId,
                     service: ContentServiceDep, principal: ReadPrincipal):
    site = service.get_site(site_id)
    if site.status != "active":
        raise ApiError(404, "SITE_NOT_FOUND", "El sitio no está publicado.", field="site_id")
    content, ads = service.get_public_landing(site_id)
    ads_out = [schemas.AdOut.from_ad(ad) for ad in ads]
    return cached_json(request, schemas.PublicSiteLanding(
        site=schemas.SiteOut.from_site(site),
        content=content,
        ads=ads_out,
        ad=ads_out[0] if ads_out else None,
    ))


@router.get("/sites/{site_id}/landing/draft", response_model=schemas.LandingDraftOut,
            summary="Borrador de la landing del sitio (consola)",
            responses={**_COMMON, 404: _ERR})
def get_site_landing_draft(site_id: SiteId, service: ContentServiceDep,
                           principal: ConsolePrincipal):
    service.get_site(site_id)
    content, landing = service.get_draft_landing(site_id)
    return _draft_out(content, landing)


@router.put("/sites/{site_id}/landing/draft", response_model=schemas.LandingDraftOut,
            summary="Guardar borrador de la landing del sitio",
            responses={**_COMMON, 404: _ERR, 422: _ERR})
def save_site_landing_draft(site_id: SiteId, data: schemas.LandingContent,
                            service: ContentServiceDep, principal: ConsolePrincipal):
    service.get_site(site_id)
    content, landing = service.save_landing(site_id, data)
    return _draft_out(content, landing)


@router.post("/sites/{site_id}/landing/publish", response_model=schemas.LandingDraftOut,
             summary="Publicar la landing del sitio",
             responses={**_COMMON, 404: _ERR})
def publish_site_landing(site_id: SiteId, service: ContentServiceDep,
                         principal: ConsolePrincipal):
    service.get_site(site_id)
    content, landing = service.publish_landing(site_id)
    return _draft_out(content, landing)


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
    content, landing = service.save_landing(LANDING_ID, data)
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
