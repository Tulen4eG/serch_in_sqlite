"""
Модуль инициализации данных и синхронизации поисковых индексов.

Выполняет три последовательные задачи при старте контейнера:
1. Скачивает исходный массив данных
в формате CSV с публичного Яндекс.Диска.

2. Парсит CSV через Pandas и заливает данные
в реляционную БД SQLite (только если она пуста).

3. Синхронизирует и индексирует текстовые поля документов
в Elasticsearch через Bulk API.
"""

import ast
import json
import logging
import os
import urllib.parse

import pandas as pd
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sqlalchemy import create_engine, text


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

CSV_FILE_PATH = "posts.csv"
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = "posts_index"
# Маппинг индекса: явно подключаем встроенный русский аналайзер
INDEX_MAPPINGS = {
    "properties": {
        "id": {"type": "integer"},
        "text": {"type": "text", "analyzer": "russian"},
    }
}


def sqlite_url() -> str:
    """
    Удаляет префикс асинхронного драйвера 'aiosqlite',
    так как Pandas работает только в синхронном режиме.
    """
    raw_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fastapi.db")
    return raw_url.replace("sqlite+aiosqlite", "sqlite")


def download_yandex_disk_file(save_path: str) -> None:
    """
    Запрашивает прямую ссылку на скачивание через REST API Яндекс.Диска
    и скачивает публичный файл потоковым методом (stream=True).
    """
    public_url = "https://disk.360.yandex.ru/d/UYooXd9q2yqTMQ"
    base_api_url = (
        "https://cloud-api.yandex.net/v1/disk/public/resources/download?"
    )
    request_url = base_api_url + urllib.parse.urlencode(
        {"public_key": public_url}
    )

    try:
        response = requests.get(request_url, timeout=30)
        response.raise_for_status()
        download_url = response.json().get("href")

        if not download_url:
            logger.error("Не удалось получить прямую ссылку для скачивания.")
            return

        logger.info("Скачивание файла...")
        with requests.get(
                download_url, stream=True, timeout=120) as file_response:
            file_response.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info("Файл сохранён: %s", os.path.abspath(save_path))
    except requests.exceptions.RequestException:
        logger.exception("Ошибка при скачивании CSV")
        raise


def convert_to_python_list(val):
    """
    Безопасно преобразует строковое представление списка из CSV.
    """
    if isinstance(val, list):
        return json.dumps(val, ensure_ascii=False)
    try:
        parsed = ast.literal_eval(str(val))
        if isinstance(parsed, list):
            return json.dumps(parsed, ensure_ascii=False)
    except (ValueError, SyntaxError):
        logger.warning("Не удалось разобрать rubrics: %r", val)
    return "[]"


def posts_count(engine) -> int:
    """
    Возвращает текущее количество записей в таблице 'posts'.
    """
    with engine.connect() as conn:
        return int(
            conn.execute(text("SELECT COUNT(*) FROM posts")).scalar() or 0
        )


def load_sqlite(engine) -> None:
    """
    Выполняет чтение CSV-выгрузки, очистку типов данных через Pandas
    и пакетную вставку (to_sql) в базу данных SQLite.
    """
    logger.info("Читаю CSV...")
    df = pd.read_csv(CSV_FILE_PATH)
    # Модифицируем колонки под типы данных в SQLAlchemy-модели
    df["rubrics"] = df["rubrics"].apply(convert_to_python_list)
    df["created_date"] = pd.to_datetime(df["created_date"])
    logger.info("Записываю %s строк в SQLite...", len(df))
    # 'append' допишет строки, если таблица существует, или создаст её
    df.to_sql(name="posts", con=engine, if_exists="append", index=False)


def ensure_index(es: Elasticsearch) -> None:
    """
    Идемпотентная проверка существования поискового индекса в Elasticsearch.
    Создает индекс с русским аналайзером, если его не было.
    """
    if es.indices.exists(index=INDEX_NAME):
        return
    es.indices.create(index=INDEX_NAME, mappings=INDEX_MAPPINGS)


def es_doc_count(es: Elasticsearch) -> int:
    """
    Возвращает количество проиндексированных документов в Elasticsearch.
    """
    if not es.indices.exists(index=INDEX_NAME):
        return 0
    stats = es.count(index=INDEX_NAME)
    return int(stats.get("count", 0))


def reindex_from_sqlite(engine, es: Elasticsearch) -> None:
    """
    Выгружает идентификаторы и тексты из SQLite и производит
    высокопроизводительную bulk-индексацию документов в Elasticsearch.
    """
    db_data = pd.read_sql("SELECT id, text FROM posts", con=engine)
    if db_data.empty:
        return

    ensure_index(es)

    actions = (
        {
            "_index": INDEX_NAME,
            "_id": str(row.id),
            "_source": {
                "id": int(row.id),
                "text": str(row.text),
            },
        }
        for row in db_data.itertuples(index=False)
    )
    success, errors = bulk(es, actions, raise_on_error=False)
    if errors:
        logger.warning("Ошибки bulk-индексации: %s", errors)
    logger.info("Проиндексировано %s документов в Elasticsearch.", success)


def main():
    engine = create_engine(sqlite_url())
    es = Elasticsearch(ELASTICSEARCH_URL)

    # === СКАЧИВАНИЕ CSV ===
    if not os.path.exists(CSV_FILE_PATH):
        download_yandex_disk_file(CSV_FILE_PATH)

    # === ЗАГРУЗКА В SQLITE ===
    sqlite_rows = posts_count(engine)
    if sqlite_rows:
        logger.info("В SQLite уже %s постов, CSV не импортирую.", sqlite_rows)
    else:
        load_sqlite(engine)
        sqlite_rows = posts_count(engine)

    # === ИНДЕКСАЦИЯ В ELASTICSEARCH ===
    indexed = es_doc_count(es)
    if indexed == sqlite_rows and sqlite_rows > 0:
        logger.info(
            "Elasticsearch уже синхронизирован (%s документов).",
            indexed
        )
        return

    logger.info(
        "Переиндексация Elasticsearch (sqlite=%s, es=%s)...",
        sqlite_rows,
        indexed,
    )
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
    reindex_from_sqlite(engine, es)
    logger.info("Инициализация и синхронизация данных успешно завершена.")


if __name__ == "__main__":
    main()
