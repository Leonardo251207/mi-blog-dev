from pathlib import Path
from typing import Tuple, Optional
from src.config import STORAGE_DIR, SOURCES_DIR
from src.shared.file_storage import save_bytes, read_bytes, verify_file_integrity, calculate_sha256

class LocalStorageAdapter:
    def __init__(self, storage_dir: Path = STORAGE_DIR, sources_dir: Path = SOURCES_DIR):
        self.storage_dir = storage_dir
        self.sources_dir = sources_dir

    def save_source_file(self, page_id: str, relative_path: str, content: str) -> str:
        target_path = self.sources_dir / page_id / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return str(target_path)

    def save_artifact(self, page_id: str, filename: str, content: bytes) -> Tuple[str, str, int]:
        """
        Saves the artifact bytes to storage_dir / page_id / filename.
        Returns: (file_path, checksum_sha256, size_bytes)
        """
        target_path = self.storage_dir / page_id / filename
        size, sha = save_bytes(target_path, content)
        return str(target_path), sha, size

    def read_artifact(self, file_path: str) -> bytes:
        return read_bytes(Path(file_path))

    def artifact_exists(self, file_path: str) -> bool:
        return Path(file_path).is_file()

    def verify_artifact(self, file_path: str, expected_sha: str) -> bool:
        return verify_file_integrity(Path(file_path), expected_sha)

    def delete_artifact_file(self, file_path: str) -> bool:
        p = Path(file_path)
        if p.is_file():
            p.unlink()
            return True
        return False
