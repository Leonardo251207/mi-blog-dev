from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CanvasBlockSchema(BaseModel):
    block_id: Optional[str] = None
    block_type: str
    order_index: int = 0
    content_payload: Dict[str, Any]
    style_config: Optional[Dict[str, Any]] = None

class PageCreationPayload(BaseModel):
    page_id: Optional[str] = None
    document_id: str
    slug: str
    content_type: str = "DEV_BLOG"
    frozen_template: Dict[str, Any] = Field(default_factory=dict)
    canvas_blocks: List[CanvasBlockSchema] = Field(default_factory=list)
    metadata_values: Dict[str, Any] = Field(default_factory=dict)
    engine_hint: Optional[str] = None
    async_mode: bool = False

class PageResponse(BaseModel):
    page_id: str
    document_id: str
    slug: str
    content_type: str
    status: str
    build_id: Optional[str] = None
    output_url: Optional[str] = None
    checksum_sha256: Optional[str] = None
    engine: Optional[str] = None
    created_at: str

class BuildResponse(BaseModel):
    build_id: str
    page_id: str
    engine: str
    status: str
    error_message: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None

class IntegrityResponse(BaseModel):
    page_id: str
    status: str
    checksum_sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    auto_repaired: bool = False
    message: Optional[str] = None
