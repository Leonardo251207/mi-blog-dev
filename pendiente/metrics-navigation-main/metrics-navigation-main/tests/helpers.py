from __future__ import annotations

from httpx import AsyncClient

TEST_KEY = "pk_live_test_00000000000000000000000000000000"
TEST_ADMIN = "test-admin"


async def graphql(
    client: AsyncClient,
    query: str,
    variables: dict | None = None,
    admin: bool = True,
):
    headers = {"X-Admin-Key": TEST_ADMIN} if admin else {}
    return await client.post(
        "/v1/query",
        json={"query": query, "variables": variables or {}},
        headers=headers,
    )
