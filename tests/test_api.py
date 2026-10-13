from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.models import Posts
from tests.conftest import TestSessionLocal


async def create_posts():
    posts = [
        Posts(
            id=1,
            rubrics=["news"],
            text="Python разработка backend",
            created_date=datetime(2024, 1, 1, 10, 0, 0),
        ),
        Posts(
            id=2,
            rubrics=["technology"],
            text="Python и Elasticsearch",
            created_date=datetime(2024, 2, 1, 10, 0, 0),
        ),
        Posts(
            id=3,
            rubrics=["programming"],
            text="FastAPI приложение на Python",
            created_date=datetime(2024, 3, 1, 10, 0, 0),
        ),
    ]

    async with TestSessionLocal() as session:
        session.add_all(posts)
        await session.commit()


@pytest.mark.asyncio
async def test_search_returns_posts(client):
    await create_posts()

    es_response = {
        "hits": {
            "hits": [
                {"_id": "1"},
                {"_id": "2"},
                {"_id": "3"},
            ]
        }
    }

    with patch(
        "app.crud.posts.es_client.search",
        new_callable=AsyncMock,
        return_value=es_response,
    ) as mock_search:
        response = await client.get("/search", params={"query": "Python"})

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 3
    assert [post["id"] for post in data] == [3, 2, 1]

    mock_search.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_returns_max_20_posts(client):
    posts = [
        Posts(
            id=i,
            rubrics=["test"],
            text=f"Post {i}",
            created_date=datetime(2024, 1, 1),
        )
        for i in range(1, 26)
    ]

    async with TestSessionLocal() as session:
        session.add_all(posts)
        await session.commit()

    es_response = {
        "hits": {
            "hits": [{"_id": str(i)} for i in range(1, 26)]
        }
    }

    with patch(
        "app.crud.posts.es_client.search",
        new_callable=AsyncMock,
        return_value=es_response,
    ):
        response = await client.get("/search", params={"query": "Python"})

    assert response.status_code == 200
    assert len(response.json()) == 20


@pytest.mark.asyncio
async def test_search_returns_empty_list(client):
    es_response = {"hits": {"hits": []}}

    with patch(
        "app.crud.posts.es_client.search",
        new_callable=AsyncMock,
        return_value=es_response,
    ):
        response = await client.get(
            "/search",
            params={"query": "unknown"},
        )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_search_requires_query(client):
    response = await client.get("/search")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_post(client):
    await create_posts()

    with patch(
        "app.crud.posts.es_client.delete",
        new_callable=AsyncMock,
    ) as mock_delete:
        response = await client.delete("/delete/1")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Пост с ID 1 успешно удален."
    }
    mock_delete.assert_awaited_once()

    async with TestSessionLocal() as session:
        deleted_post = await session.get(Posts, 1)
        assert deleted_post is None


@pytest.mark.asyncio
async def test_delete_nonexistent_post(client):
    response = await client.delete("/delete/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Пост с id 999 не найден!"
    }
