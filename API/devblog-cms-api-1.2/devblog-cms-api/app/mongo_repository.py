"""Implementación MongoDB de `PostRepository`.

Se usa en producción con MongoDB Atlas (capa gratuita M0). El CMS sigue
funcionando con SQLite cuando `CMS_MONGO_URI` está vacío.

Ventajas:
  - Persistencia real sin servidor propio.
  - La misma abstracción `PostRepository`: el servicio no cambia.
  - El servicio de métricas también puede usar el mismo clúster con otra base.

Las fechas se guardan como ISO 8601 UTC (igual que en SQLite) para mantener
el orden lexicográfico y la compatibilidad con el cursor de paginación.
"""
from __future__ import annotations

from typing import Any, Optional

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from .domain import Post, PostStatus, iso, parse_iso
from .repository import PostAlreadyExists, PostNotFound, PostRepository, SlugAlreadyExists


class MongoPostRepository(PostRepository):
    def __init__(
        self,
        uri: str = "",
        db_name: str = "devblog_cms",
        client: Any | None = None,
    ) -> None:
        if client is None:
            if not uri:
                raise ValueError("MongoPostRepository requiere uri o client")
            client = MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000)
        self._client = client
        self._db = client[db_name]
        self._posts = self._db["posts"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._posts.create_index("slug", unique=True, name="uniq_slug")
        self._posts.create_index(
            [("status", 1), ("updated_at", -1), ("_id", -1)],
            name="idx_status_updated",
        )
        self._posts.create_index(
            [("status", 1), ("published_at", -1), ("_id", -1)],
            name="idx_status_published",
        )

    @staticmethod
    def _doc(post: Post) -> dict:
        return {
            "_id": post.post_id,
            "title": post.title,
            "slug": post.slug,
            "content": post.content,
            "tags": list(post.tags),
            "status": post.status.value,
            "created_at": iso(post.created_at),
            "updated_at": iso(post.updated_at),
            "published_at": iso(post.published_at) if post.published_at else None,
            "views_total": int(post.views_total),
        }

    @staticmethod
    def _post(doc: dict) -> Post:
        return Post(
            post_id=doc["_id"],
            title=doc["title"],
            slug=doc["slug"],
            content=doc["content"],
            tags=list(doc.get("tags", [])),
            status=PostStatus(doc["status"]),
            created_at=parse_iso(doc["created_at"]),
            updated_at=parse_iso(doc["updated_at"]),
            published_at=parse_iso(doc["published_at"]) if doc.get("published_at") else None,
            views_total=int(doc.get("views_total", 0)),
        )

    def insert(self, post: Post) -> None:
        # Comprobación explícita para dar un error de dominio claro; el índice
        # único sigue protegiendo contra carreras entre procesos.
        if self._posts.find_one({"slug": post.slug}, {"_id": 1}) is not None:
            raise SlugAlreadyExists(post.slug)
        if self._posts.find_one({"_id": post.post_id}, {"_id": 1}) is not None:
            raise PostAlreadyExists(post.post_id)

        try:
            self._posts.insert_one(self._doc(post))
        except DuplicateKeyError as exc:
            if self._posts.find_one({"slug": post.slug}, {"_id": 1}) is not None:
                raise SlugAlreadyExists(post.slug) from exc
            raise PostAlreadyExists(post.post_id) from exc

    def get(self, post_id: str) -> Optional[Post]:
        doc = self._posts.find_one({"_id": post_id})
        return self._post(doc) if doc else None

    def get_by_slug(self, slug: str) -> Optional[Post]:
        doc = self._posts.find_one({"slug": slug})
        return self._post(doc) if doc else None

    def replace(self, post: Post) -> None:
        if self._posts.find_one({"_id": post.post_id}, {"_id": 1}) is None:
            raise PostNotFound(post.post_id)

        owner = self._posts.find_one(
            {"slug": post.slug, "_id": {"$ne": post.post_id}},
            {"_id": 1},
        )
        if owner is not None:
            raise SlugAlreadyExists(post.slug)

        try:
            result = self._posts.replace_one({"_id": post.post_id}, self._doc(post))
        except DuplicateKeyError as exc:
            if self._posts.find_one(
                {"slug": post.slug, "_id": {"$ne": post.post_id}}, {"_id": 1}
            ) is not None:
                raise SlugAlreadyExists(post.slug) from exc
            raise

        if result.matched_count == 0:
            raise PostNotFound(post.post_id)

    def delete(self, post_id: str) -> bool:
        return self._posts.delete_one({"_id": post_id}).deleted_count > 0

    def list_page(
        self,
        status: PostStatus,
        order_by: str,
        limit: int,
        after: Optional[tuple[Any, str]] = None,
        tag: Optional[str] = None,
    ) -> tuple[list[Post], bool]:
        if order_by not in ("updated_at", "published_at"):
            raise ValueError(f"order_by no soportado: {order_by}")

        query: dict[str, Any] = {"status": status.value}
        if tag:
            query["tags"] = tag

        if after is not None:
            timestamp, last_id = after
            ts = iso(timestamp)
            query["$or"] = [
                {order_by: {"$lt": ts}},
                {order_by: ts, "_id": {"$lt": last_id}},
            ]

        docs = list(
            self._posts.find(query)
            .sort([(order_by, -1), ("_id", -1)])
            .limit(limit + 1)
        )
        return [self._post(doc) for doc in docs[:limit]], len(docs) > limit

    def increment_views(self, post_id: str) -> Optional[int]:
        result = self._posts.update_one(
            {"_id": post_id, "status": PostStatus.PUBLICADO.value},
            {"$inc": {"views_total": 1}},
        )
        if result.modified_count == 0:
            return None
        doc = self._posts.find_one({"_id": post_id}, {"views_total": 1})
        return int(doc["views_total"]) if doc else None

    def ping(self) -> bool:
        try:
            self._db.command("ping")
            return True
        except Exception:
            return False

    def close(self) -> None:
        self._client.close()
