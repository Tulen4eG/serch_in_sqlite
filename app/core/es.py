"""
Модуль инициализации асинхронного клиента Elasticsearch.

Интегрирует поисковый движок в единый жизненный цикл приложения FastAPI.
"""

from elasticsearch import AsyncElasticsearch

from app.core.config import settings


es_client = AsyncElasticsearch(settings.elasticsearch_url)


async def close_es_client() -> None:
    """
    Безопасно разрывает соединение с Elasticsearch.
    Вызывается при штатной остановке веб-сервера.
    """
    await es_client.close()
