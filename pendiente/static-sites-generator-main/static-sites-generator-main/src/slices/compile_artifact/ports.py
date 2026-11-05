from typing import Protocol, Tuple, Dict, Any
from src.core.entities import SourceBundle, Artifact, BuildJob, EngineType

class CompilerEnginePort(Protocol):
    """Secondary Port: Compiles source bundle into production HTML/assets bytes"""
    def compile(self, bundle: SourceBundle) -> bytes:
        ...

class ArtifactStoragePort(Protocol):
    """Secondary Port: Physical artifact storage with SHA-256 checksum calculation"""
    def save_artifact(self, page_id: str, filename: str, content: bytes) -> Tuple[str, str, int]:
        """Returns: (file_path, checksum_sha256, size_bytes)"""
        ...

class ArtifactRepositoryPort(Protocol):
    """Secondary Port: Metadata repository for Artifacts"""
    def save_artifact(self, artifact: Artifact) -> None:
        ...

class BuildRepositoryPort(Protocol):
    """Secondary Port: Build Job lifecycle state tracking"""
    def save_build(self, build: BuildJob) -> None:
        ...

class CompileArtifactPort(Protocol):
    """Primary / Inbound Port: Compiles source bundle into an integrity-verified artifact"""
    def execute(self, bundle: SourceBundle, build_id: str) -> Tuple[Artifact, BuildJob]:
        ...
