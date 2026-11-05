"""Lógica de negocio: aquí viven las INVARIANTES de dominio (Paso 3).

Los routers solo traducen HTTP <-> servicio; el repositorio solo guarda datos.
Cada regla del contrato se aplica en este archivo y está marcada con su número.

Resumen de invariantes y dónde se cumplen
  1  Ciclo unidireccional ...... no existe ningún método "despublicar"; los métodos de
                                  /drafts rechazan (409) cualquier Post PUBLICADO.
  2  Inmutabilidad editorial ... update_draft rechaza PUBLICADO; el módulo Posts no
                                  tiene operación de edición.
  3  Unicidad de slug .......... el repositorio la garantiza (índice) y el servicio la
                                  traduce a 409 SLUG_DUPLICATED.
  4  Completitud para publicar . publish(): content >= 100 caracteres, title y slug válidos.
  5  Vistas monótonas .......... register_view(): solo PUBLICADO y exactamente +1.
  6  Marcas de tiempo .......... created_at nunca cambia; updated_at solo se renueva al
                                  crear/editar el borrador; published_at se fija una vez.
  7  Visibilidad ............... los borradores responden 404 en la lectura pública.
  8  Integridad de etiquetas ... se valida en los esquemas (schemas.py) antes de llegar aquí.
  9  Identificador opaco ....... post_id lo genera el servidor (uuid7); los esquemas
                                  prohíben que el cliente lo envíe.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import domain
from .domain import Post, PostStatus, slugify, utcnow, uuid7
from .errors import ApiError
from .pagination import decode_cursor, encode_cursor
from .repository import PostNotFound, PostRepository, SlugAlreadyExists
from .schemas import DraftCreate, DraftUpdate


@dataclass
class Page:
    items: list[Post]
    next_cursor: Optional[str]


class PostService:
    def __init__(self, repo: PostRepository, cursor_secret: str) -> None:
        self.repo = repo
        self._cursor_secret = cursor_secret

    # ------------------------------------------------------------------ helpers
    def _get_or_404(self, post_id: str) -> Post:
        post = self.repo.get(post_id)
        if post is None:
            raise ApiError(404, "POST_NOT_FOUND", "El Post no existe.", field="post_id")
        return post

    def _draft_or_error(self, post_id: str) -> Post:
        """Para operaciones de /drafts: 404 si no existe, 409 si ya está PUBLICADO."""
        post = self._get_or_404(post_id)
        if post.status is PostStatus.PUBLICADO:   # Invariantes 1 y 2
            raise ApiError(409, "POST_ALREADY_PUBLISHED",
                           "El Post ya está PUBLICADO; consúltalo en /posts/{post_id}.",
                           field="post_id")
        return post

    def _published_or_404(self, post_id: str) -> Post:
        """Lectura pública: un BORRADOR responde 404 como si no existiera (Invariante 7)."""
        post = self.repo.get(post_id)
        if post is None or post.status is not PostStatus.PUBLICADO:
            raise ApiError(404, "POST_NOT_FOUND", "La publicación no existe.", field="post_id")
        return post

    @staticmethod
    def _slug_conflict() -> ApiError:
        return ApiError(409, "SLUG_DUPLICATED", "El slug ya está en uso.", field="slug")

    # ------------------------------------------------------------- BORRADORES
    def create_draft(self, data: DraftCreate) -> Post:                # endpoint 1
        slug = data.slug or slugify(data.title)
        if not domain.SLUG_RE.fullmatch(slug) or len(slug) < domain.SLUG_MIN:
            raise ApiError(422, "SLUG_GENERATION_FAILED",
                           "No se pudo generar un slug válido desde el título; envía uno.",
                           field="slug")
        now = utcnow()
        post = Post(
            post_id=uuid7(),                       # Invariante 9: lo asigna el servidor
            title=data.title, slug=slug, content=data.content,
            tags=list(data.tags or []),
            status=PostStatus.BORRADOR,            # el Post nace BORRADOR
            created_at=now, updated_at=now,        # Invariante 6
            published_at=None, views_total=0,      # Invariante 5: inicia en 0
        )
        try:
            self.repo.insert(post)                 # Invariante 3 (slug único global)
        except SlugAlreadyExists:
            raise self._slug_conflict()
        return post

    def list_drafts(self, limit: int, cursor: Optional[str]) -> Page:  # endpoint 2
        return self._page(PostStatus.BORRADOR, "updated_at", limit, cursor, tag=None)

    def get_draft(self, post_id: str) -> Post:                         # endpoint 3
        return self._draft_or_error(post_id)

    def update_draft(self, post_id: str, data: DraftUpdate) -> Post:   # endpoint 4
        post = self._draft_or_error(post_id)       # Invariante 2: PUBLICADO -> 409
        post.title = data.title                    # PUT reemplaza title y content
        post.content = data.content
        if data.slug is not None:                  # slug/tags omitidos = se conservan
            post.slug = data.slug
        if data.tags is not None:
            post.tags = list(data.tags)
        post.updated_at = utcnow()                 # Invariante 6: se renueva al editar
        try:
            self.repo.replace(post)                # Invariante 3: slug de otro Post -> 409
        except SlugAlreadyExists:
            raise self._slug_conflict()
        except PostNotFound:
            raise ApiError(404, "POST_NOT_FOUND", "El Post no existe.", field="post_id")
        return post

    def delete_draft(self, post_id: str) -> None:                      # endpoint 5
        self._draft_or_error(post_id)              # PUBLICADO -> 409 (se borra por /posts)
        if not self.repo.delete(post_id):
            raise ApiError(404, "POST_NOT_FOUND", "El Post no existe.", field="post_id")

    def publish(self, post_id: str) -> Post:                           # endpoint 6
        post = self._draft_or_error(post_id)       # 404 / 409 si ya estaba PUBLICADO
        # Invariante 4 (completitud). title y slug ya se validaron al crear/editar,
        # pero se re-verifican por defensa en profundidad.
        if len(post.content) < domain.CONTENT_MIN_TO_PUBLISH:
            raise ApiError(422, "CONTENT_TOO_SHORT",
                           f"content necesita al menos {domain.CONTENT_MIN_TO_PUBLISH} "
                           "caracteres para publicarse.", field="content")
        if not (domain.TITLE_MIN <= len(post.title) <= domain.TITLE_MAX):
            raise ApiError(422, "INVALID_TITLE", "title no cumple 5-120 caracteres.", field="title")
        if not domain.SLUG_RE.fullmatch(post.slug):
            raise ApiError(422, "INVALID_SLUG", "slug no cumple el formato.", field="slug")
        # Transición única BORRADOR -> PUBLICADO (Invariante 1: sin vuelta atrás).
        post.status = PostStatus.PUBLICADO
        post.published_at = max(utcnow(), post.created_at)   # Invariante 6: una sola vez, >= created_at
        # Nótese que NO se toca updated_at: solo cambia con ediciones del borrador.
        # title/slug/content/tags quedan inmutables porque ya no hay operación de edición (Inv. 2).
        try:
            self.repo.replace(post)
        except PostNotFound:
            raise ApiError(404, "POST_NOT_FOUND", "El Post no existe.", field="post_id")
        return post

    # ----------------------------------------------------------- PUBLICACIONES
    def list_posts(self, limit: int, cursor: Optional[str], tag: Optional[str]) -> Page:  # endpoint 7
        return self._page(PostStatus.PUBLICADO, "published_at", limit, cursor, tag)

    def get_post(self, post_id: str) -> Post:                          # endpoint 8
        return self._published_or_404(post_id)

    def get_post_by_slug(self, slug: str) -> Post:                     # endpoint 9
        post = self.repo.get_by_slug(slug)         # slug único global => 0 o 1 resultado (Inv. 3)
        if post is None or post.status is not PostStatus.PUBLICADO:    # Invariante 7
            raise ApiError(404, "POST_NOT_FOUND", "La publicación no existe.", field="slug")
        return post

    def delete_post(self, post_id: str, confirm: bool) -> None:        # endpoint 10
        if not confirm:                            # borrado irreversible: exige confirm=true
            raise ApiError(422, "CONFIRM_REQUIRED",
                           "Eliminar una publicación exige confirm=true.", field="confirm")
        post = self._get_or_404(post_id)
        if post.status is PostStatus.BORRADOR:
            raise ApiError(409, "POST_NOT_PUBLISHED",
                           "El Post es un BORRADOR; elimínalo con DELETE /drafts/{post_id}.",
                           field="post_id")
        if not self.repo.delete(post_id):          # borrado físico (incluye views_total)
            raise ApiError(404, "POST_NOT_FOUND", "La publicación no existe.", field="post_id")

    def get_metrics(self, post_id: str) -> Post:                       # endpoint 11
        post = self._get_or_404(post_id)
        if post.status is PostStatus.BORRADOR:     # solo las publicaciones tienen métricas
            raise ApiError(409, "POST_NOT_PUBLISHED",
                           "Un BORRADOR no tiene métricas.", field="post_id")
        return post

    def register_view(self, post_id: str) -> None:                     # endpoint 12
        self._published_or_404(post_id)            # solo PUBLICADO acumula vistas (Inv. 5)
        if self.repo.increment_views(post_id) is None:   # +1 atómico, nunca decrece
            raise ApiError(404, "POST_NOT_FOUND", "La publicación no existe.", field="post_id")

    # --------------------------------------------------------------- paginación
    def _page(self, status: PostStatus, order_by: str, limit: int,
              cursor: Optional[str], tag: Optional[str]) -> Page:
        after = decode_cursor(cursor, order_by, self._cursor_secret) if cursor else None
        # `after` es (timestamp, id); el repositorio compara con la misma llave.
        items, has_more = self.repo.list_page(status, order_by, limit, after, tag)
        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = encode_cursor(
                last.post_id, order_by, getattr(last, order_by), self._cursor_secret
            )
        return Page(items, next_cursor)
