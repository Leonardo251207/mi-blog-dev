import sqlite3
from pathlib import Path
from src.config import SQLITE_DB_PATH

def get_connection(db_path: Path = SQLITE_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path = SQLITE_DB_PATH) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                page_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                content_type TEXT NOT NULL,
                status TEXT NOT NULL,
                build_id TEXT,
                output_url TEXT,
                source_snapshot TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS builds (
                build_id TEXT PRIMARY KEY,
                page_id TEXT NOT NULL,
                engine TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (page_id) REFERENCES pages(page_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                page_id TEXT NOT NULL,
                build_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                checksum_sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                mime_type TEXT NOT NULL DEFAULT 'text/html',
                status TEXT NOT NULL DEFAULT 'HEALTHY',
                created_at TEXT NOT NULL,
                FOREIGN KEY (page_id) REFERENCES pages(page_id),
                FOREIGN KEY (build_id) REFERENCES builds(build_id)
            )
        """)
    conn.close()
