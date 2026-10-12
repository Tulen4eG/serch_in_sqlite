from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Posts


async def check_post_before_delete(
        post_id: int, session: AsyncSession) -> Posts:
    db_post = await session.get(Posts, post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пост с id {post_id} не найден!"
        )
    return db_post
