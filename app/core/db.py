"""
Модуль инициализации асинхронного движка SQLAlchemy и управления сессиями.

Отвечает за генерацию сессий базы данных для каждого входящего HTTP-запроса.
"""

from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, declared_attr

from app.core.config import settings


class PreBase:
    """
    Базовый класс-миксин для автоматического формирования метаданных таблиц.
    """

    @declared_attr
    def __tablename__(cls):
        """
        Генерирует имя таблицы на основе имени класса в нижнем регистре.
        Например: класс модели 'Posts' создаст таблицу 'posts'.
        """
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)


Base = declarative_base(cls=PreBase)

engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session():
    """
    Генератор асинхронных сессий.
    """
    async with AsyncSessionLocal() as session:
        yield session
