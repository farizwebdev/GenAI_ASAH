"""Implementasi Fake Embedder deterministik untuk pengujian tanpa jaringan."""

import hashlib
import math
import random

from app.embeddings.base import BaseEmbedder


class FakeEmbedder(BaseEmbedder):
    """Embedder deterministik tiruan murni Python (tanpa dependensi eksternal).

    Menggunakan hash SHA-256 dari teks sebagai seed generator angka acak dan
    dinormalisasi dengan L2-norm sehingga cocok untuk perhitungan cosine similarity.
    """

    def __init__(self, dimension: int = 384) -> None:
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        # Jika teks kosong, kembalikan vektor nol
        if not text or not text.strip():
            return [0.0] * self._dim

        # Hasilkan integer seed stabil dari SHA-256 string
        hash_bytes = hashlib.sha256(text.strip().lower().encode("utf-8")).digest()
        seed = int.from_bytes(hash_bytes[:8], byteorder="big")

        rng = random.Random(seed)
        vec = [rng.gauss(0.0, 1.0) for _ in range(self._dim)]

        # L2-normalization agar panjang vektor = 1.0 (unit vector)
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]

        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
