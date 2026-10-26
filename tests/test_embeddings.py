"""Pengujian unit komprehensif untuk antarmuka Embeddings (T-04)."""

import math

import pytest

from app.core.errors import AIUnavailableError
from app.embeddings.api_embedder import APIEmbedder
from app.embeddings.base import get_embedder
from app.embeddings.fake_embedder import FakeEmbedder


def test_fake_embedder_dimension() -> None:
    """Memastikan dimensi vektor FakeEmbedder sesuai konfigurasi."""
    embedder_default = FakeEmbedder()
    assert embedder_default.dimension == 384
    vec = embedder_default.embed_text("tenda dome")
    assert len(vec) == 384

    embedder_custom = FakeEmbedder(dimension=128)
    assert embedder_custom.dimension == 128
    vec_custom = embedder_custom.embed_text("tenda dome")
    assert len(vec_custom) == 128


def test_fake_embedder_deterministic() -> None:
    """Memastikan FakeEmbedder menghasilkan vektor identik untuk teks yang sama."""
    embedder = FakeEmbedder()
    text = "sewa tenda kapasitas 4 orang"

    vec1 = embedder.embed_text(text)
    vec2 = embedder.embed_text(text)

    # Identik 100%
    assert vec1 == vec2

    # Teks berbeda menghasilkan vektor berbeda
    vec_different = embedder.embed_text("sepatu gunung ukuran 42")
    assert vec1 != vec_different


def test_fake_embedder_unit_vector() -> None:
    """Memastikan FakeEmbedder menghasilkan vektor bernilai norma 1.0 (unit vector)."""
    embedder = FakeEmbedder()
    vec = embedder.embed_text("kompor portable dan gas kaleng")

    # Hitung L2 norm
    l2_norm = math.sqrt(sum(x**2 for x in vec))
    assert math.isclose(l2_norm, 1.0, rel_tol=1e-5)


def test_fake_embedder_batch() -> None:
    """Memastikan embed_batch menghasilkan list vektor yang konsisten dengan embed_text."""
    embedder = FakeEmbedder()
    texts = ["tenda", "matras", "sleeping bag"]
    batch_vecs = embedder.embed_batch(texts)

    assert len(batch_vecs) == 3
    for i, t in enumerate(texts):
        assert batch_vecs[i] == embedder.embed_text(t)


def test_fake_embedder_empty_text() -> None:
    """Memastikan teks kosong menghasilkan vektor nol."""
    embedder = FakeEmbedder(dimension=64)
    vec = embedder.embed_text("")
    assert vec == [0.0] * 64


def test_api_embedder_missing_key_raises_error() -> None:
    """Memastikan APIEmbedder menolak jalan jika API key kosong."""
    embedder = APIEmbedder(api_key="")
    with pytest.raises(AIUnavailableError) as exc:
        embedder.embed_text("tenda")
    assert "LLM_API_KEY kosong" in str(exc.value.message_dev)


def test_get_embedder_factory() -> None:
    """Memastikan factory function get_embedder mengembalikan instance BaseEmbedder."""
    embedder = get_embedder()
    assert isinstance(embedder, FakeEmbedder)
