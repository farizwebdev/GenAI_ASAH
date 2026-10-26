"""Implementasi klien Google Gemini API menggunakan HTTP client dengan timeout dan retry."""

import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import (
    AITimeoutError,
    AIUnavailableError,
    QuotaExceededError,
)
from app.core.logging import get_logger
from app.llm.base import BaseLLMClient

logger = get_logger(__name__)


class GeminiLLMClient(BaseLLMClient):
    """Klien Gemini REST API dengan penanganan timeout, retry, dan pemetaan error."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_s: float | None = None,
        enable_cache: bool = True,
        max_retries: int = 2,
    ) -> None:
        super().__init__(timeout_s=timeout_s, enable_cache=enable_cache)
        settings = get_settings()
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL or "gemini-1.5-flash"
        self.max_retries = max_retries
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )

    def _call_model(self, prompt: str, system_instruction: str | None = None) -> str:
        if not self.api_key or not self.api_key.strip():
            raise AIUnavailableError(
                message_user="Layanan asisten AI belum dikonfigurasi.",
                message_dev="LLM_API_KEY kosong di file .env",
            )

        # Siapkan payload REST API Gemini
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        payload: dict[str, Any] = {"contents": contents}

        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_s) as client:
                    resp = client.post(self.endpoint, json=payload, headers=headers)

                # Cek HTTP Status
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise AIUnavailableError(
                            message_user="Asisten tidak dapat menghasilkan jawaban.",
                            message_dev="Respons Gemini kosong (tidak ada candidates)",
                        )
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts or "text" not in parts[0]:
                        raise AIUnavailableError(
                            message_user="Asisten tidak dapat menghasilkan jawaban.",
                            message_dev="Respons Gemini tidak memuat teks",
                        )
                    return parts[0]["text"]

                if resp.status_code == 429:
                    raise QuotaExceededError(
                        message_user="Batas kuota asisten tercapai. Silakan coba kembali nanti.",
                        message_dev=f"Gemini API rate limit/quota exceeded: {resp.text}",
                    )

                if resp.status_code in (500, 502, 503, 504):
                    # Transient error, berhak retry
                    raise httpx.HTTPStatusError(
                        f"Server error {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )

                # Error client lainnya (misal 400 Bad Request)
                raise AIUnavailableError(
                    message_user="Layanan asisten mengalami gangguan teknis.",
                    message_dev=f"Gemini HTTP {resp.status_code}: {resp.text}",
                )

            except (httpx.TimeoutException, AITimeoutError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait_time = 0.5 * (2**attempt)
                    logger.warning(
                        f"Timeout LLM ke-{attempt + 1}. Coba lagi dlm {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    raise AITimeoutError(
                        message_user="Asisten sedang sibuk. Silakan isi pesanan manual.",
                        message_dev=(
                            f"LLM timeout melebihi batas {self.timeout_s}s "
                            f"setelah {self.max_retries}x retry"
                        ),
                    ) from exc

            except (httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait_time = 0.5 * (2**attempt)
                    logger.warning(
                        f"Koneksi LLM gagal ke-{attempt + 1}. Coba lagi dlm {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    raise AIUnavailableError(
                        message_user=(
                            "Layanan asisten AI sedang tidak dapat diakses. "
                            "Silakan hubungi pegawai toko."
                        ),
                        message_dev=(
                            f"Koneksi Gemini gagal setelah {self.max_retries}x retry: {exc}"
                        ),
                    ) from exc

        raise AIUnavailableError(
            message_user=(
                "Layanan asisten AI sedang tidak dapat diakses. Silakan hubungi pegawai toko."
            ),
            message_dev=f"Gemini call gagal: {last_error}",
        )
