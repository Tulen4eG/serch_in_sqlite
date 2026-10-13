from elasticsearch import AsyncElasticsearch

from app.core.config import settings


es_client = AsyncElasticsearch(settings.elasticsearch_url)


async def close_es_client() -> None:
    await es_client.close()
