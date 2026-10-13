"""
Модуль описания ORM-моделей для работы с базой данных SQLite.
Определяет структуру таблиц и типы данных для хранения постов.
"""

from sqlalchemy import Column, JSON, Text, DateTime

from app.core import Base


class Posts(Base):
    rubrics = Column(JSON, nullable=False)
    text = Column(Text, nullable=False)
    created_date = Column(DateTime, nullable=False)
