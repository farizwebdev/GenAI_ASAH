"""Antarmuka dasar (Interface) untuk model embedding representasi teks."""

from abc import ABC, abstractmethod

from app.core.config import get_settings


class BaseEmbedder(ABC):
    """Kelas dasar abstrak untuk semua implementasi embedder teks."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensi vektor embedding yang dihasilkan."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Menghasilkan vektor embedding untuk satu kalimat teks tunggal."""
        pass

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Menghasilkan list vektor embedding untuk batch sekumpulan teks."""
        return [self.embed_text(t) for t in texts]


def get_embedder() -> BaseEmbedder:
    """Factory function untuk mendapatkan instance embedder berdasarkan .env."""
    settings = get_settings()
    provider = settings.EMBEDDER.lower().strip()

    if provider == "st":
        from app.embeddings.st_embedder import SentenceTransformerEmbedder

        return SentenceTransformerEmbedder()

    if provider == "api":
        from app.embeddings.api_embedder import APIEmbedder

        return APIEmbedder()

    from app.embeddings.fake_embedder import FakeEmbedder

    return FakeEmbedder()
