"""Pruebas de persistencia real con SQLite en un archivo temporal."""
import uuid

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

CONSOLE = {"Authorization": "Bearer console-dev-token"}
PUBLIC = {"Authorization": "Bearer public-dev-token"}
BODY = "contenido persistente " * 10   # > 100 caracteres


def settings_for(db_path: str) -> Settings:
    return Settings(
        db_path=db_path,
        console_token="console-dev-token",
        public_token="public-dev-token",
        cursor_secret="test-cursor-secret",
        cors_origins=("*",),
        public_article_path="/blog/{slug}",
        environment="test",
    )


def idem() -> dict:
    return {"Idempotency-Key": uuid.uuid4().hex}


def test_sqlite_persists_between_app_instances(tmp_path):
    db_path = str(tmp_path / "devblog.db")

    # Primera instancia: crea y publica un artÃ­culo.
    with TestClient(create_app(settings=settings_for(db_path))) as first:
        created = first.post(
            "/api/v1/drafts",
            json={
                "title": "Articulo persistente",
                "slug": "articulo-persistente",
                "content": BODY,
                "tags": ["prueba"],
            },
            headers={**CONSOLE, **idem()},
        )
        assert created.status_code == 201, created.text
        published = first.post(
            f"/api/v1/drafts/{created.json()['post_id']}/publish",
            headers={**CONSOLE, **idem()},
        )
        assert published.status_code == 200, published.text

    # Segunda instancia: el artÃ­culo sigue ahÃ­ (no se perdiÃ³ al "reiniciar").
    with TestClient(create_app(settings=settings_for(db_path))) as second:
        r = second.get("/api/v1/posts/slug/articulo-persistente", headers=PUBLIC)
        assert r.status_code == 200
        assert r.json()["content"] == BODY
        assert r.json()["tags"] == ["prueba"]


def test_sqlite_rejects_duplicate_slug_across_restarts(tmp_path):
    db_path = str(tmp_path / "devblog.db")

    with TestClient(create_app(settings=settings_for(db_path))) as first:
        r = first.post(
            "/api/v1/drafts",
            json={"title": "Primer articulo", "content": BODY, "slug": "mismo-slug"},
            headers={**CONSOLE, **idem()},
        )
        assert r.status_code == 201

    with TestClient(create_app(settings=settings_for(db_path))) as second:
        r = second.post(
            "/api/v1/drafts",
            json={"title": "Segundo articulo", "content": BODY, "slug": "mismo-slug"},
            headers={**CONSOLE, **idem()},
        )
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "SLUG_DUPLICATED"

