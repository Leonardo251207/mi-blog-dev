"""Implementación SQLite de `PostRepository`.

Ventajas para este proyecto:
  - Persiste al reiniciar (el CMS deja de perder contenido).
  - No requiere instalar un servidor de base de datos.
  - El archivo se puede respaldar/copiar y abrir con cualquier cliente SQLite.

Para cambiar a PostgreSQL/MySQL basta con crear otra clase que implemente
`PostRepository` y usarla en `create_app()`; el servicio no cambia.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from .domain import Post, PostStatus, iso, parse_iso
from .repository import PostAlreadyExists, PostNotFound, PostRepository, SlugAlreadyExists

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    post_id      TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    slug         TEXT NOT NULL UNIQUE,
    content      TEXT NOT NULL,
    tags         TEXT NOT NULL DEFAULT '[]',
    status       TEXT NOT NULL CHECK (status IN ('BORRADOR', 'PUBLICADO')),
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    published_at TEXT,
    views_total  INTEGER NOT NULL DEFAULT 0 CHECK (views_total >= 0)
);

CREATE INDEX IF NOT EXISTS idx_posts_status_updated
    ON posts (status, updated_at DESC, post_id DESC);

CREATE INDEX IF NOT EXISTS idx_posts_status_published
    ON posts (status, published_at DESC, post_id DESC);
"""


class SqlitePostRepository(PostRepository):
    """Repositorio SQLite con una conexión protegida por un RLock.

    FastAPI ejecuta los endpoints síncronos en un pool de hilos; SQLite no
    permite usar una conexión desde varios hilos por defecto. Se abre con
    `check_same_thread=False` y se serializa el acceso con `RLock`. Para un
    blog de un autor es más que suficiente; si hiciera falta más concurrencia,
    se puede pasar a SQLAlchemy + PostgreSQL sin tocar el servicio.
    """

    def __init__(self, path: str = "data/devblog.db") -> None:
        self.path = path
        if path != ":memory:":
            Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._conn = sqlite3.connect(
            path,
            check_same_thread=False,
            timeout=5.0,
            isolation_level=None,   # transacciones explícitas con BEGIN/COMMIT
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA busy_timeout = 5000")
        if path != ":memory:":
            self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)

    # ------------------------------------------------------------------ mapeo
    @staticmethod
    def _row_to_post(row: sqlite3.Row) -> Post:
        return Post(
            post_id=row["post_id"],
            title=row["title"],
            slug=row["slug"],
            content=row["content"],
            tags=json.loads(row["tags"]),
            status=PostStatus(row["status"]),
            created_at=parse_iso(row["created_at"]),
            updated_at=parse_iso(row["updated_at"]),
            published_at=parse_iso(row["published_at"]) if row["published_at"] else None,
            views_total=int(row["views_total"]),
        )

    @staticmethod
    def _values(post: Post) -> tuple:
        return (
            post.title,
            post.slug,
            post.content,
            json.dumps(post.tags, ensure_ascii=False),
            post.status.value,
            iso(post.created_at),
            iso(post.updated_at),
            iso(post.published_at) if post.published_at else None,
            post.views_total,
        )

    # --------------------------------------------------------------- interfaz
    def insert(self, post: Post) -> None:
        with self._lock:
            try:
                self._conn.execute(
                    """
                    INSERT INTO posts
                        (post_id, title, slug, content, tags, status,
                         created_at, updated_at, published_at, views_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (post.post_id, *self._values(post)),
                )
            except sqlite3.IntegrityError as exc:
                message = str(exc)
                if "posts.slug" in message:
                    raise SlugAlreadyExists(post.slug) from exc
                if "posts.post_id" in message:
                    raise PostAlreadyExists(post.post_id) from exc
                raise

    def get(self, post_id: str) -> Optional[Post]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM posts WHERE post_id = ?", (post_id,)
            ).fetchone()
        return self._row_to_post(row) if row else None

    def get_by_slug(self, slug: str) -> Optional[Post]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM posts WHERE slug = ?", (slug,)
            ).fetchone()
        return self._row_to_post(row) if row else None

    def replace(self, post: Post) -> None:
        with self._lock:
            current = self._conn.execute(
                "SELECT post_id FROM posts WHERE post_id = ?", (post.post_id,)
            ).fetchone()
            if current is None:
                raise PostNotFound(post.post_id)

            owner = self._conn.execute(
                "SELECT post_id FROM posts WHERE slug = ? AND post_id <> ?",
                (post.slug, post.post_id),
            ).fetchone()
            if owner is not None:
                raise SlugAlreadyExists(post.slug)

            try:
                self._conn.execute(
                    """
                    UPDATE posts SET
                        title = ?, slug = ?, content = ?, tags = ?, status = ?,
                        created_at = ?, updated_at = ?, published_at = ?, views_total = ?
                    WHERE post_id = ?
                    """,
                    (*self._values(post), post.post_id),
                )
            except sqlite3.IntegrityError as exc:
                if "posts.slug" in str(exc):
                    raise SlugAlreadyExists(post.slug) from exc
                raise

    def delete(self, post_id: str) -> bool:
        with self._lock:
            cursor = self._conn.execute(
                "DELETE FROM posts WHERE post_id = ?", (post_id,)
            )
            return cursor.rowcount > 0

    def list_page(self, status: PostStatus, order_by: str, limit: int,
                  after: Optional[tuple[datetime, str]] = None,
                  tag: Optional[str] = None) -> tuple[list[Post], bool]:
        if order_by not in ("updated_at", "published_at"):
            raise ValueError(f"order_by no soportado: {order_by}")

        where = ["status = ?"]
        params: list[object] = [status.value]

        if tag:
            # SQLite incluye JSON1 por defecto en Python 3.9+.
            where.append(
                "EXISTS (SELECT 1 FROM json_each(posts.tags) WHERE json_each.value = ?)"
            )
            params.append(tag)

        if after is not None:
            timestamp, last_id = after
            ts = iso(timestamp)
            # Orden total: (timestamp DESC, post_id DESC). La siguiente página
            # trae lo estrictamente posterior a ese par.
            where.append(f"({order_by} < ? OR ({order_by} = ? AND post_id < ?))")
            params.extend([ts, ts, last_id])

        sql = (
            f"SELECT * FROM posts WHERE {' AND '.join(where)} "
            f"ORDER BY {order_by} DESC, post_id DESC LIMIT ?"
        )
        params.append(limit + 1)

        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()

        posts = [self._row_to_post(row) for row in rows]
        return posts[:limit], len(posts) > limit

    def increment_views(self, post_id: str) -> Optional[int]:
        with self._lock:
            cursor = self._conn.execute(
                """
                UPDATE posts SET views_total = views_total + 1
                WHERE post_id = ? AND status = ?
                """,
                (post_id, PostStatus.PUBLICADO.value),
            )
            if cursor.rowcount == 0:
                return None
            row = self._conn.execute(
                "SELECT views_total FROM posts WHERE post_id = ?", (post_id,)
            ).fetchone()
            return int(row["views_total"]) if row else None

    def ping(self) -> bool:
        try:
            with self._lock:
                self._conn.execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False

    def close(self) -> None:
        with self._lock:
            self._conn.close()
