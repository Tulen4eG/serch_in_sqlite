"""
Модуль обработки API-запросов для полнотекстового поиска постов.
Включает интеграцию с Elasticsearch и валидацию ответов.
"""

from typing import List

from elasticsearch import (
    ApiError,
    ConnectionError as ESConnectionError,
    TransportError
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import ERROR_SEARCH_RESPONSES
from app.core import get_async_session
from app.crud import posts_crud
from app.schemas import PostsSchema


router = APIRouter()


@router.get(
        "/search",
        response_model=List[PostsSchema],
        summary="Поиск постов по тексту",
        responses=ERROR_SEARCH_RESPONSES
)
async def search_posts(
    query: str = Query(..., min_length=1, description="Текстовый запрос"),
    session: AsyncSession = Depends(get_async_session)
) -> List[PostsSchema]:
    """
    Поиск постов по тексту с использованием Elasticsearch и SQLite.
    Возвращает до 20 записей со всеми полями БД, от новых к старым.

    - **param query**: Строка запроса для поиска.
    """
    try:
        return await posts_crud.search(query, session)
    except (ApiError, ESConnectionError, TransportError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Поисковый сервис временно недоступен",
        ) from exc
