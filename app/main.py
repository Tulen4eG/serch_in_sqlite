"""
Главный модуль запуска веб-сервера FastAPI.

Конфигурирует основной инстанс приложения, подключает роутеры 
и управляет событиями жизненного цикла (lifespan) приложения.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import main_router
from app.core import settings, close_es_client


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    # Очистка ресурсов при выключении сервера
    await close_es_client()


app = FastAPI(
    title=settings.app_title,
    description=settings.description,
    lifespan=lifespan,
)

app.include_router(main_router)
