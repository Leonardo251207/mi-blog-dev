"""Pruebas del contrato v1.2. Ejecutar:  pytest -q"""
import base64
import json
import uuid
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

CONSOLE = {"Authorization": "Bearer console-dev-token"}
PUBLIC = {"Authorization": "Bearer public-dev-token"}
BODY = "palabra " * 30          # 240 caracteres (>= 100 para poder publicar)
UUID7_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"


def make_settings(**overrides) -> Settings:
    """ConfiguraciÃ³n aislada: no depende del .env de la mÃ¡quina."""
    base = Settings(
        db_path=":memory:",
        console_token="console-dev-token",
        public_token="public-dev-token",
        cursor_secret="test-cursor-secret",
        cors_origins=("*",),
        public_site_url="",
        public_article_path="/blog/{slug}",
        environment="test",
    )
    return replace(base, **overrides)


@pytest.fixture()
def client():
    # app limpia (SQLite en memoria) por prueba; el lifespan cierra la conexiÃ³n.
    with TestClient(create_app(settings=make_settings())) as test_client:
        yield test_client


def idem():
    return {"Idempotency-Key": uuid.uuid4().hex}


def make_draft(client, title="Mi primer artÃ­culo", content=BODY, **extra):
    r = client.post("/api/v1/drafts", json={"title": title, "content": content, **extra},
                    headers={**CONSOLE, **idem()})
    assert r.status_code == 201, r.text
    return r.json()


def publish(client, post_id):
    r = client.post(f"/api/v1/drafts/{post_id}/publish", headers={**CONSOLE, **idem()})
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------- borradores
def test_create_draft_generates_uuid7_and_slug(client):
    import re
    d = make_draft(client, title="Despliega tu web gratis en Vercel", tags=["tutorial"])
    assert re.match(UUID7_RE, d["post_id"])
    assert d["slug"] == "despliega-tu-web-gratis-en-vercel"
    assert d["status"] == "BORRADOR" and d["created_at"].endswith("Z")


