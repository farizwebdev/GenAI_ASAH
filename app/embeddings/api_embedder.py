"""Implementasi Embedder berbasis API eksternal (contoh: Gemini text-embedding-004)."""

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import (
    AITimeoutError,
    AIUnavailableError,
    QuotaExceededError,
)
from app.embeddings.base import BaseEmbedder


class APIEmbedder(BaseEmbedder):
    """Embedder yang memanggil REST API embedding eksternal."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_s: float = 10.0,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.EMBED_MODEL or "text-embedding-004"
        self.timeout_s = timeout_s
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:embedContent"
        )
        self._dim = 768

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        if not self.api_key or not self.api_key.strip():
            raise AIUnavailableError(
                message_user="Layanan embedding API belum dikonfigurasi.",
                message_dev="LLM_API_KEY kosong di file .env untuk APIEmbedder",
            )

        payload: dict[str, Any] = {
            "model": f"models/{self.model}",
            "content": {"parts": [{"text": text}]},
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                resp = client.post(self.endpoint, json=payload, headers=headers)

            if resp.status_code == 200:
                data = resp.json()
                values = data.get("embedding", {}).get("values", [])
                if values:
                    self._dim = len(values)
                    return values
                raise AIUnavailableError(
                    message_user="Gagal mendapatkan embedding teks.",
                    message_dev="Respon API embedding tidak memuat values",
                )

            if resp.status_code == 429:
                raise QuotaExceededError(
                    message_user="Batas kuota embedding tercapai.",
                    message_dev="Embedding API rate limit/quota exceeded",
                )

            raise AIUnavailableError(
                message_user="Layanan embedding API mengalami gangguan.",
                message_dev=f"Embedding API HTTP {resp.status_code}: {resp.text}",
            )

        except httpx.TimeoutException as exc:
            raise AITimeoutError(
                message_user="Layanan embedding melebihi batas waktu.",
                message_dev=f"Embedding API timeout setelah {self.timeout_s}s",
            ) from exc
        except (httpx.NetworkError, httpx.HTTPError) as exc:
            raise AIUnavailableError(
                message_user="Tidak dapat terhubung ke penyedia embedding API.",
                message_dev=f"Koneksi embedding gagal: {exc}",
            ) from exc

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
