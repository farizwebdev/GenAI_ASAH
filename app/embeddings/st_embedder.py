"""Implementasi Embedder lokal menggunakan pustaka Sentence Transformers."""

from typing import Any

from app.core.config import get_settings
from app.core.errors import AIUnavailableError
from app.core.logging import get_logger
from app.embeddings.base import BaseEmbedder

logger = get_logger(__name__)


class SentenceTransformerEmbedder(BaseEmbedder):
    """Embedder berbasis model lokal menggunakan SentenceTransformer."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = (
            model_name or settings.EMBED_MODEL or "paraphrase-multilingual-MiniLM-L12-v2"
        )
        self._model: Any = None
        self._dimension: int = 384

    def _ensure_model_loaded(self) -> None:
        """Memuat model SentenceTransformer secara malas (lazy loading)."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Memuat model embedding lokal: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            dim = self._model.get_sentence_embedding_dimension()
            if dim:
                self._dimension = int(dim)
        except ImportError as exc:
            raise AIUnavailableError(
                message_user="Model embedding lokal belum dapat dijalankan.",
                message_dev=(
                    "Pustaka 'sentence-transformers' belum terpasang. "
                    "Gunakan EMBEDDER=fake untuk mode uji."
                ),
            ) from exc
        except Exception as exc:
            raise AIUnavailableError(
                message_user="Gagal menginisialisasi model embedding lokal.",
                message_dev=f"Gagal memuat SentenceTransformer '{self.model_name}': {exc}",
            ) from exc

    @property
    def dimension(self) -> int:
        self._ensure_model_loaded()
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        self._ensure_model_loaded()
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self._ensure_model_loaded()
        vecs = self._model.encode(texts, normalize_embeddings=True)
        return vecs.tolist()
