"""Lógica de negocio del contenido del sitio (landing + publicidad)."""
from __future__ import annotations

from typing import Optional

from .content import Ad, Landing, Site
from .content_defaults import landing_default_for
from .content_repository import ContentRepository, LANDING_ID
from .domain import uuid7, utcnow
from .errors import ApiError
from .schemas import AdCreate, LandingContent, SiteCreate, SiteUpdate

PROTECTED_SITES = {"portfolio", "devblog"}


class ContentService:
    def __init__(self, repo: ContentRepository) -> None:
        self.repo = repo

    # ------------------------------------------------------------- sitios
    def list_sites(self, include_archived: bool = False) -> list[Site]:
        sites = self.repo.list_sites()
        if include_archived:
            return sites
        return [site for site in sites if site.status != "archived"]

    def get_site(self, site_id: str) -> Site:
        site = self.repo.get_site(site_id)
        if site is None:
            raise ApiError(404, "SITE_NOT_FOUND", "El sitio no existe.", field="site_id")
        return site

    def create_site(self, data: SiteCreate) -> Site:
        if self.repo.get_site(data.site_id) is not None:
            raise ApiError(409, "SITE_DUPLICATED", "Ya existe un sitio con ese identificador.",
                           field="site_id")
        now = utcnow()
        site = Site(
            site_id=data.site_id,
            name=data.name,
            kind=data.kind,
            domain=data.domain,
            description=data.description,
            status=data.status,
            theme=data.theme.model_dump(),
            created_at=now,
            updated_at=now,
        )
        self.repo.upsert_site(site)
        content = landing_default_for(site.site_id, site.kind)
        self.repo.save_landing_draft(site.site_id, content)
        self.repo.publish_landing(site.site_id)
        return site

    def update_site(self, site_id: str, data: SiteUpdate) -> Site:
        current = self.get_site(site_id)
        updated = Site(
            site_id=current.site_id,
            name=data.name,
            kind=data.kind,
            domain=data.domain,
            description=data.description,
            status=data.status,
            theme=data.theme.model_dump(),
            created_at=current.created_at,
            updated_at=utcnow(),
        )
        self.repo.upsert_site(updated)
        return updated

    def delete_site(self, site_id: str) -> None:
        if site_id in PROTECTED_SITES:
            raise ApiError(409, "SITE_PROTECTED",
                           "Este sitio es parte del ecosistema base y no se puede eliminar.",
                           field="site_id")
        if not self.repo.delete_site(site_id):
            raise ApiError(404, "SITE_NOT_FOUND", "El sitio no existe.", field="site_id")

    # -------------------------------------------------------------- media
    def save_media(self, filename: str, content_type: str, data: bytes) -> str:
        return self.repo.save_media(filename, content_type, data)

    def get_media(self, media_id: str) -> Optional[tuple[str, str, bytes]]:
        return self.repo.get_media(media_id)

    # ------------------------------------------------------------- landing
    def get_public_landing(self, site_id: str = LANDING_ID) -> tuple[LandingContent, list[Ad]]:
        landing = self.repo.get_landing(site_id)
        raw: dict = {}
        if landing is not None:
            raw = landing.published if landing.published is not None else landing.draft
        content = LandingContent.model_validate(raw or {})
        ads = self.repo.list_ads(only_active=True)
        return content, ads

    def get_draft_landing(self, site_id: str = LANDING_ID) -> tuple[LandingContent, Optional[Landing]]:
        landing = self.repo.get_landing(site_id)
        raw = landing.draft if landing is not None else {}
        return LandingContent.model_validate(raw or {}), landing

    def save_landing(self, site_id: str, content: LandingContent) -> tuple[LandingContent, Landing]:
        landing = self.repo.save_landing_draft(site_id, content.model_dump(mode="json"))
        return content, landing

    def publish_landing(self, site_id: str = LANDING_ID) -> tuple[LandingContent, Landing]:
        landing = self.repo.publish_landing(site_id)
        if landing is None:
            raise ApiError(404, "LANDING_NOT_FOUND", "La landing no tiene contenido para publicar.")
        content = LandingContent.model_validate(landing.published or landing.draft)
        return content, landing

    # ---------------------------------------------------------------- ads
    def list_ads(self, only_active: bool = False) -> list[Ad]:
        return self.repo.list_ads(only_active=only_active)

    def get_public_ad(self, ad_id: str) -> Ad:
        ad = self.repo.get_ad(ad_id)
        if ad is None or not ad.active:
            raise ApiError(404, "AD_NOT_FOUND", "La publicidad no existe o está inactiva.", field="ad_id")
        return ad

    def get_ad(self, ad_id: str) -> Ad:
        ad = self.repo.get_ad(ad_id)
        if ad is None:
            raise ApiError(404, "AD_NOT_FOUND", "La publicidad no existe.", field="ad_id")
        return ad

    def create_ad(self, data: AdCreate) -> Ad:
        now = utcnow()
        ad = Ad(
            ad_id=uuid7(),
            title=data.title,
            subtitle=data.subtitle,
            body=data.body,
            cta_label=data.cta_label,
            cta_url=data.cta_url,
            image_url=data.image_url,
            layout=data.layout,
            theme=data.theme.model_dump(),
            active=data.active,
            created_at=now,
            updated_at=now,
        )
        self.repo.upsert_ad(ad)
        return ad

    def update_ad(self, ad_id: str, data: AdCreate) -> Ad:
        current = self.get_ad(ad_id)
        updated = Ad(
            ad_id=current.ad_id,
            title=data.title,
            subtitle=data.subtitle,
            body=data.body,
            cta_label=data.cta_label,
            cta_url=data.cta_url,
            image_url=data.image_url,
            layout=data.layout,
            theme=data.theme.model_dump(),
            active=data.active,
            created_at=current.created_at,
            updated_at=utcnow(),
        )
        self.repo.upsert_ad(updated)
        return updated

    def delete_ad(self, ad_id: str) -> None:
        if not self.repo.delete_ad(ad_id):
            raise ApiError(404, "AD_NOT_FOUND", "La publicidad no existe.", field="ad_id")
