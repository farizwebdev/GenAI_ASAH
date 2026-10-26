"""Antarmuka dasar (Interface) untuk klien Large Language Model (LLM)."""

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.json_utils import clean_and_parse_json

logger = get_logger(__name__)


class LLMCache:
    """In-memory LRU Cache sederhana untuk menyimpan hasil pemanggilan LLM identik."""

    def __init__(self, capacity: int = 128) -> None:
        self.capacity = capacity
        self.cache: OrderedDict[tuple[str, str | None], str] = OrderedDict()

    def get(self, prompt: str, system_instruction: str | None) -> str | None:
        key = (prompt, system_instruction)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, prompt: str, system_instruction: str | None, value: str) -> None:
        key = (prompt, system_instruction)
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def clear(self) -> None:
        self.cache.clear()


class BaseLLMClient(ABC):
    """Kelas dasar abstrak untuk semua implementasi LLM (Gemini, Fake, dll)."""

    def __init__(self, timeout_s: float | None = None, enable_cache: bool = True) -> None:
        settings = get_settings()
        self.timeout_s = timeout_s or settings.LLM_TIMEOUT_S
        self.enable_cache = enable_cache
        self._cache = LLMCache() if enable_cache else None

    @abstractmethod
    def _call_model(self, prompt: str, system_instruction: str | None = None) -> str:
        """Eksekusi pemanggilan langsung ke provider model AI spesifik."""
        pass

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        """Menghasilkan teks dari prompt dengan dukungan caching dan penanganan error.

        Args:
            prompt: Pesan utama yang dikirim ke LLM.
            system_instruction: Instruksi sistem (role / persona / panduan).

        Returns:
            str: Teks hasil generasi dari LLM.
        """
        # Cek Cache
        if self._cache:
            cached = self._cache.get(prompt, system_instruction)
            if cached is not None:
                logger.debug("LLM cache hit untuk prompt yang sama.")
                return cached

        # Panggilan model aktual
        result = self._call_model(prompt, system_instruction)

        # Simpan ke Cache
        if self._cache:
            self._cache.put(prompt, system_instruction, result)

        return result

    def generate_json(
        self, prompt: str, system_instruction: str | None = None
    ) -> dict[str, Any]:
        """Menghasilkan output teks dan mem-parse-nya menjadi objek JSON/dict."""
        raw_text = self.generate(prompt, system_instruction)
        return clean_and_parse_json(raw_text)


def get_llm_client() -> BaseLLMClient:
    """Factory function untuk mendapatkan instance klien LLM berdasarkan .env."""
    settings = get_settings()
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "gemini":
        from app.llm.gemini_client import GeminiLLMClient

        return GeminiLLMClient()

    # Default fallback / provider uji
    from app.llm.fake_client import FakeLLMClient

    return FakeLLMClient()
