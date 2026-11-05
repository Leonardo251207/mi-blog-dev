"""Pruebas del repositorio MongoDB con mongomock (sin Atlas)."""
import uuid
from dataclasses import replace

import mongomock
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import ApiError
from app.main import create_app
from app.mongo_repository import MongoPostRepository
from app.repository import SlugAlreadyExists
from app.schemas import DraftCreate
from app.services import PostService

BODY = "contenido de prueba " * 12


def make_repo() -> MongoPostRepository:
    client = mongomock.MongoClient(tz_aware=True)
    return MongoPostRepository(client=client, db_name="devblog_test")


def make_service() -> PostService:
    return PostService(make_repo(), "test-cursor-secret")


def test_mongo_insert_get_and_duplicate_slug():
    repo = make_repo()
    service = PostService(repo, "secret")
    draft = service.create_draft(DraftCreate(title="Primer articulo", content=BODY, slug="primer-articulo"))
    assert service.get_draft(draft.post_id).slug == "primer-articulo"
    with pytest.raises(SlugAlreadyExists):
        repo.insert(replace(draft, post_id=uuid.uuid4().hex))


def test_mongo_publish_list_filter_and_views():
    repo = make_repo()
    service = PostService(repo, "secret")
    a = service.create_draft(DraftCreate(title="Articulo tutorial", content=BODY, tags=["tutorial"]))
    b = service.create_draft(DraftCreate(title="Articulo deployment", content=BODY, tags=["deployment"]))
    service.publish(a.post_id)
    service.publish(b.post_id)

    page = service.list_posts(10, None, None)
    assert len(page.items) == 2 and not page.next_cursor
    tagged = service.list_posts(10, None, "tutorial").items
    assert [p.post_id for p in tagged] == [a.post_id]

    service.register_view(a.post_id)
    service.register_view(a.post_id)
    assert service.get_metrics(a.post_id).views_total == 2


def test_mongo_cursor_pagination_and_update_conflict():
    repo = make_repo()
    service = PostService(repo, "secret")
    posts = []
    for i in range(5):
        draft = service.create_draft(DraftCreate(title=f"Articulo numero {i}", content=BODY))
        service.publish(draft.post_id)
        posts.append(draft.post_id)

    seen = []
    cursor = None
    while True:
        page = service.list_posts(2, cursor, None)
        seen.extend(p.post_id for p in page.items)
        cursor = page.next_cursor
        if not cursor:
            break
    assert seen == list(reversed(posts))

    a = service.create_draft(DraftCreate(title="Borrador uno", content=BODY, slug="slug-uno"))
    b = service.create_draft(DraftCreate(title="Borrador dos", content=BODY, slug="slug-dos"))
    with pytest.raises(ApiError) as exc:
        service.update_draft(b.post_id, DraftCreate(title="Borrador dos", content=BODY, slug="slug-uno"))
    assert exc.value.status_code == 409
    assert service.get_draft(a.post_id).slug == "slug-uno"


def test_mongo_api_end_to_end():
    settings = Settings(
        db_path=":memory:",
        console_token="console-dev-token",
        public_token="public-dev-token",
        cursor_secret="test-cursor-secret",
        cors_origins=("*",),
        public_article_path="/blog/{slug}",
        environment="test",
    )
    repo = make_repo()
    headers = {"Authorization": "Bearer console-dev-token", "Idempotency-Key": uuid.uuid4().hex}

    with TestClient(create_app(settings=settings, repository=repo)) as client:
        created = client.post(
            "/api/v1/drafts",
            json={"title": "Articulo Mongo", "content": BODY, "slug": "articulo-mongo", "tags": ["mongo"]},
            headers=headers,
        )
        assert created.status_code == 201, created.text
        post_id = created.json()["post_id"]
        published = client.post(f"/api/v1/drafts/{post_id}/publish", headers={**headers, "Idempotency-Key": uuid.uuid4().hex})
        assert published.status_code == 200, published.text

        public = {"Authorization": "Bearer public-dev-token"}
        assert client.get("/api/v1/posts?tag=mongo", headers=public).json()["items"][0]["post_id"] == post_id
        assert client.get("/api/v1/posts/slug/articulo-mongo", headers=public).json()["content"] == BODY
        assert client.post(f"/api/v1/posts/{post_id}/views", headers=public).status_code == 204
        metrics = client.get(f"/api/v1/posts/{post_id}/metrics", headers={"Authorization": "Bearer console-dev-token"})
        assert metrics.json()["views_total"] == 1