def test_client_cannot_send_post_id_or_status(client):
    r = client.post("/api/v1/drafts", headers={**CONSOLE, **idem()},
                    json={"title": "Titulo valido", "content": BODY, "post_id": "x", "status": "PUBLICADO"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("payload,field", [
    ({"title": "abc", "content": BODY}, "title"),
    ({"title": "Titulo valido", "content": ""}, "content"),
    ({"title": "Titulo valido", "content": BODY, "slug": "Slug Malo"}, "slug"),
    ({"title": "Titulo valido", "content": BODY, "tags": ["a", "a"]}, "tags"),
    ({"title": "Titulo valido", "content": BODY, "tags": ["uno", "dos", "tres", "cuatro", "cinco", "seis"]}, "tags"),
    ({"title": "Titulo valido", "content": BODY, "tags": ["MAYUS"]}, "tags"),
])
def test_validation_errors_use_contract_format(client, payload, field):
    r = client.post("/api/v1/drafts", json=payload, headers={**CONSOLE, **idem()})
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR" and err["field"].startswith(field)


def test_slug_conflict_409_even_against_published(client):
    d = make_draft(client, slug="mismo-slug")
    publish(client, d["post_id"])
    r = client.post("/api/v1/drafts", headers={**CONSOLE, **idem()},
                    json={"title": "Otro titulo", "content": BODY, "slug": "mismo-slug"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "SLUG_DUPLICATED"


def test_idempotency_replay_and_reuse(client):
    h = {**CONSOLE, **idem()}
    body = {"title": "Titulo valido", "content": BODY}
    r1 = client.post("/api/v1/drafts", json=body, headers=h)
    r2 = client.post("/api/v1/drafts", json=body, headers=h)       # reintento
    assert r1.status_code == r2.status_code == 201 and r1.json() == r2.json()
    assert len(client.get("/api/v1/drafts", headers=CONSOLE).json()["items"]) == 1
    r3 = client.post("/api/v1/drafts", json={**body, "title": "Cambiado ok"}, headers=h)
    assert r3.status_code == 422 and r3.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_idempotency_key_required(client):
    r = client.post("/api/v1/drafts", json={"title": "Titulo valido", "content": BODY}, headers=CONSOLE)
    assert r.status_code == 422


def test_put_keeps_slug_and_tags_when_omitted_and_renews_updated_at(client):
    d = make_draft(client, slug="mi-slug", tags=["tutorial"])
    r = client.put(f"/api/v1/drafts/{d['post_id']}", headers=CONSOLE,
                   json={"title": "Titulo nuevo", "content": BODY + "mas"})
    assert r.status_code == 200
    out = r.json()
    assert out["slug"] == "mi-slug" and out["tags"] == ["tutorial"] and out["title"] == "Titulo nuevo"


def test_put_slug_of_other_post_409(client):
    make_draft(client, slug="slug-uno")
    b = make_draft(client, title="Segundo articulo", slug="slug-dos")
    r = client.put(f"/api/v1/drafts/{b['post_id']}", headers=CONSOLE,
                   json={"title": "Segundo articulo", "content": BODY, "slug": "slug-uno"})
    assert r.status_code == 409


def test_get_draft_404_and_422(client):
    assert client.get(f"/api/v1/drafts/{uuid.uuid4()}", headers=CONSOLE).status_code == 422  # no es UUIDv7
    missing = "0192a3b5-1122-7334-8445-556677889900"
    assert client.get(f"/api/v1/drafts/{missing}", headers=CONSOLE).status_code == 404
    assert client.get("/api/v1/drafts/105", headers=CONSOLE).status_code == 422             # id entero (v1.0)


def test_delete_draft_then_404(client):
    d = make_draft(client)
    assert client.delete(f"/api/v1/drafts/{d['post_id']}", headers=CONSOLE).status_code == 204
    assert client.get(f"/api/v1/drafts/{d['post_id']}", headers=CONSOLE).status_code == 404


# ------------------------------------------------------------------- publish
def test_publish_flow_and_invariants(client):
    d = make_draft(client, slug="articulo-uno")
    pid = d["post_id"]
    pub = publish(client, pid)
    assert pub["status"] == "PUBLICADO" and pub["url"] == "/blog/articulo-uno" and pub["published_at"].endswith("Z")
    # Invariantes 1 y 2: todo /drafts responde 409 para un PUBLICADO
    assert client.get(f"/api/v1/drafts/{pid}", headers=CONSOLE).status_code == 409
    assert client.put(f"/api/v1/drafts/{pid}", headers=CONSOLE,
                      json={"title": "Titulo nuevo", "content": BODY}).status_code == 409
    assert client.delete(f"/api/v1/drafts/{pid}", headers=CONSOLE).status_code == 409
    # publicar de nuevo con otra key -> 409 ; con la misma key -> resultado original
    assert client.post(f"/api/v1/drafts/{pid}/publish", headers={**CONSOLE, **idem()}).status_code == 409


def test_publish_same_key_replays_original(client):
    d = make_draft(client)
    h = {**CONSOLE, **idem()}
    r1 = client.post(f"/api/v1/drafts/{d['post_id']}/publish", headers=h)
    r2 = client.post(f"/api/v1/drafts/{d['post_id']}/publish", headers=h)
    assert r1.status_code == r2.status_code == 200 and r1.json() == r2.json()


def test_publish_requires_100_chars(client):
    d = make_draft(client, content="corto")
    r = client.post(f"/api/v1/drafts/{d['post_id']}/publish", headers={**CONSOLE, **idem()})
    assert r.status_code == 422 and r.json()["error"]["code"] == "CONTENT_TOO_SHORT"


# ------------------------------------------------------------------- posts
def test_drafts_are_invisible_to_public(client):
    d = make_draft(client, slug="secreto")
    assert client.get(f"/api/v1/posts/{d['post_id']}", headers=PUBLIC).status_code == 404
    assert client.get("/api/v1/posts/slug/secreto", headers=PUBLIC).status_code == 404
    assert client.get("/api/v1/posts", headers=PUBLIC).json()["items"] == []
    assert client.post(f"/api/v1/posts/{d['post_id']}/views", headers=PUBLIC).status_code == 404


def test_read_by_slug_single_request_and_by_id(client):
    d = make_draft(client, slug="leer-por-slug", tags=["tutorial"])
    publish(client, d["post_id"])
    r = client.get("/api/v1/posts/slug/leer-por-slug", headers=PUBLIC)
    assert r.status_code == 200
    art = r.json()
    assert art["post_id"] == d["post_id"] and art["content"] == BODY and art["reading_time_min"] == 1
    assert client.get(f"/api/v1/posts/{d['post_id']}", headers=PUBLIC).json() == art
    assert client.get("/api/v1/posts/slug/no-existe", headers=PUBLIC).status_code == 404
    assert client.get("/api/v1/posts/slug/Slug_Malo", headers=PUBLIC).status_code == 422


@pytest.mark.parametrize("reserved", ["metrics", "views"])
def test_slug_route_not_shadowed_by_metrics_or_views(client, reserved):
    d = make_draft(client, title="Slug reservado", slug=reserved)
    publish(client, d["post_id"])
    r = client.get(f"/api/v1/posts/slug/{reserved}", headers=PUBLIC)
    assert r.status_code == 200 and r.json()["slug"] == reserved


def test_views_and_metrics(client):
    d = make_draft(client)
    pid = d["post_id"]
    assert client.get(f"/api/v1/posts/{pid}/metrics", headers=CONSOLE).status_code == 409   # BORRADOR
    publish(client, pid)
    for _ in range(3):
        assert client.post(f"/api/v1/posts/{pid}/views", headers=PUBLIC).status_code == 204
    m = client.get(f"/api/v1/posts/{pid}/metrics", headers=CONSOLE).json()
    assert m["views_total"] == 3 and m["reading_time_min"] == 1 and m["post_id"] == pid
    # La Consola NO es actor de /views (scope posts:view) y el sitio NO ve mÃ©tricas
    assert client.post(f"/api/v1/posts/{pid}/views", headers=CONSOLE).status_code == 403
    assert client.get(f"/api/v1/posts/{pid}/metrics", headers=PUBLIC).status_code == 403


def test_delete_post_needs_confirm_and_is_physical(client):
    d = make_draft(client, slug="borrame")
    pid = d["post_id"]
    assert client.delete(f"/api/v1/posts/{pid}?confirm=true", headers=CONSOLE).status_code == 409  # BORRADOR
    publish(client, pid)
    assert client.delete(f"/api/v1/posts/{pid}", headers=CONSOLE).status_code == 422               # falta confirm
    r = client.delete(f"/api/v1/posts/{pid}?confirm=false", headers=CONSOLE)
    assert r.status_code == 422 and r.json()["error"]["code"] == "CONFIRM_REQUIRED"
    assert client.delete(f"/api/v1/posts/{pid}?confirm=true", headers=CONSOLE).status_code == 204
    assert client.get("/api/v1/posts/slug/borrame", headers=PUBLIC).status_code == 404
    # el slug queda libre otra vez
    assert client.post("/api/v1/drafts", headers={**CONSOLE, **idem()},
                       json={"title": "Reutiliza slug", "content": BODY, "slug": "borrame"}).status_code == 201


# ----------------------------------------------------------------- paginaciÃ³n
def test_cursor_pagination_is_complete_stable_and_opaque(client):
    ids = []
    for i in range(5):
        d = make_draft(client, title=f"Articulo numero {i}")
        publish(client, d["post_id"])
        ids.append(d["post_id"])
    seen, cursor, pages = [], None, 0
    while True:
        url = "/api/v1/posts?limit=2" + (f"&cursor={cursor}" if cursor else "")
        body = client.get(url, headers=PUBLIC).json()
        seen += [it["post_id"] for it in body["items"]]
        pages += 1
        cursor = body.get("next_cursor")
        if not cursor:
            break
    assert pages == 3 and seen == list(reversed(ids))          # sin repetidos ni faltantes, mÃ¡s nuevo primero
    # la parte decodificable del cursor sigue siendo {"id", "published_at"};
    # la segunda parte es la firma HMAC que impide alterarlo.
    first = client.get("/api/v1/posts?limit=2", headers=PUBLIC).json()["next_cursor"]
    payload_b64, signature = first.split(".", 1)
    assert signature
    raw = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)))
    assert list(raw) == ["id", "published_at"]


def test_cursor_tampering_is_422(client):
    for i in range(3):
        d = make_draft(client, title=f"Articulo firmado {i}")
        publish(client, d["post_id"])
    cursor = client.get("/api/v1/posts?limit=1", headers=PUBLIC).json()["next_cursor"]
    payload, signature = cursor.split(".", 1)

    bad_payload = payload[:-1] + ("A" if payload[-1] != "A" else "B")
    r1 = client.get(f"/api/v1/posts?cursor={bad_payload}.{signature}", headers=PUBLIC)
    assert r1.status_code == 422 and r1.json()["error"]["code"] == "INVALID_CURSOR"

    bad_signature = signature[:-1] + ("A" if signature[-1] != "A" else "B")
    r2 = client.get(f"/api/v1/posts?cursor={payload}.{bad_signature}", headers=PUBLIC)
    assert r2.status_code == 422 and r2.json()["error"]["code"] == "INVALID_CURSOR"


def test_cursor_from_other_listing_or_garbage_is_422(client):
    for i in range(3):
        make_draft(client, title=f"Borrador numero {i}")
    cur = client.get("/api/v1/drafts?limit=1", headers=CONSOLE).json()["next_cursor"]   # usa updated_at
    r = client.get(f"/api/v1/posts?cursor={cur}", headers=PUBLIC)
    assert r.status_code == 422 and r.json()["error"]["code"] == "INVALID_CURSOR"
    assert client.get("/api/v1/posts?cursor=basura", headers=PUBLIC).status_code == 422
    assert client.get("/api/v1/posts?limit=0", headers=PUBLIC).status_code == 422
    assert client.get("/api/v1/posts?limit=51", headers=PUBLIC).status_code == 422


def test_tag_filter(client):
    a = make_draft(client, title="Articulo con tag", tags=["tutorial"])
    b = make_draft(client, title="Articulo sin tag")
    publish(client, a["post_id"]); publish(client, b["post_id"])
    items = client.get("/api/v1/posts?tag=tutorial", headers=PUBLIC).json()["items"]
    assert [i["post_id"] for i in items] == [a["post_id"]]


# ------------------------------------------------------- seguridad y trÃ¡fico
def test_auth_errors(client):
    assert client.get("/api/v1/drafts").status_code == 401
    assert client.get("/api/v1/drafts", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.get("/api/v1/drafts", headers=PUBLIC).status_code == 403     # el sitio no administra borradores


def test_rate_limit_public_10_per_second(client):
    codes = [client.get("/api/v1/posts", headers=PUBLIC).status_code for _ in range(12)]
    assert codes[:10] == [200] * 10 and codes[10] == 429
    r = client.get("/api/v1/posts", headers=PUBLIC)
    assert r.status_code == 429 and "retry-after" in r.headers
    assert r.json()["error"]["code"] == "RATE_LIMITED"


def test_no_ads_anywhere_in_contract(client):
    spec = json.dumps(client.get("/openapi.json").json()).lower()
    assert "ads" not in spec.replace("heads", "").replace("loads", "").replace("threads", "")


# ------------------------------------------------------------ cachÃ© HTTP (v1.2)
def test_public_reads_have_etag_and_cache_control_and_304(client):
    d = make_draft(client, slug="cacheable")
    publish(client, d["post_id"])
    for url in ("/api/v1/posts", "/api/v1/posts/slug/cacheable", f"/api/v1/posts/{d['post_id']}"):
        r = client.get(url, headers=PUBLIC)
        assert r.status_code == 200
        assert r.headers["cache-control"] == "public, max-age=60"
        etag = r.headers["etag"]
        r2 = client.get(url, headers={**PUBLIC, "If-None-Match": etag})
        assert r2.status_code == 304 and r2.content == b"" and r2.headers["etag"] == etag
        r3 = client.get(url, headers={**PUBLIC, "If-None-Match": '"otro"'})
        assert r3.status_code == 200
    # un mismo cuerpo => mismo ETag; si cambia la lista, cambia el ETag
    # (se usa el token de la Consola: el del sitio pÃºblico ya agotÃ³ su cupo de 10 peticiones/s)
    before = client.get("/api/v1/posts", headers=CONSOLE).headers["etag"]
    e = make_draft(client, title="Otro articulo nuevo")
    publish(client, e["post_id"])
    assert client.get("/api/v1/posts", headers=CONSOLE).headers["etag"] != before


def test_everything_else_is_no_store(client):
    d = make_draft(client, slug="no-cache")
    pid = d["post_id"]
    assert client.get("/api/v1/drafts", headers=CONSOLE).headers["cache-control"] == "no-store"
    assert client.get(f"/api/v1/drafts/{pid}", headers=CONSOLE).headers["cache-control"] == "no-store"
    publish(client, pid)
    assert client.get(f"/api/v1/posts/{pid}/metrics", headers=CONSOLE).headers["cache-control"] == "no-store"
    assert client.post(f"/api/v1/posts/{pid}/views", headers=PUBLIC).headers["cache-control"] == "no-store"
    assert client.get("/api/v1/posts/slug/no-existe", headers=PUBLIC).headers["cache-control"] == "no-store"  # errores
    assert client.get("/api/v1/drafts").headers["cache-control"] == "no-store"                                # 401


def test_reading_does_not_count_a_view(client):
    d = make_draft(client, slug="solo-leer")
    publish(client, d["post_id"])
    for _ in range(3):
        client.get("/api/v1/posts/slug/solo-leer", headers=PUBLIC)
    assert client.get(f"/api/v1/posts/{d['post_id']}/metrics", headers=CONSOLE).json()["views_total"] == 0


# ------------------------------------------------------------ salud, CORS y 500
def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["database"] == "ok"


def test_cors_preflight_allows_frontend(client):
    r = client.options(
        "/api/v1/posts",
        headers={
            "Origin": "http://localhost:5500",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] in ("*", "http://localhost:5500")


def test_publish_url_is_configurable():
    settings = make_settings(
        public_site_url="https://blog.example.com",
        public_article_path="/articulos/{slug}",
    )
    with TestClient(create_app(settings=settings)) as custom_client:
        d = make_draft(custom_client, slug="url-configurable")
        pub = publish(custom_client, d["post_id"])
        assert pub["url"] == "https://blog.example.com/articulos/url-configurable"


def test_unhandled_errors_use_contract_format(monkeypatch):
    app = create_app(settings=make_settings())

    def boom(data):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(app.state.service, "create_draft", boom)
    with TestClient(app, raise_server_exceptions=False) as broken_client:
        r = broken_client.post(
            "/api/v1/drafts",
            json={"title": "Titulo valido", "content": BODY},
            headers={**CONSOLE, **idem()},
        )
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"
    assert r.headers["cache-control"] == "no-store"


