"""Contexto de la superficie GraphQL."""

from __future__ import annotations

from dataclasses import dataclass

from strawberry.fastapi import BaseContext

from app.bootstrap.container import Container


@dataclass
class Context(BaseContext):
    container: Container
    admin: bool
