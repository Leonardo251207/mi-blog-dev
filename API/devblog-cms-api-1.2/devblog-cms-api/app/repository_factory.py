"""Fábrica de persistencia: MongoDB si hay URI, SQLite en caso contrario."""
from __future__ import annotations

from .config import Settings
from .content_repository import (ContentRepository, MongoContentRepository,
                                 SqliteContentRepository)
from .mongo_repository import MongoPostRepository
from .repository import PostRepository
from .sqlite_repository import SqlitePostRepository


def build_repository(settings: Settings) -> PostRepository:
    if settings.mongo_uri:
        return MongoPostRepository(settings.mongo_uri, settings.mongo_db)
    return SqlitePostRepository(settings.db_path)


def build_content_repository(settings: Settings) -> ContentRepository:
    """Landing y publicidad usan el mismo motor que los posts."""
    if settings.mongo_uri:
        return MongoContentRepository(settings.mongo_uri, settings.mongo_db)
    return SqliteContentRepository(settings.db_path)
