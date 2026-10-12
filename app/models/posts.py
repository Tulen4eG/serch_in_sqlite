from sqlalchemy import Column, String, JSON

from app.core.db import Base


class Posts(Base):
    rubrics = Column(JSON, nullable=False)
    text = Column(String(250), nullable=False)
    created_date = Column(String(19), nullable=False)
