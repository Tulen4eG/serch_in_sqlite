from datetime import datetime as dt

from pydantic import BaseModel, Field, ConfigDict


class PostsSchema(BaseModel):
    id: int = Field(
        title="ID поста",
        description="Уникальный идентификатор поста в базе данных",
    )
    rubrics: list[str] = Field(
        title="Рубрики",
        description="Список рубрик, к которым относится текст",
    )
    text: str = Field(
        title="Текст",
        description="Текст, по которому будет осуществляться поиск",
    )
    created_date: dt = Field(
        title="Дата создания",
        description="Дата создания текста в формате YYYY-MM-DD HH:MM:SS",
    )

    model_config = ConfigDict(
        title="Модель данных с постами",
        from_attributes=True,
        json_schema_extra={
           "example": {
               "id": 1,
               "created_date": "2019-07-25 12:42:13",
               "text": "Пример текста",
               "rubrics": [
                   "VK-1603736028819866",
                   "VK-11879320040",
                   "VK-63192684938"
                ]
           }
        }
    )


class DeletePostSchema(BaseModel):
    message: str = Field(
        title="Сообщение об успешном удалении",
        example="Пост с ID 5 успешно удален."
    )
