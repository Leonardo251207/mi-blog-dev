from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class EngineType(str, Enum):
    ASTRO = "astro"
    HUGO = "hugo"
    QUARTO = "quarto"

class PageStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class BuildStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ArtifactStatus(str, Enum):
    HEALTHY = "HEALTHY"
    CORRUPTED = "CORRUPTED"
    MISSING = "MISSING"

@dataclass
class CanvasBlock:
    block_id: str
    block_type: str
    order_index: int
    content_payload: Dict[str, Any]
    style_config: Optional[Dict[str, Any]] = None

@dataclass
class SourceBundle:
    page_id: str
    engine: EngineType
    sources_path: str
    files: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

@dataclass
class Artifact:
    artifact_id: str
    page_id: str
    build_id: str
    file_path: str
    checksum_sha256: str
    size_bytes: int
    mime_type: str = "text/html"
    status: ArtifactStatus = ArtifactStatus.HEALTHY
    created_at: str = field(default_factory=utc_now_iso)

@dataclass
class BuildJob:
    build_id: str
    page_id: str
    engine: EngineType
    status: BuildStatus = BuildStatus.PENDING
    error_message: Optional[str] = None
    started_at: str = field(default_factory=utc_now_iso)
    completed_at: Optional[str] = None

@dataclass
class Page:
    page_id: str
    document_id: str
    slug: str
    content_type: str
    status: PageStatus
    build_id: Optional[str] = None
    output_url: Optional[str] = None
    source_snapshot: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
