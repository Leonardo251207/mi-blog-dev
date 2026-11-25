"""Pruebas de los módulos nuevos: landing, publicidad y métricas del CMS."""
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

CONSOLE = {"Authorization": "Bearer console-dev-token"}
PUBLIC = {"Authorization": "Bearer public-dev-token"}


def make_settings(**overrides) -> Settings:
    base = Settings(
        db_path=":memory:",
        console_token="console-dev-token",
        public_token="public-dev-token",
        cursor_secret="test-cursor-secret",
        cors_origins=("*",),
        public_site_url="",
        public_article_path="/blog/{slug}",
        environment="test",
        metrics_url="http://127.0.0.1:1",
        metrics_timeout_s=0.3,
    )
    return replace(base, **overrides)


@pytest.fixture()
def client():
    with TestClient(create_app(settings=make_settings())) as test_client:
        yield test_client


# ================================ LANDING ===================================
def test_public_landing_has_default_content_and_active_ad(client):
    r = client.get("/api/v1/landing", headers=PUBLIC)
    assert r.status_code == 200
    body = r.json()
    assert body["content"]["hero"]["first_name"] == "Leonardo"
    assert len(body["content"]["technologies"]) == 6
    assert body["ad"]["title"]
    assert body["ads"][0]["active"] is True
    assert r.headers["cache-control"] == "public, max-age=60"


def test_landing_draft_does_not_change_public_until_publish(client):
    draft = client.get("/api/v1/landing/draft", headers=CONSOLE).json()
    content = draft["content"]
    content["hero"]["first_name"] = "Ada"
    content["hero"]["tagline"] = "Nueva landing desde el CMS."

    saved = client.put("/api/v1/landing/draft", headers=CONSOLE, json=content)
    assert saved.status_code == 200
    assert saved.json()["content"]["hero"]["first_name"] == "Ada"

    public_before = client.get("/api/v1/landing", headers=PUBLIC).json()
    assert public_before["content"]["hero"]["first_name"] == "Leonardo"

    published = client.post("/api/v1/landing/publish", headers=CONSOLE)
    assert published.status_code == 200

    public_after = client.get("/api/v1/landing", headers=PUBLIC).json()
    assert public_after["content"]["hero"]["first_name"] == "Ada"
    assert public_after["content"]["hero"]["tagline"] == "Nueva landing desde el CMS."


def test_landing_rejects_unsafe_urls(client):
    content = client.get("/api/v1/landing/draft", headers=CONSOLE).json()["content"]
    content["hero"]["cta_url"] = "javascript:alert(1)"
    r = client.put("/api/v1/landing/draft", headers=CONSOLE, json=content)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR" or "error" in r.json()


def test_landing_draft_requires_console_token(client):
    assert client.get("/api/v1/landing/draft").status_code == 401
    assert client.get("/api/v1/landing/draft", headers=PUBLIC).status_code == 403


# =============================== PUBLICIDAD =================================
def ad_payload(**overrides):
    data = {
        "title": "Curso de Python",
        "subtitle": "Aprende desde cero",
        "body": "Cupo limitado para la próxima generación.",
        "cta_label": "Inscribirme",
        "cta_url": "https://example.com/curso",
        "image_url": "",
        "layout": "split",
        "theme": {"background": "#101820", "text": "#ffffff", "accent": "#ffd23f"},
        "active": False,
    }
    data.update(overrides)
    return data


def test_ads_crud_and_public_only_returns_active_ads(client):
    created = client.post("/api/v1/ads", headers=CONSOLE, json=ad_payload())
    assert created.status_code == 201
    ad = created.json()
    assert ad["title"] == "Curso de Python"
    assert ad["active"] is False

    public = client.get("/api/v1/ads", headers=PUBLIC).json()
    assert all(item["active"] for item in public)
    assert ad["ad_id"] not in [item["ad_id"] for item in public]

    admin = client.get("/api/v1/ads/admin", headers=CONSOLE).json()
    assert ad["ad_id"] in [item["ad_id"] for item in admin]

    updated = client.put(
        f"/api/v1/ads/{ad['ad_id']}",
        headers=CONSOLE,
        json=ad_payload(active=True, title="Curso de Python 2026"),
    )
    assert updated.status_code == 200
    assert updated.json()["active"] is True

    public_after = client.get("/api/v1/ads", headers=PUBLIC).json()
    assert ad["ad_id"] in [item["ad_id"] for item in public_after]

    deleted = client.delete(f"/api/v1/ads/{ad['ad_id']}", headers=CONSOLE)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/ads/{ad['ad_id']}", headers=PUBLIC).status_code == 404


def test_ads_validate_colors_and_layout(client):
    bad_color = ad_payload(theme={"background": "rojo", "text": "#ffffff", "accent": "#3df0a8"})
    assert client.post("/api/v1/ads", headers=CONSOLE, json=bad_color).status_code == 422

    bad_layout = ad_payload(layout="carrusel")
    assert client.post("/api/v1/ads", headers=CONSOLE, json=bad_layout).status_code == 422


