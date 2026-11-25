"""Persistencia del contenido del sitio: landing y publicidad.

Se mantiene separada de `PostRepository` porque son agregados distintos. La
interfaz es la misma para SQLite (local) y MongoDB (producción), igual que en
el blog: el servicio no sabe qué motor hay debajo.

La landing tiene dos copias del mismo documento:
  - `draft`     -> lo que la consola está editando.
  - `published` -> lo que ve el sitio público.
Publicar copia el borrador sobre la versión publicada. Así se puede preparar un
cambio sin romper la landing que ya está en línea.
"""
from __future__ import annotations

import copy
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .content import Ad, Landing, Site
from .content_defaults import (
    DEFAULT_ADS,
    DEFAULT_LANDING_CONTENT,
    DEFAULT_SITES,
    landing_default_for,
)
from .domain import iso, parse_iso, utcnow, uuid7

LANDING_ID = "portfolio"
LEGACY_LANDING_ID = "principal"


class ContentRepositoryError(Exception):
    """Error genérico de persistencia del contenido del sitio."""


class ContentRepository:
    """Interfaz común para landing y publicidad."""

    def list_sites(self) -> list[Site]: ...
    def get_site(self, site_id: str) -> Optional[Site]: ...
    def upsert_site(self, site: Site) -> None: ...
    def delete_site(self, site_id: str) -> bool: ...
    def get_landing(self, site_id: str = LANDING_ID) -> Optional[Landing]: ...
    def save_landing_draft(self, site_id: str, content: dict) -> Landing: ...
    def publish_landing(self, site_id: str = LANDING_ID) -> Optional[Landing]: ...
    def list_ads(self, only_active: bool = False) -> list[Ad]: ...
    def get_ad(self, ad_id: str) -> Optional[Ad]: ...
    def upsert_ad(self, ad: Ad) -> None: ...
    def delete_ad(self, ad_id: str) -> bool: ...
    def ping(self) -> bool: ...
    def close(self) -> None: ...


