"""Esquema GraphQL: consulta y administración."""

from __future__ import annotations

import strawberry

from app.entrypoints.query.graphql.mutations import Mutation
from app.entrypoints.query.graphql.queries import Query

schema = strawberry.Schema(query=Query, mutation=Mutation)
