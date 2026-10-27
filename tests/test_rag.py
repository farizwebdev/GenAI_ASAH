"""Pengujian unit komprehensif untuk modul RAG toko (T-14).

Sesuai PRD Bagian 6.7 dan Bagian 10:
- Menguji semua kasus pada data/eval/rag_eval.csv menggunakan FakeEmbedder dan FakeLLMClient.
- Menguji ambang batas RAG_MIN_SCORE (pertanyaan tidak relevan dialihkan ke pegawai tanpa LLM).
- Menguji penanganan potongan belum lengkap berlabel [ISI ...].
- Menguji aturan penolakan konfirmasi stok dan ketersediaan tanggal tertentu.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.embeddings.fake_embedder import FakeEmbedder
from app.llm.fake_client import FakeLLMClient
from app.services.rag import RAGService, VectorStore

BASE_DIR = Path(__file__).resolve().parent.parent
EVAL_PATH = BASE_DIR / "data" / "eval" / "rag_eval.csv"

SIMULATED_REPLIES = {
    "r01": "Kak, masa sewa dihitung per 2 hari sama dengan 1 hari sewa ya.",
    "r02": "Halo Kak, booking lewat WhatsApp tidak wajib DP.",
    "r03": "Halo Kak, jaminannya identitas fisik seperti KTP atau SIM.",
    "r04": "Toko buka setiap hari pukul 08.00 sampai 21.00 WIB ya Kak.",
    "r05": "Halo Kak, ketersediaan alat dapat dicek di katalog website atau ke pegawai toko ya.",
    "r06": "Bisa Kak, penambahan barang bisa dilakukan langsung di toko.",
    "r07": "Halo Kak, terkait nominal denda akan dikonfirmasi ke pegawai toko ya.",
    "r08": "Kak, cara booking via WA kirim format nama, tanggal, jam, dan list barang.",
    "r09": "Alamat toko di Jl. Ringroad Utara No.163, Jombor Kidul, Mlati ya Kak.",
    "r10": "Toko Sabana Adventure tutup pukul 21.00 WIB setiap hari ya Kak.",
    "r11": "Pembayaran sewa bisa tunai, QRIS, atau transfer bank saat pengambilan ya Kak.",
    "r12": "Bisa Kak, jaminan identitas fisik seperti BPJS atau KTM bisa digunakan.",
    "r13": "Iya Kak, untuk sewa jaket mohon sebutkan ukuran agar disiapkan.",
    "r14": "Jika alat rusak, penyewa dikenai biaya perbaikan atau penggantian ya Kak.",
    "r15": "Bisa Kak, kami menerima transfer bank terutama untuk organisasi.",
    "r16": "Toko buka setiap hari termasuk hari Minggu dari 08.00-21.00 WIB ya Kak.",
    "r17": "Halo Kak, pembatalan sewa dapat disampaikan ke pegawai toko kami ya.",
    "r18": "Bisa Kak, kami menyewakan kompor portable dan nesting.",
    "r19": "Alat yang disewakan antara lain tenda dome, carrier, matras, dan kompor Kak.",
    "r20": "Ketersediaan alat ukuran 42 silakan cek di katalog website atau pegawai ya Kak.",
    "r21": "Sewa 4 hari dihitung sebagai 2 hari sewa ya Kak.",
}


@pytest.fixture
def rag_service() -> RAGService:
    """Fixture instance RAGService dengan FakeEmbedder dan FakeLLMClient."""
    fake_embedder = FakeEmbedder()
    fake_llm = FakeLLMClient()
    for qid, reply_text in SIMULATED_REPLIES.items():
        fake_llm.register_response(qid, reply_text)

    vector_store = VectorStore(embedder=fake_embedder)
    return RAGService(
        vector_store=vector_store,
        llm_client=fake_llm,
        min_score=0.35,
    )


def test_rag_eval_all_cases(rag_service: RAGService) -> None:
    """Menguji seluruh 21 pertanyaan di rag_eval.csv memenuhi retrieval dan must_contain."""
    with open(EVAL_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 20, "Dataset rag_eval.csv minimal memuat 20 pertanyaan"

    for r in rows:
        qid = r["id"]
        question = r["question"]
        expected_kb = r["expected_kb_ids"].strip()
        must_contain = r["must_contain"].strip()
        must_not_contain = r["must_not_contain"].strip()

        # Set respons terprogram
        if isinstance(rag_service.llm_client, FakeLLMClient):
            rag_service.llm_client.default_response = SIMULATED_REPLIES.get(
                qid, "Halo Kak, siap dibantu."
            )

        reply_text, sources, top_score, forwarded = rag_service.ask(question)

        # 1. Pastikan target KB ada dalam sumber rujukan (top-3 sources)
        assert expected_kb in sources, (
            f"Kasus {qid} gagal: expected {expected_kb} tidak ada di sources {sources} "
            f"(pertanyaan: '{question}', score: {top_score})"
        )

        # 2. Cek must_contain jika ada
        if must_contain:
            assert must_contain.lower() in reply_text.lower(), (
                f"Kasus {qid} gagal: '{must_contain}' tidak ada dalam jawaban: '{reply_text}'"
            )

        # 3. Cek must_not_contain jika ada (larangan klaim stok pasti)
        if must_not_contain:
            assert must_not_contain.lower() not in reply_text.lower(), (
                f"Kasus {qid} gagal: '{must_not_contain}' ditemukan dalam jawaban: '{reply_text}'"
            )


def test_rag_min_score_forward_to_staff(rag_service: RAGService) -> None:
    """Menguji bahwa pertanyaan di luar topik toko dialihkan ke pegawai tanpa LLM."""
    out_of_domain = "Berapa resep bumbu nasi goreng kambing spesial?"

    # Reset call count pada LLM
    if isinstance(rag_service.llm_client, FakeLLMClient):
        rag_service.llm_client.call_count = 0

    reply_text, sources, top_score, forwarded = rag_service.ask(out_of_domain)

    assert forwarded is True
    assert top_score < 0.35
    assert len(sources) == 0
    assert "teruskan ke pegawai toko" in reply_text.lower()

    # Pastikan LLM tidak dipanggil untuk menghemat biaya dan kuota token
    if isinstance(rag_service.llm_client, FakeLLMClient):
        assert rag_service.llm_client.call_count == 0


def test_rag_stock_availability_refusal(rag_service: RAGService) -> None:
    """Menguji bahwa pertanyaan stok ketersediaan tanggal tidak mengklaim stok tersedia."""
    stock_query = "ready tenda kapasitas 4 untuk tanggal 31 besok gak kak?"
    reply_text, sources, top_score, forwarded = rag_service.ask(stock_query)

    assert "KB-09" in sources
    assert "katalog" in reply_text.lower()
    assert "stok tersedia" not in reply_text.lower()
    assert "tidak dapat memastikan" in reply_text.lower()


def test_rag_unfilled_tag_handled(rag_service: RAGService) -> None:
    """Menguji bahwa pertanyaan seputar potongan [ISI ...] diarahkan ke pegawai."""
    unfilled_query = "Berapa nominal denda kalau telat balikin tenda kak?"
    reply_text, sources, top_score, _ = rag_service.ask(unfilled_query)

    assert "KB-06" in sources
    assert "pegawai toko" in reply_text.lower()
    assert "dikonfirmasi" in reply_text.lower()
