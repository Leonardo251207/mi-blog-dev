import uuid
from typing import Dict, Any, Tuple
from src.core.entities import Artifact, ArtifactStatus, PageStatus
from src.core.errors import PageNotFoundError, ArtifactNotFoundError, ArtifactCorruptedError
from src.adapters.driven.sqlite_artifact_repository import SqliteArtifactRepository
from src.adapters.driven.sqlite_page_repository import SqlitePageRepository
from src.adapters.driven.local_storage_adapter import LocalStorageAdapter
from src.slices.generate_sources.ports import GenerateSourcesPort
from src.slices.compile_artifact.ports import CompileArtifactPort
from .ports import ManageArtifactsPort

class ManageArtifactsService(ManageArtifactsPort):
    def __init__(
        self,
        artifact_repo: SqliteArtifactRepository,
        page_repo: SqlitePageRepository,
        storage: LocalStorageAdapter,
        generate_service: GenerateSourcesPort,
        compile_service: CompileArtifactPort
    ):
        self.artifact_repo = artifact_repo
        self.page_repo = page_repo
        self.storage = storage
        self.generate_service = generate_service
        self.compile_service = compile_service

    def rebuild(self, page_id: str) -> Artifact:
        page = self.page_repo.get_page(page_id)
        if not page or not page.source_snapshot:
            raise PageNotFoundError(page_id)

        # 1. Regenerate sources
        bundle = self.generate_service.execute(page.source_snapshot)

        # 2. Recompile artifact
        new_build_id = f"bld-rebuild-{uuid.uuid4().hex[:8]}"
        artifact, build_job = self.compile_service.execute(bundle, new_build_id)

        # 3. Update page record
        page.build_id = new_build_id
        page.output_url = f"/api/v1/pages/{page_id}/content"
        page.status = PageStatus.COMPLETED
        self.page_repo.save_page(page)

        return artifact

    def verify_integrity(self, page_id: str, auto_repair: bool = True) -> Dict[str, Any]:
        artifact = self.artifact_repo.get_by_page_id(page_id)
        if not artifact:
            # Check if page exists in DB with snapshot
            page = self.page_repo.get_page(page_id)
            if page and page.source_snapshot and auto_repair:
                recovered_artifact = self.rebuild(page_id)
                return {
                    "page_id": page_id,
                    "status": ArtifactStatus.HEALTHY.value,
                    "message": "Artifact record was missing; auto-rebuild succeeded.",
                    "checksum_sha256": recovered_artifact.checksum_sha256,
                    "auto_repaired": True
                }
            raise ArtifactNotFoundError(page_id)

        file_exists = self.storage.artifact_exists(artifact.file_path)
        if not file_exists:
            self.artifact_repo.update_status(artifact.artifact_id, ArtifactStatus.MISSING)
            if auto_repair:
                recovered_artifact = self.rebuild(page_id)
                return {
                    "page_id": page_id,
                    "status": ArtifactStatus.HEALTHY.value,
                    "message": "Physical file was missing from storage; auto-rebuild succeeded.",
                    "checksum_sha256": recovered_artifact.checksum_sha256,
                    "auto_repaired": True
                }
            return {
                "page_id": page_id,
                "status": ArtifactStatus.MISSING.value,
                "expected_sha": artifact.checksum_sha256,
                "auto_repaired": False
            }

        # Verify hash
        is_valid = self.storage.verify_artifact(artifact.file_path, artifact.checksum_sha256)
        if not is_valid:
            self.artifact_repo.update_status(artifact.artifact_id, ArtifactStatus.CORRUPTED)
            if auto_repair:
                recovered_artifact = self.rebuild(page_id)
                return {
                    "page_id": page_id,
                    "status": ArtifactStatus.HEALTHY.value,
                    "message": "Physical file checksum mismatch; auto-rebuild succeeded.",
                    "checksum_sha256": recovered_artifact.checksum_sha256,
                    "auto_repaired": True
                }
            return {
                "page_id": page_id,
                "status": ArtifactStatus.CORRUPTED.value,
                "expected_sha": artifact.checksum_sha256,
                "auto_repaired": False
            }

        return {
            "page_id": page_id,
            "status": ArtifactStatus.HEALTHY.value,
            "checksum_sha256": artifact.checksum_sha256,
            "size_bytes": artifact.size_bytes,
            "auto_repaired": False
        }

    def get_content(self, page_id: str) -> Tuple[bytes, str]:
        # Perform integrity verification & auto repair if missing/corrupt
        verification = self.verify_integrity(page_id, auto_repair=True)
        artifact = self.artifact_repo.get_by_page_id(page_id)
        if not artifact:
            raise ArtifactNotFoundError(page_id)
        data = self.storage.read_artifact(artifact.file_path)
        return data, artifact.mime_type
