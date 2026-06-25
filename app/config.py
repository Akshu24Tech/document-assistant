from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/text-embedding-004"
    log_level: str = "INFO"
    app_name: str = "Document Assistant API"

    # optional shared secret. when set, every API endpoint needs the X-API-Key header.
    api_key: str = ""

    # where chroma and the chat-history db live
    data_dir: str = "data"
    chroma_dir: str = "data/chroma"
    history_db: str = "data/history.db"

    # chunking knobs (characters, not tokens — keeps it simple and predictable)
    chunk_size: int = 1000
    chunk_overlap: int = 150

    # how many chunks to pull into the answer prompt
    top_k: int = 4


@lru_cache
def get_settings() -> Settings:
    # cached so we don't re-read the .env on every request
    return Settings()
