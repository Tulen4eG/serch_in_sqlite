import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from elasticsearch import AsyncElasticsearch, NotFoundError
from typing import List

from app.models import Posts


ELASTIC_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
es_client = AsyncElasticsearch(ELASTIC_URL)
INDEX_NAME = "posts_index"


class CRUDPosts:
    async def remove(self, db_obj: Posts, session: AsyncSession) -> Posts:
        """
        Удаляет переданный объект из базы данных.
        """
        await session.delete(db_obj)
        await session.commit()
        try:
            await es_client.delete(index=INDEX_NAME, id=str(db_obj.id))
            print(f"Документ {db_obj.id} успешно удален из Elasticsearch.")
        except NotFoundError:
            print(f"Предупреждение: Id {db_obj.id} не найден в Elasticsearch.")
        return db_obj

    async def search(self, query: str, session: AsyncSession) -> List[Posts]:
        """
        Полнотекстовый поиск по Elasticsearch с получением
        полных и отсортированных данных из SQLite.
        """
        es_result = await es_client.search(
            index=INDEX_NAME,
            query={
                "match": {
                    "text": query
                }
            },
            size=1500,
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
