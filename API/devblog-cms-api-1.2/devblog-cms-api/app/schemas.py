"""Modelos Pydantic: entradas y salidas del contrato (Pasos 4 y 5).

- `extra="forbid"` en las entradas: el cliente NUNCA puede enviar `post_id`,
  `status`, fechas ni `views_total` (modificadores `#`/`@`, Invariante 9).
- Las salidas serializan las fechas como ISO 8601 UTC con "Z".
"""
from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import (BaseModel, ConfigDict, Field, PlainSerializer, StringConstraints,
                      field_validator)

from . import content_defaults, domain
from .content import Ad, Site
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


# ==================== CONTENIDO DE LA LANDING (CMS) ==========================
# Modelos anidados: el CMS edita la landing como un documento estructurado.
# `extra="ignore"` permite leer documentos guardados por versiones anteriores
# sin romper la página si algún día se retira un campo.
def _safe_url(value: str, *, allow_data_image: bool = False) -> str:
    value = (value or "").strip()
    if not value:
        return value
    lowered = value.lower()
    if lowered.startswith(("javascript:", "vbscript:")):
        raise ValueError("URL no permitida")
    if lowered.startswith("data:") and not (
        allow_data_image and lowered.startswith("data:image/")
    ):
        raise ValueError("URL no permitida")
    return value


class LandingHero(BaseModel):
    model_config = ConfigDict(extra="ignore")
    eyebrow: str = Field(default="Hola, mundo", max_length=80)
    first_name: str = Field(default="Leonardo", min_length=1, max_length=60)
    last_name: str = Field(default="Nucamendi Ruiz", min_length=1, max_length=80)
    role: str = Field(default="", max_length=180)
    location: str = Field(default="", max_length=80)
    tagline: str = Field(default="", max_length=240)
    cta_label: str = Field(default="Ver mis proyectos", max_length=60)
    cta_url: str = Field(default="#proyectos", max_length=500)
    note: str = Field(default="Creando desde · México", max_length=120)
    photo_url: str = Field(default="assets/perfil.jpg", max_length=500)

    @field_validator("cta_url")
    @classmethod
    def _cta_url(cls, v: str) -> str:
        return _safe_url(v)

    @field_validator("photo_url")
    @classmethod
    def _photo_url(cls, v: str) -> str:
        return _safe_url(v, allow_data_image=True)


class SectionHeading(BaseModel):
    model_config = ConfigDict(extra="ignore")
    label: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=160)


class LandingSections(BaseModel):
    model_config = ConfigDict(extra="ignore")
    technologies: SectionHeading = Field(default_factory=SectionHeading)
    projects: SectionHeading = Field(default_factory=SectionHeading)
    certifications: SectionHeading = Field(default_factory=SectionHeading)
    notes: SectionHeading = Field(default_factory=SectionHeading)
    videos: SectionHeading = Field(default_factory=SectionHeading)
    contact: SectionHeading = Field(default_factory=SectionHeading)


class TechnologyContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1, max_length=40)
    icon: str = Field(default="", max_length=8)
    color: str = Field(default="var(--green)", max_length=40)


class ProjectContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(min_length=1, max_length=120)
    badge: str = Field(default="", max_length=40)
    description: str = Field(default="", max_length=400)
    url: str = Field(default="", max_length=500)
    link_label: str = Field(default="", max_length=60)
    art: Literal["green", "dots", "purple"] = "dots"

    @field_validator("url")
    @classmethod
    def _url(cls, v: str) -> str:
        return _safe_url(v)


class CertificationContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    issuer: str = Field(default="", max_length=120)
    title: str = Field(min_length=1, max_length=160)
    url: str = Field(default="", max_length=500)
    tag: str = Field(default="", max_length=40)
    color: str = Field(default="var(--green)", max_length=40)

    @field_validator("url")
    @classmethod
    def _url(cls, v: str) -> str:
        return _safe_url(v)


class VideoContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=400)
    url: str = Field(min_length=1, max_length=1000)
    poster: str = Field(default="", max_length=1000)
    captions_url: str = Field(default="", max_length=1000)
    cta_label: str = Field(default="", max_length=60)
    cta_url: str = Field(default="", max_length=500)
    aspect: Literal["16:9", "9:16", "1:1"] = "16:9"

    @field_validator("url", "captions_url", "cta_url")
    @classmethod
    def _urls(cls, v: str) -> str:
        return _safe_url(v)

    @field_validator("poster")
    @classmethod
    def _poster(cls, v: str) -> str:
        return _safe_url(v, allow_data_image=True)


class LandingContact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kicker: str = Field(default="Construyamos algo juntos", max_length=120)
    title: str = Field(default="¿Tienes una idea?", max_length=160)
    accent: str = Field(default="Hablemos.", max_length=80)
    message: str = Field(default="", max_length=400)
    github: str = Field(default="", max_length=500)
    linkedin: str = Field(default="", max_length=500)
    email: str = Field(default="", max_length=160)
    footer: str = Field(default="", max_length=200)

    @field_validator("github", "linkedin")
    @classmethod
    def _urls(cls, v: str) -> str:
        return _safe_url(v)


def _default_technologies() -> list[TechnologyContent]:
    return [TechnologyContent(**item)
            for item in content_defaults.DEFAULT_LANDING_CONTENT["technologies"]]


def _default_projects() -> list[ProjectContent]:
    return [ProjectContent(**item)
            for item in content_defaults.DEFAULT_LANDING_CONTENT["projects"]]


def _default_certifications() -> list[CertificationContent]:
    return [CertificationContent(**item)
            for item in content_defaults.DEFAULT_LANDING_CONTENT["certifications"]]


