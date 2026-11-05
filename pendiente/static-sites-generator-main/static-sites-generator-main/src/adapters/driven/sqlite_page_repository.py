import json
from typing import Optional, List
from src.core.entities import Page, PageStatus, BuildJob, BuildStatus, EngineType
from src.shared.database import get_connection

class SqlitePageRepository:
    def save_page(self, page: Page) -> None:
        conn = get_connection()
        snapshot_json = json.dumps(page.source_snapshot) if page.source_snapshot else None
        with conn:
            conn.execute("""
                INSERT INTO pages (page_id, document_id, slug, content_type, status, build_id, output_url, source_snapshot, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(page_id) DO UPDATE SET
                    slug=excluded.slug,
                    content_type=excluded.content_type,
                    status=excluded.status,
                    build_id=excluded.build_id,
                    output_url=excluded.output_url,
                    source_snapshot=coalesce(excluded.source_snapshot, pages.source_snapshot),
                    updated_at=excluded.updated_at
            """, (
                page.page_id,
                page.document_id,
                page.slug,
                page.content_type,
                page.status.value,
                page.build_id,
                page.output_url,
                snapshot_json,
                page.created_at,
                page.updated_at
            ))
        conn.close()

    def get_page(self, page_id: str) -> Optional[Page]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM pages WHERE page_id = ?", (page_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        snapshot = json.loads(row["source_snapshot"]) if row["source_snapshot"] else None
        return Page(
            page_id=row["page_id"],
            document_id=row["document_id"],
            slug=row["slug"],
            content_type=row["content_type"],
            status=PageStatus(row["status"]),
            build_id=row["build_id"],
            output_url=row["output_url"],
            source_snapshot=snapshot,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def get_by_slug(self, slug: str) -> Optional[Page]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM pages WHERE slug = ?", (slug,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        snapshot = json.loads(row["source_snapshot"]) if row["source_snapshot"] else None
        return Page(
            page_id=row["page_id"],
            document_id=row["document_id"],
            slug=row["slug"],
            content_type=row["content_type"],
            status=PageStatus(row["status"]),
            build_id=row["build_id"],
            output_url=row["output_url"],
            source_snapshot=snapshot,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def save_build(self, build: BuildJob) -> None:
        conn = get_connection()
        with conn:
            conn.execute("""
                INSERT INTO builds (build_id, page_id, engine, status, error_message, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(build_id) DO UPDATE SET
                    status=excluded.status,
                    error_message=excluded.error_message,
                    completed_at=excluded.completed_at
            """, (
                build.build_id,
                build.page_id,
                build.engine.value,
                build.status.value,
                build.error_message,
                build.started_at,
                build.completed_at
            ))
        conn.close()

    def get_build(self, build_id: str) -> Optional[BuildJob]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM builds WHERE build_id = ?", (build_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return BuildJob(
            build_id=row["build_id"],
            page_id=row["page_id"],
            engine=EngineType(row["engine"]),
            status=BuildStatus(row["status"]),
            error_message=row["error_message"],
            started_at=row["started_at"],
            completed_at=row["completed_at"]
        )
