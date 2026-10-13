from elasticsearch import (
    ApiError,
    ConnectionError as ESConnectionError,
    TransportError
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import check_post_before_delete, ERROR_DELETE_RESPONSES
from app.core import get_async_session
from app.crud import posts_crud
from app.schemas import DeletePostSchema


router = APIRouter()


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=DeletePostSchema,
    summary="Удаление поста",
    responses=ERROR_DELETE_RESPONSES
)
async def delete_post(
    post_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> DeletePostSchema:
    """
    Удаляет документ из SQLite и из индекса Elasticsearch по id.

    - **param post_id**: ID поста для удаления.
    """
    db_post = await check_post_before_delete(post_id, session)
    try:
        await posts_crud.remove(db_post, session)
    except (ApiError, ESConnectionError, TransportError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Поисковый сервис недоступен",
        ) from exc
    return DeletePostSchema(message=f"Пост с ID {post_id} успешно удален.")
