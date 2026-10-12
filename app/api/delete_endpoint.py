from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from .utills import check_post_before_delete
from app.core import get_async_session
from app.crud import posts_crud
from app.schemas import DeletePostSchema


router = APIRouter()


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=DeletePostSchema,
    summary="Удаление поста"
)
async def delete_post(
    post_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> DeletePostSchema:
    """
    Удаление поста по его ID.

    - **param post_id**: ID поста для удаления.
    """
    db_post = await check_post_before_delete(post_id, session)
    await posts_crud.remove(db_post, session)
    return DeletePostSchema(message=f"Пост с ID {post_id} успешно удален.")
