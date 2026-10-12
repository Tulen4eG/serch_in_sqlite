from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core import get_async_session
from app.crud import posts_crud
from app.schemas import PostsSchema


router = APIRouter()


@router.get(
        "/search",
        response_model=List[PostsSchema],
        summary="Поиск постов по тексту"
)
async def search_posts(
    query: str, session: AsyncSession = Depends(get_async_session)
) -> List[PostsSchema]:
    """
    Поиск постов по тексту с использованием Elasticsearch и SQLite.
    Возвращает список постов, соответствующих запросу.

    - **param query**: Строка запроса для поиска.
    """
    return await posts_crud.search(query, session)