# ============================== SQLite =======================================
_SCHEMA = """
CREATE TABLE IF NOT EXISTS landing (
    landing_id        TEXT PRIMARY KEY,
    draft_content     TEXT NOT NULL,
    published_content TEXT,
    updated_at        TEXT NOT NULL,
    published_at      TEXT
);

CREATE TABLE IF NOT EXISTS sites (
    site_id     TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    kind        TEXT NOT NULL,
    domain      TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'active',
    theme       TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ads (
    ad_id      TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    subtitle   TEXT NOT NULL DEFAULT '',
    body       TEXT NOT NULL DEFAULT '',
    cta_label  TEXT NOT NULL DEFAULT '',
    cta_url    TEXT NOT NULL DEFAULT '',
    image_url  TEXT NOT NULL DEFAULT '',
    layout     TEXT NOT NULL DEFAULT 'banner'
               CHECK (layout IN ('banner', 'tarjeta', 'split')),
    theme      TEXT NOT NULL DEFAULT '{}',
    active     INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ads_active_created
    ON ads (active, created_at DESC, ad_id DESC);

CREATE TABLE IF NOT EXISTS site_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class SqliteContentRepository(ContentRepository):
    def __init__(self, path: str = "data/devblog.db") -> None:
        self.path = path
        if path != ":memory:":
            Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._conn = sqlite3.connect(
            path,
            check_same_thread=False,
            timeout=5.0,
            isolation_level=None,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA busy_timeout = 5000")
        if path != ":memory:":
            self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.executescript(_SCHEMA)
        self._migrate_legacy_landing()
        self._seed_default_sites()
        self._seed_default_landings()
        self._seed_default_ads()

    # ------------------------------------------------------------- mapeo
    @staticmethod
    def _landing(row: sqlite3.Row | None) -> Optional[Landing]:
        if row is None:
            return None
        published = row["published_content"]
        return Landing(
            landing_id=row["landing_id"],
            draft=json.loads(row["draft_content"]),
            published=json.loads(published) if published else None,
            updated_at=parse_iso(row["updated_at"]),
            published_at=parse_iso(row["published_at"]) if row["published_at"] else None,
        )

    @staticmethod
    def _ad(row: sqlite3.Row) -> Ad:
        return Ad(
            ad_id=row["ad_id"],
            title=row["title"],
            subtitle=row["subtitle"],
            body=row["body"],
            cta_label=row["cta_label"],
            cta_url=row["cta_url"],
            image_url=row["image_url"],
            layout=row["layout"],
            theme=json.loads(row["theme"] or "{}"),
            active=bool(row["active"]),
            created_at=parse_iso(row["created_at"]),
            updated_at=parse_iso(row["updated_at"]),
        )

    @staticmethod
    def _site(row: sqlite3.Row) -> Site:
        return Site(
            site_id=row["site_id"],
            name=row["name"],
            kind=row["kind"],
            domain=row["domain"],
            description=row["description"],
            status=row["status"],
            theme=json.loads(row["theme"] or "{}"),
            created_at=parse_iso(row["created_at"]),
            updated_at=parse_iso(row["updated_at"]),
        )

    def _migrate_legacy_landing(self) -> None:
        """Migra la landing única `principal` al sitio `portfolio`."""
        with self._lock:
            legacy = self._conn.execute(
                "SELECT 1 FROM landing WHERE landing_id = ?", (LEGACY_LANDING_ID,)
            ).fetchone()
            current = self._conn.execute(
                "SELECT 1 FROM landing WHERE landing_id = ?", (LANDING_ID,)
            ).fetchone()
            if legacy is not None and current is None:
                self._conn.execute(
                    """
                    INSERT INTO landing
                        (landing_id, draft_content, published_content, updated_at, published_at)
                    SELECT ?, draft_content, published_content, updated_at, published_at
                    FROM landing WHERE landing_id = ?
                    """,
                    (LANDING_ID, LEGACY_LANDING_ID),
                )

    def _seed_default_sites(self) -> None:
        now = utcnow()
        with self._lock:
            for item in DEFAULT_SITES:
                self._conn.execute(
                    """
                    INSERT OR IGNORE INTO sites
                        (site_id, name, kind, domain, description, status, theme, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["site_id"],
                        item["name"],
                        item["kind"],
                        item.get("domain", ""),
                        item.get("description", ""),
                        item.get("status", "active"),
                        json.dumps(item.get("theme", {}), ensure_ascii=False),
                        iso(now),
                        iso(now),
                    ),
                )

    def _seed_default_landings(self) -> None:
        now = utcnow()
        with self._lock:
            for item in DEFAULT_SITES:
                content = landing_default_for(item["site_id"], item["kind"])
                payload = json.dumps(content, ensure_ascii=False)
                self._conn.execute(
                    """
                    INSERT OR IGNORE INTO landing
                        (landing_id, draft_content, published_content, updated_at, published_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (item["site_id"], payload, payload, iso(now), iso(now)),
                )

    def _seed_default_ads(self) -> None:
        """Crea la publicidad de ejemplo una sola vez.

        El marcador `ads_seeded` evita que un anuncio borrado reaparezca al
        reiniciar el servicio (lo que sería muy confuso para el editor).
        """
        now = utcnow()
        with self._lock:
            marker = self._conn.execute(
                "SELECT value FROM site_meta WHERE key = 'ads_seeded'"
            ).fetchone()
            if marker is not None:
                return
            for item in DEFAULT_ADS:
                self.upsert_ad(Ad(
                    ad_id=uuid7(),
                    title=item["title"],
                    subtitle=item["subtitle"],
                    body=item["body"],
                    cta_label=item["cta_label"],
                    cta_url=item["cta_url"],
                    image_url=item["image_url"],
                    layout=item["layout"],
                    theme=dict(item["theme"]),
                    active=bool(item["active"]),
                    created_at=now,
                    updated_at=now,
                ))
            self._conn.execute(
                "INSERT INTO site_meta (key, value) VALUES ('ads_seeded', ?)",
                (iso(now),),
            )

    # ------------------------------------------------------------ sitios
    def list_sites(self) -> list[Site]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sites ORDER BY created_at ASC, site_id ASC"
            ).fetchall()
        return [self._site(row) for row in rows]

    def get_site(self, site_id: str) -> Optional[Site]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM sites WHERE site_id = ?", (site_id,)
            ).fetchone()
        return self._site(row) if row else None

    def upsert_site(self, site: Site) -> None:
        now = site.updated_at or utcnow()
        created = site.created_at or now
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO sites
                    (site_id, name, kind, domain, description, status, theme, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(site_id) DO UPDATE SET
                    name = excluded.name,
                    kind = excluded.kind,
                    domain = excluded.domain,
                    description = excluded.description,
                    status = excluded.status,
                    theme = excluded.theme,
                    updated_at = excluded.updated_at
                """,
                (
                    site.site_id,
                    site.name,
                    site.kind,
                    site.domain,
                    site.description,
                    site.status,
                    json.dumps(site.theme or {}, ensure_ascii=False),
                    iso(created),
                    iso(now),
                ),
            )

    def delete_site(self, site_id: str) -> bool:
        with self._lock:
            self._conn.execute("DELETE FROM landing WHERE landing_id = ?", (site_id,))
            result = self._conn.execute(
                "DELETE FROM sites WHERE site_id = ?", (site_id,)
            )
        return result.rowcount > 0

    # ---------------------------------------------------------- landing
    def get_landing(self, site_id: str = LANDING_ID) -> Optional[Landing]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM landing WHERE landing_id = ?", (site_id,)
            ).fetchone()
        return self._landing(row)

    def save_landing_draft(self, site_id: str, content: dict) -> Landing:
        now = utcnow()
        payload = json.dumps(content, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO landing
                    (landing_id, draft_content, published_content, updated_at, published_at)
                VALUES (?, ?, NULL, ?, NULL)
                ON CONFLICT(landing_id) DO UPDATE SET
                    draft_content = excluded.draft_content,
                    updated_at = excluded.updated_at
                """,
                (site_id, payload, iso(now)),
            )
            row = self._conn.execute(
                "SELECT * FROM landing WHERE landing_id = ?", (site_id,)
            ).fetchone()
        landing = self._landing(row)
        assert landing is not None
        return landing

    def publish_landing(self, site_id: str = LANDING_ID) -> Optional[Landing]:
        now = utcnow()
        with self._lock:
            self._conn.execute(
                """
                UPDATE landing SET
                    published_content = draft_content,
                    published_at = ?
                WHERE landing_id = ?
                """,
                (iso(now), site_id),
            )
        return self.get_landing(site_id)

    # -------------------------------------------------------------- ads
    def list_ads(self, only_active: bool = False) -> list[Ad]:
        sql = "SELECT * FROM ads"
        params: tuple[Any, ...] = ()
        if only_active:
            sql += " WHERE active = 1"
        sql += " ORDER BY created_at DESC, ad_id DESC"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [self._ad(row) for row in rows]

    def get_ad(self, ad_id: str) -> Optional[Ad]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM ads WHERE ad_id = ?", (ad_id,)
            ).fetchone()
        return self._ad(row) if row else None

    def upsert_ad(self, ad: Ad) -> None:
        now = ad.updated_at or utcnow()
        created = ad.created_at or now
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO ads
                    (ad_id, title, subtitle, body, cta_label, cta_url, image_url,
                     layout, theme, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ad_id) DO UPDATE SET
                    title = excluded.title,
                    subtitle = excluded.subtitle,
                    body = excluded.body,
                    cta_label = excluded.cta_label,
                    cta_url = excluded.cta_url,
                    image_url = excluded.image_url,
                    layout = excluded.layout,
                    theme = excluded.theme,
                    active = excluded.active,
                    updated_at = excluded.updated_at
                """,
                (
                    ad.ad_id,
                    ad.title,
                    ad.subtitle,
                    ad.body,
                    ad.cta_label,
                    ad.cta_url,
                    ad.image_url,
                    ad.layout,
                    json.dumps(ad.theme or {}, ensure_ascii=False),
                    1 if ad.active else 0,
                    iso(created),
                    iso(now),
                ),
            )

    def delete_ad(self, ad_id: str) -> bool:
        with self._lock:
            cursor = self._conn.execute("DELETE FROM ads WHERE ad_id = ?", (ad_id,))
            return cursor.rowcount > 0

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


