"""Fábrica de persistencia: MongoDB si hay URI, SQLite en caso contrario."""
from __future__ import annotations

from .config import Settings
from .mongo_repository import MongoPostRepository
from .repository import PostRepository
from .sqlite_repository import SqlitePostRepository


def build_repository(settings: Settings) -> PostRepository:
    if settings.mongo_uri:
        return MongoPostRepository(settings.mongo_uri, settings.mongo_db)
    return SqlitePostRepository(settings.db_path)
