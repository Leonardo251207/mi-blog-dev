"""Modelos Pydantic: entradas y salidas del contrato (Pasos 4 y 5).

- `extra="forbid"` en las entradas: el cliente NUNCA puede enviar `post_id`,
  `status`, fechas ni `views_total` (modificadores `#`/`@`, Invariante 9).
- Las salidas serializan las fechas como ISO 8601 UTC con "Z".
"""
from datetime import datetime
from typing import Annotated, Optional

from pydantic import (BaseModel, ConfigDict, Field, PlainSerializer, StringConstraints,
                      field_validator)

from . import domain
from .domain import Post, PostStatus

UtcDatetime = Annotated[datetime, PlainSerializer(domain.iso, return_type=str, when_used="json")]

Title = Annotated[str, StringConstraints(strip_whitespace=True,
                                         min_length=domain.TITLE_MIN, max_length=domain.TITLE_MAX)]
Slug = Annotated[str, StringConstraints(min_length=domain.SLUG_MIN, max_length=domain.SLUG_MAX,
                                        pattern=domain.SLUG_PATTERN)]
Content = Annotated[str, StringConstraints(min_length=domain.CONTENT_MIN,
                                           max_length=domain.CONTENT_MAX)]
Tags = Annotated[list[str], Field(max_length=domain.MAX_TAGS)]


# ============================ ENTRADAS =======================================
class _DraftBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("title", check_fields=False)
    @classmethod
    def _title_single_line(cls, v: str) -> str:
        if "\n" in v or "\r" in v:
            raise ValueError("title no puede contener saltos de línea")
        return v

    @field_validator("content", check_fields=False)
    @classmethod
    def _content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content no puede estar vacío")
        return v

    @field_validator("tags", check_fields=False)
    @classmethod
    def _tags_rules(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        # Invariante 8: máx. 5 (en el tipo), sin duplicados, formato [a-z0-9-]{2,30}.
        if v is None:
            return v
        if len(set(v)) != len(v):
            raise ValueError("tags no puede contener elementos duplicados")
        for tag in v:
            if not domain.TAG_RE.fullmatch(tag):
                raise ValueError(f"tag inválido: '{tag}' (usa minúsculas, dígitos y guiones, 2-30 caracteres)")
        return v


class DraftCreate(_DraftBase):
    """Endpoint 1. title (!), content (!), slug (?), tags[] (?)"""
    title: Title
    content: Content
    slug: Optional[Slug] = None      # si se omite, se genera desde title
    tags: Optional[Tags] = None


class DraftUpdate(_DraftBase):
    """Endpoint 4. title (!), content (!), slug (?), tags[] (?) — si se omiten se conservan."""
    title: Title
    content: Content
    slug: Optional[Slug] = None
    tags: Optional[Tags] = None


# ============================ SALIDAS ========================================
class ErrorBody(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class DraftCreated(BaseModel):                       # 201 - endpoint 1
    post_id: str
    status: PostStatus
    title: str
    slug: str
    tags: list[str]
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @classmethod
    def from_post(cls, p: Post) -> "DraftCreated":
        return cls(post_id=p.post_id, status=p.status, title=p.title, slug=p.slug,
                   tags=p.tags, created_at=p.created_at, updated_at=p.updated_at)


class DraftListItem(BaseModel):                      # endpoint 2 (sin content)
    post_id: str
    title: str
    slug: str
    tags: list[str]
    updated_at: UtcDatetime

    @classmethod
    def from_post(cls, p: Post) -> "DraftListItem":
        return cls(post_id=p.post_id, title=p.title, slug=p.slug, tags=p.tags, updated_at=p.updated_at)


class DraftList(BaseModel):
    items: list[DraftListItem]
    next_cursor: Optional[str] = None                # se omite en la última página


class DraftDetail(BaseModel):                        # 200 - endpoint 3
    post_id: str
    title: str
    slug: str
    content: str
    tags: list[str]
    status: PostStatus
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @classmethod
    def from_post(cls, p: Post) -> "DraftDetail":
        return cls(post_id=p.post_id, title=p.title, slug=p.slug, content=p.content, tags=p.tags,
                   status=p.status, created_at=p.created_at, updated_at=p.updated_at)


class DraftUpdated(BaseModel):                       # 200 - endpoint 4
    post_id: str
    status: PostStatus
    title: str
    slug: str
    tags: list[str]
    updated_at: UtcDatetime

    @classmethod
    def from_post(cls, p: Post) -> "DraftUpdated":
        return cls(post_id=p.post_id, status=p.status, title=p.title, slug=p.slug,
                   tags=p.tags, updated_at=p.updated_at)


class PublishResult(BaseModel):                      # 200 - endpoint 6
    post_id: str
    status: PostStatus
    slug: str
    url: str
    published_at: UtcDatetime

    @classmethod
    def from_post(cls, p: Post, url: str) -> "PublishResult":
        return cls(post_id=p.post_id, status=p.status, slug=p.slug,
                   url=url, published_at=p.published_at)


class PostListItem(BaseModel):                       # endpoint 7 (sin content)
    post_id: str
    title: str
    slug: str
    tags: list[str]
    published_at: UtcDatetime
    reading_time_min: int

    @classmethod
    def from_post(cls, p: Post) -> "PostListItem":
        return cls(post_id=p.post_id, title=p.title, slug=p.slug, tags=p.tags,
                   published_at=p.published_at, reading_time_min=domain.reading_time_min(p.content))


class PostList(BaseModel):
    items: list[PostListItem]
    next_cursor: Optional[str] = None


class PostDetail(BaseModel):                         # endpoints 8 y 9
    post_id: str
    title: str
    slug: str
    content: str
    tags: list[str]
    status: PostStatus
    published_at: UtcDatetime
    reading_time_min: int

    @classmethod
    def from_post(cls, p: Post) -> "PostDetail":
        return cls(post_id=p.post_id, title=p.title, slug=p.slug, content=p.content, tags=p.tags,
                   status=p.status, published_at=p.published_at,
                   reading_time_min=domain.reading_time_min(p.content))


class PostMetrics(BaseModel):                        # endpoint 11
    post_id: str
    views_total: int
    reading_time_min: int
    published_at: UtcDatetime

    @classmethod
    def from_post(cls, p: Post) -> "PostMetrics":
        return cls(post_id=p.post_id, views_total=p.views_total,
                   reading_time_min=domain.reading_time_min(p.content), published_at=p.published_at)
