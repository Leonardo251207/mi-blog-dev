from typing import Protocol, Dict, Any, List
from src.core.entities import SourceBundle, EngineType, CanvasBlock

class SourceTransformerPort(Protocol):
    """Secondary Port: Engine-specific transformer from CMS canvas blocks to source files"""
    def transform(self, page_id: str, slug: str, content_type: str, blocks: List[CanvasBlock], metadata: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, str]:
        """Returns a dict of {relative_file_path: file_content_text}"""
        ...

class SourceStoragePort(Protocol):
    """Secondary Port: Persisting source code files"""
    def save_source_file(self, page_id: str, relative_path: str, content: str) -> str:
        ...

class GenerateSourcesPort(Protocol):
    """Primary / Inbound Port: Generating source code bundle from snapshot"""
    def execute(self, snapshot: Dict[str, Any]) -> SourceBundle:
        ...
