"""Lógica de negocio del contenido del sitio (landing + publicidad)."""
from __future__ import annotations

from typing import Optional

from .content import Ad, Landing
from .content_repository import ContentRepository
from .domain import uuid7, utcnow
from .errors import ApiError
from .schemas import AdCreate, LandingContent


class ContentService:
    def __init__(self, repo: ContentRepository) -> None:
        self.repo = repo

    # ------------------------------------------------------------- landing
    def get_public_landing(self) -> tuple[LandingContent, list[Ad]]:
        landing = self.repo.get_landing()
        raw: dict = {}
        if landing is not None:
            raw = landing.published if landing.published is not None else landing.draft
        content = LandingContent.model_validate(raw or {})
        ads = self.repo.list_ads(only_active=True)
        return content, ads

    def get_draft_landing(self) -> tuple[LandingContent, Optional[Landing]]:
        landing = self.repo.get_landing()
        raw = landing.draft if landing is not None else {}
        return LandingContent.model_validate(raw or {}), landing

    def save_landing(self, content: LandingContent) -> tuple[LandingContent, Landing]:
        landing = self.repo.save_landing_draft(content.model_dump(mode="json"))
        return content, landing

    def publish_landing(self) -> tuple[LandingContent, Landing]:
        landing = self.repo.publish_landing()
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
