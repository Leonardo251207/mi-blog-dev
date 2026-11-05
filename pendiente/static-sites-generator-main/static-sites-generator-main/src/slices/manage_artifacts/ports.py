from typing import Protocol, Dict, Any, Tuple
from src.core.entities import Artifact

class ManageArtifactsPort(Protocol):
    """Inbound Port for artifact inspection, integrity verification, auto-recovery and content serving"""
    def get_content(self, page_id: str) -> Tuple[bytes, str]:
        """Returns (content_bytes, mime_type)"""
        ...

    def verify_integrity(self, page_id: str) -> Dict[str, Any]:
        """Verifies disk existence and SHA-256 hash match, auto-recovering if needed"""
        ...

    def rebuild(self, page_id: str) -> Artifact:
        """Forces a rebuild from the stored immutable snapshot"""
        ...
