from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import main_router
from app.core import settings, close_es_client


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await close_es_client()


app = FastAPI(
    title=settings.app_title,
    description=settings.description,
    lifespan=lifespan,
)

app.include_router(main_router)
