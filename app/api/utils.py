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

ERROR_DELETE_RESPONSES = {
    "404": {
        "description": "Объект не найден в базе данных SQLite",
        "content": {
            "application/json": {
                "example": {"detail": "Пост с id 42 не найден!"}
            }
        }
    },
    "503": {
        "description": "Поисковый сервис (Elasticsearch) недоступен",
        "content": {
            "application/json": {
                "example": {"detail": "Поисковый сервис временно недоступен"}
            }
        }
    }
}

ERROR_SEARCH_RESPONSES = {
    "503": {"description": "Elasticsearch недоступен"},
}
