"""
Модуль реализации Create, Read, Update, Delete для постов.

Инкапсулирует в себе всю сложную гибридную логику одновременной работы
с реляционной базой данных SQLite и поисковым движком Elasticsearch.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from elasticsearch import NotFoundError
from typing import List

from app.core import settings, es_client
from app.models import Posts


logger = logging.getLogger(__name__)

# Размер выборки из Elastic. Берется с запасом, так как итоговая 
# сортировка по дате и фильтрация лимита происходят на стороне SQLite
ES_SEARCH_SIZE = 1500


class CRUDPosts:
    """
    Класс управления бизнес-логикой постов.
    """
    async def remove(self, db_obj: Posts, session: AsyncSession) -> Posts:
        """
        Удаляет переданный объект из базы данных.
        """
        await session.delete(db_obj)
        # flush отправляет SQL-запрос DELETE в базу,
        # но не фиксирует его намертво.
        # Это позволяет заблокировать строку,
        # пока мы работаем с Elasticsearch
        await session.flush()
        try:
            # Пытаемся удалить зеркальный документ из индекса Elasticsearch
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
            # Критический сбой: откатываем SQLite назад
            await session.rollback()
            logger.exception(
                "Не удалось удалить документ %s из Elasticsearch",
                db_obj.id,
            )
            raise
        # Если всё прошло успешно, коммитим изменения в SQLite
        await session.commit()
        return db_obj

    async def search(self, query: str, session: AsyncSession) -> List[Posts]:
        """
        Полнотекстовый поиск по Elasticsearch с получением
        до 20 новейших и отсортированных по дате постов из SQLite.
        """
        # Полнотекстовый поиск в Elasticsearch
        es_result = await es_client.search(
            index=settings.elasticsearch_index,
            query={"match": {"text": query}},
            size=ES_SEARCH_SIZE,
        )

        # Извлекаем строковые идентификаторы документов
        # и приводим их к целым числам для SQLite
        hits = es_result["hits"]["hits"]
        if not hits:
            return []
        post_ids = [int(hit["_id"]) for hit in hits]

        # Выборка оригинальных записей из SQLite с сортировкой по новизне
        db_query = (
            select(Posts)
            .where(Posts.id.in_(post_ids))
            .order_by(Posts.created_date.desc())
            .limit(20)
        )

        result = await session.execute(db_query)
        return result.scalars().all()


posts_crud = CRUDPosts()