# ============================== MongoDB ======================================
class MongoContentRepository(ContentRepository):
    def __init__(
        self,
        uri: str = "",
        db_name: str = "devblog_cms",
        client: Any | None = None,
    ) -> None:
        if client is None:
            if not uri:
                raise ValueError("MongoContentRepository requiere uri o client")
            from pymongo import MongoClient

            client = MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000)
        self._client = client
        self._db = client[db_name]
        self._landing = self._db["landing"]
        self._sites = self._db["sites"]
        self._ads = self._db["ads"]
        self._meta = self._db["site_meta"]
        self._ensure_indexes()
        self._migrate_legacy_landing()
        self._seed_default_sites()
        self._seed_default_landings()
        self._seed_default_ads()

    def _ensure_indexes(self) -> None:
        self._ads.create_index(
            [("active", 1), ("created_at", -1), ("_id", -1)],
            name="idx_active_created",
        )

    def _migrate_legacy_landing(self) -> None:
        if self._landing.find_one({"_id": LANDING_ID}) is not None:
            return
        legacy = self._landing.find_one({"_id": LEGACY_LANDING_ID})
        if legacy is None:
            return
        migrated = copy.deepcopy(legacy)
        migrated["_id"] = LANDING_ID
        self._landing.insert_one(migrated)

    def _seed_default_sites(self) -> None:
        now = iso(utcnow())
        for item in DEFAULT_SITES:
            self._sites.update_one(
                {"_id": item["site_id"]},
                {
                    "$setOnInsert": {
                        "name": item["name"],
                        "kind": item["kind"],
                        "domain": item.get("domain", ""),
                        "description": item.get("description", ""),
                        "status": item.get("status", "active"),
                        "theme": copy.deepcopy(item.get("theme", {})),
                        "created_at": now,
                        "updated_at": now,
                    }
                },
                upsert=True,
            )

    def _seed_default_landings(self) -> None:
        now = iso(utcnow())
        for item in DEFAULT_SITES:
            content = landing_default_for(item["site_id"], item["kind"])
            self._landing.update_one(
                {"_id": item["site_id"]},
                {
                    "$setOnInsert": {
                        "draft_content": copy.deepcopy(content),
                        "published_content": copy.deepcopy(content),
                        "updated_at": now,
                        "published_at": now,
                    }
                },
                upsert=True,
            )

    def _seed_default_ads(self) -> None:
        now = utcnow()
        result = self._meta.update_one(
            {"_id": "ads_seeded"},
            {"$setOnInsert": {"seeded_at": iso(now)}},
            upsert=True,
        )
        if result.upserted_id is None:
            return
        for item in DEFAULT_ADS:
            self.upsert_ad(Ad(
                ad_id=uuid7(),
                title=item["title"],
                subtitle=item["subtitle"],
                body=item["body"],
                cta_label=item["cta_label"],
                cta_url=item["cta_url"],
                image_url=item["image_url"],
                layout=item["layout"],
                theme=dict(item["theme"]),
                active=bool(item["active"]),
                created_at=now,
                updated_at=now,
            ))

    @staticmethod
    def _landing_doc(doc: dict | None) -> Optional[Landing]:
        if doc is None:
            return None
        return Landing(
            landing_id=doc["_id"],
            draft=copy.deepcopy(doc.get("draft_content") or {}),
            published=copy.deepcopy(doc.get("published_content")),
            updated_at=parse_iso(doc["updated_at"]),
            published_at=parse_iso(doc["published_at"]) if doc.get("published_at") else None,
        )

    @staticmethod
    def _ad_doc(doc: dict) -> Ad:
        return Ad(
            ad_id=doc["_id"],
            title=doc.get("title", ""),
            subtitle=doc.get("subtitle", ""),
            body=doc.get("body", ""),
            cta_label=doc.get("cta_label", ""),
            cta_url=doc.get("cta_url", ""),
            image_url=doc.get("image_url", ""),
            layout=doc.get("layout", "banner"),
            theme=copy.deepcopy(doc.get("theme") or {}),
            active=bool(doc.get("active", True)),
            created_at=parse_iso(doc["created_at"]) if doc.get("created_at") else None,
            updated_at=parse_iso(doc["updated_at"]) if doc.get("updated_at") else None,
        )

    @staticmethod
    def _site_doc(doc: dict) -> Site:
        return Site(
            site_id=doc["_id"],
            name=doc.get("name", ""),
            kind=doc.get("kind", "client"),
            domain=doc.get("domain", ""),
            description=doc.get("description", ""),
            status=doc.get("status", "active"),
            theme=copy.deepcopy(doc.get("theme") or {}),
            created_at=parse_iso(doc["created_at"]) if doc.get("created_at") else None,
            updated_at=parse_iso(doc["updated_at"]) if doc.get("updated_at") else None,
        )

    # ------------------------------------------------------------ sitios
    def list_sites(self) -> list[Site]:
        docs = self._sites.find().sort([("created_at", 1), ("_id", 1)])
        return [self._site_doc(doc) for doc in docs]

    def get_site(self, site_id: str) -> Optional[Site]:
        doc = self._sites.find_one({"_id": site_id})
        return self._site_doc(doc) if doc else None

    def upsert_site(self, site: Site) -> None:
        now = site.updated_at or utcnow()
        created = site.created_at or now
        self._sites.update_one(
            {"_id": site.site_id},
            {
                "$set": {
                    "name": site.name,
                    "kind": site.kind,
                    "domain": site.domain,
                    "description": site.description,
                    "status": site.status,
                    "theme": copy.deepcopy(site.theme or {}),
                    "updated_at": iso(now),
                },
                "$setOnInsert": {"created_at": iso(created)},
            },
            upsert=True,
        )

    def delete_site(self, site_id: str) -> bool:
        self._landing.delete_one({"_id": site_id})
        return self._sites.delete_one({"_id": site_id}).deleted_count > 0

    # ---------------------------------------------------------- landing
    def get_landing(self, site_id: str = LANDING_ID) -> Optional[Landing]:
        return self._landing_doc(self._landing.find_one({"_id": site_id}))

    def save_landing_draft(self, site_id: str, content: dict) -> Landing:
        now = iso(utcnow())
        self._landing.update_one(
            {"_id": site_id},
            {
                "$set": {
                    "draft_content": copy.deepcopy(content),
                    "updated_at": now,
                },
                "$setOnInsert": {"published_at": None},
            },
            upsert=True,
        )
        landing = self.get_landing(site_id)
        assert landing is not None
        return landing

    def publish_landing(self, site_id: str = LANDING_ID) -> Optional[Landing]:
        doc = self._landing.find_one({"_id": site_id})
        if doc is None:
            return None
        self._landing.update_one(
            {"_id": site_id},
            {
                "$set": {
                    "published_content": copy.deepcopy(doc.get("draft_content") or {}),
                    "published_at": iso(utcnow()),
                }
            },
        )
        return self.get_landing(site_id)

    def list_ads(self, only_active: bool = False) -> list[Ad]:
        query = {"active": True} if only_active else {}
        docs = self._ads.find(query).sort([("created_at", -1), ("_id", -1)])
        return [self._ad_doc(doc) for doc in docs]

    def get_ad(self, ad_id: str) -> Optional[Ad]:
        doc = self._ads.find_one({"_id": ad_id})
        return self._ad_doc(doc) if doc else None

    def upsert_ad(self, ad: Ad) -> None:
        now = ad.updated_at or utcnow()
        created = ad.created_at or now
        doc = {
            "title": ad.title,
            "subtitle": ad.subtitle,
            "body": ad.body,
            "cta_label": ad.cta_label,
            "cta_url": ad.cta_url,
            "image_url": ad.image_url,
            "layout": ad.layout,
            "theme": copy.deepcopy(ad.theme or {}),
            "active": bool(ad.active),
            "created_at": iso(created),
            "updated_at": iso(now),
        }
        self._ads.update_one({"_id": ad.ad_id}, {"$set": doc}, upsert=True)

    def delete_ad(self, ad_id: str) -> bool:
        return self._ads.delete_one({"_id": ad_id}).deleted_count > 0

    def ping(self) -> bool:
        try:
            self._db.command("ping")
            return True
        except Exception:
            return False

    def close(self) -> None:
        self._client.close()
