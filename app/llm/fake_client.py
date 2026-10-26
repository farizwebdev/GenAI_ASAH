"""Implementasi Fake LLM Client untuk pengujian unit tanpa koneksi jaringan."""

from app.core.errors import (
    AITimeoutError,
    AIUnavailableError,
    QuotaExceededError,
)
from app.llm.base import BaseLLMClient


class FakeLLMClient(BaseLLMClient):
    """Klien LLM palsu (mock/stub) dengan respons terprogram untuk pengujian deterministik."""

    def __init__(
        self,
        default_response: str = '{"status": "ok", "message": "Fake LLM Response"}',
        timeout_s: float | None = None,
        enable_cache: bool = True,
    ) -> None:
        super().__init__(timeout_s=timeout_s, enable_cache=enable_cache)
        self.default_response = default_response
        self._responses: dict[str, str] = {}

        # Flag simulasi error untuk testing skenario gagal
        self.simulate_timeout: bool = False
        self.simulate_quota_exceeded: bool = False
        self.simulate_unavailable: bool = False
        self.simulate_invalid_json: bool = False
        self.call_count: int = 0

    def register_response(self, keyword_or_prefix: str, response: str) -> None:
        """Mendaftarkan respons tertentu bila prompt mengandung kata kunci tersebut."""
        self._responses[keyword_or_prefix] = response

    def clear_registered_responses(self) -> None:
        """Menghapus semua respons kustom terdaftar."""
        self._responses.clear()

    def _call_model(self, prompt: str, system_instruction: str | None = None) -> str:
        self.call_count += 1

        # Simulasi error jika diaktifkan
        if self.simulate_timeout:
            raise AITimeoutError(
                message_user="Asisten sedang sibuk. Silakan isi pesanan manual.",
                message_dev=f"Simulasi LLM timeout setelah {self.timeout_s}s",
            )
        if self.simulate_quota_exceeded:
            raise QuotaExceededError(
                message_user="Batas kuota asisten tercapai. Silakan coba kembali nanti.",
                message_dev="Simulasi LLM kuota habis (429)",
            )
        if self.simulate_unavailable:
            raise AIUnavailableError(
                message_user=(
                    "Layanan asisten AI sedang tidak dapat diakses. "
                    "Silakan hubungi pegawai toko."
                ),
                message_dev="Simulasi layanan LLM mati (503)",
            )
        if self.simulate_invalid_json:
            return "Maaf, respon ini sengaja bukan format JSON valid {{"

        # Cek apakah ada respons kustom yang cocok dengan prompt
        for key, response in self._responses.items():
            if key in prompt:
                return response

        return self.default_response
