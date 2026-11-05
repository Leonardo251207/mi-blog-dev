import uuid
from typing import Dict, Tuple
from src.core.entities import (
    SourceBundle,
    Artifact,
    BuildJob,
    EngineType,
    BuildStatus,
    ArtifactStatus,
    utc_now_iso
)
from src.core.errors import UnsupportedEngineError, BuildExecutionError
from .ports import CompileArtifactPort, CompilerEnginePort, ArtifactStoragePort, ArtifactRepositoryPort, BuildRepositoryPort
from .adapters import AstroCompilerAdapter, HugoCompilerAdapter, QuartoCompilerAdapter

class CompileArtifactService(CompileArtifactPort):
    def __init__(
        self,
        storage_port: ArtifactStoragePort,
        artifact_repo: ArtifactRepositoryPort,
        build_repo: BuildRepositoryPort
    ):
        self.storage = storage_port
        self.artifact_repo = artifact_repo
        self.build_repo = build_repo
        self.compilers: Dict[EngineType, CompilerEnginePort] = {
            EngineType.ASTRO: AstroCompilerAdapter(),
            EngineType.HUGO: HugoCompilerAdapter(),
            EngineType.QUARTO: QuartoCompilerAdapter(),
        }

    def execute(self, bundle: SourceBundle, build_id: str) -> Tuple[Artifact, BuildJob]:
        build_job = BuildJob(
            build_id=build_id,
            page_id=bundle.page_id,
            engine=bundle.engine,
            status=BuildStatus.PROCESSING,
            started_at=utc_now_iso()
        )
        self.build_repo.save_build(build_job)

        compiler = self.compilers.get(bundle.engine)
        if not compiler:
            build_job.status = BuildStatus.FAILED
            build_job.error_message = f"Unsupported engine: {bundle.engine}"
            build_job.completed_at = utc_now_iso()
            self.build_repo.save_build(build_job)
            raise UnsupportedEngineError(bundle.engine.value)

        try:
            # Execute compilation
            compiled_bytes = compiler.compile(bundle)

            # Store physical artifact & compute SHA-256
            file_path, sha256_hash, size_bytes = self.storage.save_artifact(
                page_id=bundle.page_id,
                filename="index.html",
                content=compiled_bytes
            )

            # Create artifact entity
            artifact = Artifact(
                artifact_id=f"art-{uuid.uuid4().hex[:12]}",
                page_id=bundle.page_id,
                build_id=build_id,
                file_path=file_path,
                checksum_sha256=sha256_hash,
                size_bytes=size_bytes,
                mime_type="text/html",
                status=ArtifactStatus.HEALTHY,
                created_at=utc_now_iso()
            )
            self.artifact_repo.save_artifact(artifact)

            # Complete build
            build_job.status = BuildStatus.COMPLETED
            build_job.completed_at = utc_now_iso()
            self.build_repo.save_build(build_job)

            return artifact, build_job

        except Exception as e:
            build_job.status = BuildStatus.FAILED
            build_job.error_message = str(e)
            build_job.completed_at = utc_now_iso()
            self.build_repo.save_build(build_job)
            raise BuildExecutionError(str(e))
