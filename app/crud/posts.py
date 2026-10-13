import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from elasticsearch import NotFoundError
from typing import List

from app.core import settings, es_client
from app.models import Posts


logger = logging.getLogger(__name__)

ES_SEARCH_SIZE = 1500


class CRUDPosts:
    async def remove(self, db_obj: Posts, session: AsyncSession) -> Posts:
        """
        Удаляет переданный объект из базы данных.
        """
        await session.delete(db_obj)
        await session.flush()
        try:
            await es_client.delete(
                index=settings.elasticsearch_index,
                id=str(db_obj.id)
            )
        except NotFoundError:
            logger.warning(
                "Документ %s удалён из БД, в Elasticsearch его не было",
                db_obj.id,
            )
        except Exception:
            await session.rollback()
            logger.exception(
                "Не удалось удалить документ %s из Elasticsearch",
                db_obj.id,
            )
            raise
        await session.commit()
        return db_obj

    async def search(self, query: str, session: AsyncSession) -> List[Posts]:
        """
        Полнотекстовый поиск по Elasticsearch с получением
        до 20 новейших и отсортированных по дате постов из SQLite.
        """
        es_result = await es_client.search(
            index=settings.elasticsearch_index,
            query={"match": {"text": query}},
            size=ES_SEARCH_SIZE,
        )

        hits = es_result["hits"]["hits"]
        if not hits:
            return []
        post_ids = [int(hit["_id"]) for hit in hits]

        db_query = (
            select(Posts)
            .where(Posts.id.in_(post_ids))
            .order_by(Posts.created_date.desc())
            .limit(20)
        )

        result = await session.execute(db_query)
        return result.scalars().all()


posts_crud = CRUDPosts()
