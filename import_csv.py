from dotenv import load_dotenv
import ast
import json
import os
import pandas as pd
from elasticsearch import Elasticsearch
from sqlalchemy import create_engine
import urllib.parse
import requests


load_dotenv()


raw_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./fastapi.db")
if ":///" in raw_url:
    clean_path = raw_url.split(":///")[-1]
    DB_URL = f"sqlite:///{clean_path}"

DB_URL = os.environ["DATABASE_URL"].replace("sqlite+aiosqlite", "sqlite")
CSV_FILE_PATH = "posts.csv"
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = "posts_index"
PUBLIC_LINK = "https://disk.360.yandex.ru/d/UYooXd9q2yqTMQ"
OUTPUT_FILENAME = "posts.csv"


def download_yandex_disk_file(public_url, save_path):
    base_api_url = (
        "https://cloud-api.yandex.net/v1/disk/public/resources/download?"
    )
    request_url = base_api_url + urllib.parse.urlencode(
        {"public_key": public_url}
    )

    try:
        response = requests.get(request_url)
        response.raise_for_status()
        download_url = response.json().get("href")

        if not download_url:
            print("Не удалось получить прямую ссылку для скачивания.")
            return

        print("Скачивание файла...")
        with requests.get(download_url, stream=True) as file_response:
            file_response.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(
            f"Файл успешно скачан и сохранен как: {os.path.abspath(save_path)}"
        )

    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка при скачивании: {e}")


def convert_to_json(val):
    try:
        lst = ast.literal_eval(str(val))
        return json.dumps(lst)
    except Exception:
        return "[]"


def main():
    if not os.path.exists(CSV_FILE_PATH):
        download_yandex_disk_file(PUBLIC_LINK, CSV_FILE_PATH)

    # === ЗАГРУЗКА В SQLITE ===
    print("1. Читаю и подготавливаю CSV...")
    df = pd.read_csv(CSV_FILE_PATH)

    df["rubrics"] = df["rubrics"].apply(convert_to_json)

    print("2. Записываю данные в SQLite...")
    engine = create_engine(DB_URL)
    df.to_sql(name="posts", con=engine, if_exists="append", index=False)
    print("Данные успешно сохранены в SQLite!")

    # === ИНДЕКСАЦИЯ В ELASTICSEARCH ===
    print("3. Подключаюсь к Elasticsearch...")
    es = Elasticsearch(
        ELASTICSEARCH_URL
    )

    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(
            index=INDEX_NAME,
            mappings={
                "properties": {
                    "id": {"type": "integer"},
                    "text": {"type": "text", "analyzer": "russian"},
                }
            },
        )

    print("4. Переношу тексты в поисковый индекс...")
    db_data = pd.read_sql("SELECT id, text FROM posts", con=engine)

    for _, row in db_data.iterrows():
        es.index(
            index=INDEX_NAME,
            id=str(row["id"]),
            document={"id": int(row["id"]), "text": str(row["text"])},
        )

    print(
        f"Все {len(db_data)} записей проиндексированы в Elasticsearch."
    )


if __name__ == "__main__":
    main()
