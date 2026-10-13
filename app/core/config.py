from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = "Поисковик данных SQLite"
    description: str = "Сервис для поиска по базе данных SQLite"
    database_url: str = "sqlite+aiosqlite:///./fastapi.db"
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "posts_index"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
