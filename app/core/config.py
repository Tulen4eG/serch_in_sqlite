from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_title: str = "Поисковик данных SQLite"
    description: str = "Сервис для поиска по базе данных SQLite"
    database_url: str = "sqlite+aiosqlite:///./fastapi.db"

    class Config:
        env_file = ".env"


settings = Settings()
