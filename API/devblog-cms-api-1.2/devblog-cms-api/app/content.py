"""Entidades del contenido editable del sitio: landing y publicidad.

La landing se guarda como un documento JSON (borrador + publicado) porque el
CMS debe poder evolucionar su estructura sin migrar columnas. La publicidad sí
tiene campos estructurados porque su diseño se edita con un formulario.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Landing:
    landing_id: str
    draft: dict
    published: dict | None
    updated_at: datetime
    published_at: datetime | None = None


@dataclass
class Ad:
    ad_id: str
    title: str
    subtitle: str
    body: str
    cta_label: str
    cta_url: str
    image_url: str
    layout: str
    theme: dict = field(default_factory=dict)
    active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