def _default_sections() -> LandingSections:
    sections = content_defaults.DEFAULT_LANDING_CONTENT["sections"]
    return LandingSections(
        technologies=SectionHeading(**sections["technologies"]),
        projects=SectionHeading(**sections["projects"]),
        certifications=SectionHeading(**sections["certifications"]),
        notes=SectionHeading(**sections["notes"]),
        videos=SectionHeading(**sections.get("videos", {})),
        contact=SectionHeading(**sections["contact"]),
    )


def _default_hero() -> LandingHero:
    return LandingHero(**content_defaults.DEFAULT_LANDING_CONTENT["hero"])


def _default_contact() -> LandingContact:
    return LandingContact(**content_defaults.DEFAULT_LANDING_CONTENT["contact"])


class LandingContent(BaseModel):
    """Documento completo de la landing. La consola lo guarda como borrador."""
    model_config = ConfigDict(extra="ignore")
    hero: LandingHero = Field(default_factory=_default_hero)
    sections: LandingSections = Field(default_factory=_default_sections)
    technologies: list[TechnologyContent] = Field(
        default_factory=_default_technologies, max_length=12)
    projects: list[ProjectContent] = Field(
        default_factory=_default_projects, max_length=12)
    certifications: list[CertificationContent] = Field(
        default_factory=_default_certifications, max_length=12)
    videos: list[VideoContent] = Field(default_factory=list, max_length=12)
    contact: LandingContact = Field(default_factory=_default_contact)


class LandingDraftOut(BaseModel):
    content: LandingContent
    updated_at: UtcDatetime
    published_at: Optional[UtcDatetime] = None
    has_published: bool = False


# ============================== SITIOS ======================================
Color = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]


class SiteTheme(BaseModel):
    model_config = ConfigDict(extra="ignore")
    preset: str = Field(default="tech-terminal", max_length=40)
    accent: Color = "#3df0a8"
    background: Color = "#050807"
    surface: Color = "#0b1110"
    text: Color = "#eef5f1"
    muted: Color = "#8c9c95"
    heading_font: str = Field(default="Manrope", max_length=80)
    body_font: str = Field(default="Manrope", max_length=80)
    radius: int = Field(default=0, ge=0, le=32)


class SiteBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=100)
    kind: Literal["portfolio", "project", "blog", "client"] = "client"
    domain: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=300)
    status: Literal["active", "draft", "archived"] = "active"
    theme: SiteTheme = Field(default_factory=SiteTheme)


class SiteCreate(SiteBase):
    site_id: Slug


class SiteUpdate(SiteBase):
    pass


class SiteOut(SiteBase):
    site_id: str
    created_at: UtcDatetime | None = None
    updated_at: UtcDatetime | None = None

    @classmethod
    def from_site(cls, site: Site) -> "SiteOut":
        return cls(
            site_id=site.site_id,
            name=site.name,
            kind=site.kind,  # type: ignore[arg-type]
            domain=site.domain,
            description=site.description,
            status=site.status,  # type: ignore[arg-type]
            theme=SiteTheme(**site.theme),
            created_at=site.created_at,
            updated_at=site.updated_at,
        )


# ============================ PUBLICIDAD ====================================


class AdTheme(BaseModel):
    model_config = ConfigDict(extra="forbid")
    background: Color = "#0b1110"
    text: Color = "#eef5f1"
    accent: Color = "#3df0a8"


class AdBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3, max_length=120)
    subtitle: str = Field(default="", max_length=160)
    body: str = Field(default="", max_length=600)
    cta_label: str = Field(default="", max_length=60)
    cta_url: str = Field(default="", max_length=500)
    image_url: str = Field(default="", max_length=500)
    layout: Literal["banner", "tarjeta", "split"] = "banner"
    theme: AdTheme = Field(default_factory=AdTheme)
    active: bool = True

    @field_validator("cta_url")
    @classmethod
    def _cta_url(cls, v: str) -> str:
        return _safe_url(v)

    @field_validator("image_url")
    @classmethod
    def _image_url(cls, v: str) -> str:
        return _safe_url(v, allow_data_image=True)


class AdCreate(AdBase):
    pass


class AdUpdate(AdBase):
    pass


class AdOut(AdBase):
    ad_id: str
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @classmethod
    def from_ad(cls, ad: Ad) -> "AdOut":
        return cls(
            ad_id=ad.ad_id,
            title=ad.title,
            subtitle=ad.subtitle,
            body=ad.body,
            cta_label=ad.cta_label,
            cta_url=ad.cta_url,
            image_url=ad.image_url,
            layout=ad.layout,  # type: ignore[arg-type]
            theme=AdTheme(**ad.theme),
            active=ad.active,
            created_at=ad.created_at,
            updated_at=ad.updated_at,
        )


class PublicLanding(BaseModel):
    content: LandingContent
    ads: list[AdOut] = []
    ad: Optional[AdOut] = None


class PublicSiteLanding(BaseModel):
    site: SiteOut
    content: LandingContent
    ads: list[AdOut] = []
    ad: Optional[AdOut] = None


class MediaOut(BaseModel):
    media_id: str
    url: str
    content_type: str
    size: int
    filename: str


# ============================== MÉTRICAS ====================================
class MetricsRow(BaseModel):
    clave: str
    valor: int


class MetricsSeriesPoint(BaseModel):
    cubo: UtcDatetime
    pageviews: int
    sesiones: int


class MetricsOverview(BaseModel):
    disponible: bool
    sitio: str
    desde: UtcDatetime
    hasta: UtcDatetime
    grano: str
    pageviews: int = 0
    sesiones: int = 0
    visitantes_unicos: int = 0
    por_ruta: list[MetricsRow] = []
    por_host: list[MetricsRow] = []
    serie: list[MetricsSeriesPoint] = []
    error: Optional[str] = None
