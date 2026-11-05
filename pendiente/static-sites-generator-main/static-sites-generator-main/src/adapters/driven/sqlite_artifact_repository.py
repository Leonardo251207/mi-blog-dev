from typing import Optional
from src.core.entities import Artifact, ArtifactStatus
from src.shared.database import get_connection

class SqliteArtifactRepository:
    def save_artifact(self, artifact: Artifact) -> None:
        conn = get_connection()
        with conn:
            conn.execute("""
                INSERT INTO artifacts (artifact_id, page_id, build_id, file_path, checksum_sha256, size_bytes, mime_type, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(artifact_id) DO UPDATE SET
                    checksum_sha256=excluded.checksum_sha256,
                    size_bytes=excluded.size_bytes,
                    status=excluded.status
            """, (
                artifact.artifact_id,
                artifact.page_id,
                artifact.build_id,
                artifact.file_path,
                artifact.checksum_sha256,
                artifact.size_bytes,
                artifact.mime_type,
                artifact.status.value,
                artifact.created_at
            ))
        conn.close()

    def get_by_page_id(self, page_id: str) -> Optional[Artifact]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM artifacts WHERE page_id = ? ORDER BY created_at DESC LIMIT 1", (page_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return Artifact(
            artifact_id=row["artifact_id"],
            page_id=row["page_id"],
            build_id=row["build_id"],
            file_path=row["file_path"],
            checksum_sha256=row["checksum_sha256"],
            size_bytes=row["size_bytes"],
            mime_type=row["mime_type"],
            status=ArtifactStatus(row["status"]),
            created_at=row["created_at"]
        )

    def update_status(self, artifact_id: str, status: ArtifactStatus) -> None:
        conn = get_connection()
        with conn:
            conn.execute("UPDATE artifacts SET status = ? WHERE artifact_id = ?", (status.value, artifact_id))
        conn.close()