def test_ads_admin_requires_console_token(client):
    assert client.get("/api/v1/ads/admin").status_code == 401
    assert client.get("/api/v1/ads/admin", headers=PUBLIC).status_code == 403


# ================================ MÉTRICAS ==================================
def test_metrics_overview_unavailable_returns_flag(client):
    r = client.get("/api/v1/metrics/overview?days=7&grano=DIA", headers=CONSOLE)
    assert r.status_code == 200
    body = r.json()
    assert body["disponible"] is False
    assert body["error"]
    assert body["pageviews"] == 0


def test_metrics_overview_normalizes_graphql_payload(client, monkeypatch):
    from app.routers import metrics as metrics_router

    now = datetime.now(timezone.utc).replace(microsecond=0)

    def fake_overview(settings, *, days, grano):
        return {
            "disponible": True,
            "sitio": settings.metrics_site,
            "desde": now,
            "hasta": now,
            "grano": grano,
            "pageviews": 42,
            "sesiones": 18,
            "visitantes_unicos": 12,
            "por_ruta": [{"clave": "/", "valor": 30}],
            "por_host": [{"clave": "mi-blog-dev.vercel.app", "valor": 42}],
            "serie": [{"cubo": now, "pageviews": 42, "sesiones": 18}],
            "error": None,
        }

    monkeypatch.setattr(metrics_router, "overview", fake_overview)
    r = client.get("/api/v1/metrics/overview?days=30&grano=HORA", headers=CONSOLE)
    assert r.status_code == 200
    body = r.json()
    assert body["disponible"] is True
    assert body["pageviews"] == 42
    assert body["por_ruta"][0] == {"clave": "/", "valor": 30}
    assert body["serie"][0]["pageviews"] == 42


def test_metrics_overview_requires_console_token(client):
    assert client.get("/api/v1/metrics/overview").status_code == 401
    assert client.get("/api/v1/metrics/overview", headers=PUBLIC).status_code == 403


# ================================= SITIOS ===================================
def test_default_sites_and_project_landing(client):
    sites = client.get("/api/v1/sites", headers=PUBLIC)
    assert sites.status_code == 200
    ids = {site["site_id"] for site in sites.json()}
    assert {"portfolio", "devblog-project", "devblog"} <= ids

    project = client.get("/api/v1/sites/devblog-project/landing", headers=PUBLIC)
    assert project.status_code == 200
    body = project.json()
    assert body["site"]["site_id"] == "devblog-project"
    assert body["content"]["videos"][0]["title"] == "Recorrido del CMS"
    assert body["content"]["sections"]["videos"]["title"]


def test_create_client_site_with_video_and_delete(client):
    payload = {
        "site_id": "cliente-demo",
        "name": "Cliente Demo",
        "kind": "client",
        "domain": "ejemplo.com",
        "description": "Landing de prueba",
        "theme": {
            "preset": "modern-magazine",
            "accent": "#ff8a3d",
            "background": "#050807",
            "surface": "#0b1110",
            "text": "#eef5f1",
            "muted": "#8c9c95",
            "heading_font": "Manrope",
            "body_font": "Georgia",
            "radius": 12,
        },
    }
    created = client.post("/api/v1/sites", headers=CONSOLE, json=payload)
    assert created.status_code == 201
    assert created.json()["site_id"] == "cliente-demo"

    draft = client.get("/api/v1/sites/cliente-demo/landing/draft", headers=CONSOLE)
    assert draft.status_code == 200
    content = draft.json()["content"]
    assert content["hero"]["first_name"] == "Tu"

    content["videos"] = [{
        "title": "Video de bienvenida",
        "description": "Ejemplo",
        "url": "https://example.com/video.mp4",
        "poster": "",
        "captions_url": "",
        "cta_label": "",
        "cta_url": "",
        "aspect": "16:9",
    }]
    saved = client.put("/api/v1/sites/cliente-demo/landing/draft",
                       headers=CONSOLE, json=content)
    assert saved.status_code == 200
    assert client.post("/api/v1/sites/cliente-demo/landing/publish",
                       headers=CONSOLE).status_code == 200

    public = client.get("/api/v1/sites/cliente-demo/landing", headers=PUBLIC)
    assert public.status_code == 200
    assert public.json()["content"]["videos"][0]["url"] == "https://example.com/video.mp4"

    deleted = client.delete("/api/v1/sites/cliente-demo", headers=CONSOLE)
    assert deleted.status_code == 204
    assert client.get("/api/v1/sites/cliente-demo/landing", headers=PUBLIC).status_code == 404


def test_protected_site_cannot_be_deleted(client):
    r = client.delete("/api/v1/sites/portfolio", headers=CONSOLE)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SITE_PROTECTED"


def test_video_url_rejects_javascript(client):
    content = client.get("/api/v1/sites/devblog-project/landing/draft",
                         headers=CONSOLE).json()["content"]
    content["videos"] = [{
        "title": "Malicioso",
        "url": "javascript:alert(1)",
        "aspect": "16:9",
    }]
    r = client.put("/api/v1/sites/devblog-project/landing/draft",
                   headers=CONSOLE, json=content)
    assert r.status_code == 422
