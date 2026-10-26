"""Konfigurasi aplikasi berbasis environment variables menggunakan Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pengaturan utama layanan Gen AI Sabana Adventure Jombor."""

    # Keamanan dan Autentikasi
    SERVICE_API_KEY: str = "ganti_dengan_kunci_layanan"

    # LLM Settings
    LLM_PROVIDER: str = "fake"  # gemini | fake
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""
    LLM_TIMEOUT_S: float = 10.0

    # Embedding & Vector Store
    EMBEDDER: str = "fake"  # st | api | fake
    EMBED_MODEL: str = ""
    VECTOR_STORE: str = "chroma"  # chroma | faiss

    # Threshold & Guardrails
    INTENT_MIN_CONF: float = 0.5
    RAG_MIN_SCORE: float = 0.35

    # Waktu & Lokalisasi
    TIMEZONE: str = "Asia/Jakarta"
    SEED: int = 42
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Mengambil instance konfigurasi singleton dengan cache."""
    return Settings()
