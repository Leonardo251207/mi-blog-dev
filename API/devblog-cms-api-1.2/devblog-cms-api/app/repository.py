"""Capa de persistencia: interfaz y repositorio en memoria.

`PostRepository` es la ÚNICA interfaz que usa el servicio. La implementación
real por defecto es SQLite (`app/sqlite_repository.py`); la de memoria se
conserva para pruebas rápidas y como ejemplo mínimo.

Notas para otra implementación SQL:
  - Invariante 3 (slug único)  -> UNIQUE INDEX sobre `slug`; capturar el error
    de integridad y lanzar SlugAlreadyExists.
  - list_page                  -> ORDER BY ts DESC, post_id DESC
                                  WHERE (ts, post_id) < (:ts, :id) LIMIT :n+1
  - increment_views            -> UPDATE ... SET views_total = views_total + 1
                                  WHERE post_id = :id AND status = 'PUBLICADO'
  - replace con cambio de estado -> UPDATE ... WHERE post_id = :id AND status = 'BORRADOR'
                                  (evita carreras entre editar y publicar).
"""
from __future__ import annotations

import copy
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from .domain import Post, PostStatus


class SlugAlreadyExists(Exception):
    """Violación de la unicidad global del slug (Invariante 3)."""


class PostAlreadyExists(Exception):
    """El post_id ya está ocupado (no debería ocurrir: lo genera el servidor)."""


class PostNotFound(Exception):
    """El Post desapareció entre la lectura y la escritura (carrera)."""


class PostRepository(ABC):
    @abstractmethod
    def insert(self, post: Post) -> None: ...

    @abstractmethod
    def get(self, post_id: str) -> Optional[Post]: ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Post]: ...

    @abstractmethod
    def replace(self, post: Post) -> None: ...

    @abstractmethod
    def delete(self, post_id: str) -> bool: ...

    @abstractmethod
    def list_page(self, status: PostStatus, order_by: str, limit: int,
                  after: Optional[tuple[datetime, str]] = None,
                  tag: Optional[str] = None) -> tuple[list[Post], bool]:
        """Devuelve (elementos, hay_más). `order_by`: 'updated_at' | 'published_at'."""

    @abstractmethod
    def increment_views(self, post_id: str) -> Optional[int]:
        """Suma exactamente 1 y devuelve el nuevo total (None si no existe o no está publicado)."""

    def ping(self) -> bool:
        """Comprobación barata para /health. Las implementaciones pueden sobrescribirla."""
        return True

    def close(self) -> None:
        """Libera recursos. Las implementaciones pueden sobrescribirla."""
        return None


class InMemoryPostRepository(PostRepository):
    """Persistencia en memoria: un dict (la 'tabla única' Publicacion_Blog)
    más un índice por slug. Un RLock hace atómicas las operaciones, porque
    FastAPI ejecuta los endpoints síncronos en un pool de hilos."""

    def __init__(self) -> None:
        self._posts: dict[str, Post] = {}
        self._slug_index: dict[str, str] = {}      # slug -> post_id
        self._lock = threading.RLock()

    def insert(self, post: Post) -> None:
        with self._lock:
            if post.post_id in self._posts:
                raise PostAlreadyExists(post.post_id)
            if post.slug in self._slug_index:
                raise SlugAlreadyExists(post.slug)
            self._posts[post.post_id] = copy.deepcopy(post)
            self._slug_index[post.slug] = post.post_id

    def get(self, post_id: str) -> Optional[Post]:
        with self._lock:
            post = self._posts.get(post_id)
            return copy.deepcopy(post) if post else None   # copia: nadie muta el "disco"

    def get_by_slug(self, slug: str) -> Optional[Post]:
        with self._lock:
            post_id = self._slug_index.get(slug)
            return self.get(post_id) if post_id else None

    def replace(self, post: Post) -> None:
        with self._lock:
            current = self._posts.get(post.post_id)
            if current is None:
                raise PostNotFound(post.post_id)
            owner = self._slug_index.get(post.slug)
            if owner is not None and owner != post.post_id:
                raise SlugAlreadyExists(post.slug)
            if current.slug != post.slug:
                del self._slug_index[current.slug]
                self._slug_index[post.slug] = post.post_id
            self._posts[post.post_id] = copy.deepcopy(post)

    def delete(self, post_id: str) -> bool:
        with self._lock:
            post = self._posts.pop(post_id, None)
            if post is None:
                return False
            del self._slug_index[post.slug]
            return True

    def list_page(self, status, order_by, limit, after=None, tag=None):
        with self._lock:
            rows = [p for p in self._posts.values() if p.status is status]
            if tag:
                rows = [p for p in rows if tag in p.tags]
            key = lambda p: (getattr(p, order_by), p.post_id)
            rows.sort(key=key, reverse=True)                 # (timestamp DESC, id DESC)
            if after is not None:
                rows = [p for p in rows if key(p) < after]   # estrictamente posteriores
            page = rows[:limit]
            return [copy.deepcopy(p) for p in page], len(rows) > limit

    def increment_views(self, post_id: str) -> Optional[int]:
        with self._lock:
            post = self._posts.get(post_id)
            if post is None or post.status is not PostStatus.PUBLICADO:
                return None
            post.views_total += 1
            return post.views_total
