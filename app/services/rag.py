"""Layanan Tanya-Jawab Informasi Toko (RAG Service) sesuai PRD Bagian 6.7.

Alur RAG:
1. Membaca data/kb/kb_toko.md dan memecah menjadi potongan per ID (KB-01 s/d KB-12).
2. Mengindeks potongan ke vector store (ChromaDB / InMemoryVectorStore untuk mode ringan).
3. Melakukan pencarian semantik & leksikal top-3 terhadap pertanyaan pelanggan.
4. Jika skor tertinggi < RAG_MIN_SCORE (0.35), teruskan ke pegawai tanpa memanggil LLM.
5. Generator memanggil LLM dengan prompts/rag_v1.txt (gaya pegawai ramah 'Kak', memuat sources).
6. Aturan ketat: tidak boleh memastikan ketersediaan stok/tanggal tertentu dan tidak mengarang
   nilai dari potongan bertanda [ISI ...].
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from rapidfuzz import fuzz

from app.core.config import get_settings
from app.core.logging import get_logger
from app.embeddings.base import BaseEmbedder, get_embedder
from app.llm.base import BaseLLMClient, get_llm_client

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
KB_PATH = BASE_DIR / "data" / "kb" / "kb_toko.md"
PROMPT_PATH = BASE_DIR / "prompts" / "rag_v1.txt"

# Peta kata kunci spesifik per ID untuk membantu resolusi topik toko
KB_KEYWORD_MAP: dict[str, list[str]] = {
    "KB-01": ["booking", "cara booking", "format", "wa", "whatsapp", "dp", "uang muka"],
    "KB-02": ["penambahan", "nambah", "tambah", "di toko", "tambah barang", "nyampe toko"],
    "KB-03": [
        "hitungan", "hitung", "dihitung", "masa sewa", "durasi", "2 hari", "3 hari",
        "4 hari", "sewa berapa hari", "hari sewa", "sewa 3 hari", "sewa 4 hari",
    ],
    "KB-04": ["jaminan", "ktp", "sim", "ktm", "bpjs", "npwp", "identitas fisik", "luar jogja"],
    "KB-05": ["pembayaran", "bayar", "transfer", "qris", "tunai", "cash", "bayarnya"],
    "KB-06": ["denda", "pengembalian", "rusak", "hilang", "terlambat", "telat", "biaya perbaikan"],
    "KB-07": [
        "jam", "operasional", "buka", "tutup", "wib", "hari minggu", "setiap hari", "jam buka",
    ],
    "KB-08": [
        "lokasi", "alamat", "di mana", "ringroad", "jombor", "sleman", "sinduadi", "toko di mana",
    ],
    "KB-09": ["ready", "stok", "ketersediaan", "ada gak", "tanggal", "apakah ada", "katalog"],
    "KB-10": ["ukuran", "sepatu", "jaket", "size", "nomor sepatu"],
    "KB-11": ["ubah", "batal", "batalin", "cancel", "ganti tanggal", "pembatalan"],
    "KB-12": [
        "alat", "daftar", "kategori", "disewakan", "apa saja", "tenda", "kompor",
        "nesting", "headlamp", "carrier", "sleeping bag", "matras",
    ],
}


@dataclass
class KBChunk:
    """Satu potongan dokumen dari basis pengetahuan toko."""

    id: str
    topik: str
    source: str
    content: str
    keywords: list[str] = field(default_factory=list)
    has_unfilled_tag: bool = False


def load_kb_chunks(file_path: Path | None = None) -> list[KBChunk]:
    """Membaca dan mem-parsing kb_toko.md menjadi daftar KBChunk."""
    path = file_path or KB_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Berkas basis pengetahuan {path} tidak ditemukan.")

    raw_text = path.read_text(encoding="utf-8")
    parts = [p.strip() for p in raw_text.split("---") if p.strip()]

    chunks: list[KBChunk] = []
    for i in range(0, len(parts), 2):
        header = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""

        id_match = re.search(r"id:\s*(\S+)", header)
        topik_match = re.search(r"topik:\s*(\S+)", header)
        source_match = re.search(r"source:\s*(\S+)", header)

        chunk_id = id_match.group(1) if id_match else f"KB-{len(chunks)+1:02d}"
        topik = topik_match.group(1) if topik_match else "umum"
        source = source_match.group(1) if source_match else "toko"

        keywords = KB_KEYWORD_MAP.get(chunk_id, [])
        has_unfilled = "[ISI" in body

        chunks.append(
            KBChunk(
                id=chunk_id,
                topik=topik,
                source=source,
                content=body,
                keywords=keywords,
                has_unfilled_tag=has_unfilled,
            )
        )

    return chunks


class VectorStore:
    """Antarmuka penyimpanan vektor dan pencarian kemiripan dokumen."""

    def __init__(self, embedder: BaseEmbedder | None = None) -> None:
        self.embedder = embedder or get_embedder()
        self.chunks: list[KBChunk] = []
        self._vectors: list[np.ndarray] = []

    def index_chunks(self, chunks: list[KBChunk]) -> None:
        """Mengindeks daftar potongan dokumen ke dalam memori."""
        self.chunks = chunks
        self._vectors = []
        for c in chunks:
            text_to_embed = f"{c.content} {c.topik} {' '.join(c.keywords)}"
            vec = np.array(self.embedder.embed_text(text_to_embed))
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            self._vectors.append(vec)

    def search(self, query: str, top_k: int = 3) -> list[tuple[KBChunk, float]]:
        """Mencari top-k potongan paling relevan dengan kombinasi semantik dan leksikal."""
        if not self.chunks:
            return []

        q_lower = query.lower()
        q_vec = np.array(self.embedder.embed_text(query))
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scored: list[tuple[KBChunk, float]] = []

        for idx, chunk in enumerate(self.chunks):
            # 1. Cosine similarity
            cos_sim = float(np.dot(q_vec, self._vectors[idx])) if len(self._vectors) > idx else 0.0
            sem_score = max(0.0, cos_sim)

            # 2. Skor kecocokan kata kunci dan topik
            lex_score = 0.0
            for kw in chunk.keywords:
                if kw in q_lower:
                    lex_score += 0.35

            if chunk.topik.replace("_", " ") in q_lower:
                lex_score += 0.30

            # Fuzzy token matching dengan isi dokumen
            content_match = fuzz.token_set_ratio(q_lower, chunk.content.lower()) / 100.0
            if content_match >= 0.60:
                lex_score += 0.35

            # Gabungkan skor (maksimal 1.0)
            final_score = min(1.0, (0.3 * sem_score) + (0.7 * min(1.0, lex_score)))
            scored.append((chunk, round(final_score, 4)))

        # Urutkan berdasarkan skor menurun
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class RAGService:
    """Layanan RAG untuk menjawab pertanyaan seputar toko Sabana Adventure."""

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        llm_client: BaseLLMClient | None = None,
        min_score: float | None = None,
        prompt_path: Path | None = None,
    ) -> None:
        settings = get_settings()
        self.min_score = min_score if min_score is not None else settings.RAG_MIN_SCORE
        self.llm_client = llm_client
        self.vector_store = vector_store or VectorStore()
        self.prompt_path = prompt_path or PROMPT_PATH
        self._system_prompt = ""
        self._load_system_prompt()
        self._initialize_kb()

    def _load_system_prompt(self) -> None:
        """Memuat prompt sistem dari prompts/rag_v1.txt."""
        if self.prompt_path.is_file():
            self._system_prompt = self.prompt_path.read_text(encoding="utf-8").strip()

    def _initialize_kb(self) -> None:
        """Memuat data KB dan mengindeksnya."""
        chunks = load_kb_chunks()
        self.vector_store.index_chunks(chunks)

    def _get_llm(self) -> BaseLLMClient:
        """Mengambil LLM Client secara lazy."""
        if self.llm_client is None:
            self.llm_client = get_llm_client()
        return self.llm_client

    def ask(self, question: str) -> tuple[str, list[str], float, bool]:
        """Menjawab pertanyaan informasi toko menggunakan pipeline RAG.

        Args:
            question: Pertanyaan teks dari pelanggan.

        Returns:
            tuple: (reply_text, sources, top_score, forwarded_to_staff)
        """
        top_chunks = self.vector_store.search(question, top_k=3)
        if not top_chunks:
            return (
                "Halo Kak, mohon maaf untuk pertanyaan tersebut akan kami teruskan ke pegawai "
                "toko agar dapat dibantu lebih lanjut ya.",
                [],
                0.0,
                True,
            )

        top_score = top_chunks[0][1]

        # PRD 6.7: Jika skor tertinggi < RAG_MIN_SCORE (default 0.35),
        # teruskan ke pegawai tanpa memanggil LLM.
        if top_score < self.min_score:
            logger.info(
                f"Skor retrieval RAG ({top_score:.3f}) di bawah ambang {self.min_score}. "
                "Pertanyaan diteruskan ke pegawai."
            )
            return (
                "Halo Kak, mohon maaf untuk pertanyaan tersebut akan kami teruskan ke pegawai "
                "toko agar dapat dibantu lebih lanjut ya.",
                [],
                top_score,
                True,
            )

        sources = [c.id for c, _ in top_chunks]
        top_chunk = top_chunks[0][0]
        q_lower = question.lower()

        # Aturan Khusus 1: Pertanyaan ketersediaan stok atau tanggal tertentu
        if any(w in q_lower for w in ["ready", "stok", "ketersediaan", "ada gak"]):
            reply = (
                "Halo Kak, untuk ketersediaan alat dan stok pada tanggal tertentu dapat "
                "dicek langsung melalui katalog website kami atau ditanyakan ke pegawai toko ya. "
                "Asisten tidak dapat memastikan ketersediaan stok."
            )
            return reply, ["KB-09"], top_score, False

        # Aturan Khusus 2: Potongan mengandung [ISI ...] dan ditanyakan nominal/detailnya
        if top_chunk.has_unfilled_tag and any(
            w in q_lower for w in ["berapa", "nominal", "ketentuan detail", "aturan luar jogja"]
        ):
            reply = (
                f"Halo Kak, terkait informasi detail mengenai {top_chunk.topik.replace('_', ' ')} "
                "akan dikonfirmasi langsung oleh pegawai toko kami ya."
            )
            return reply, sources[:1], top_score, False

        # Format konteks untuk LLM
        context_blocks: list[str] = []
        for chunk, _score in top_chunks:
            context_blocks.append(f"[{chunk.id}] {chunk.content}")
        context_text = "\n\n".join(context_blocks)

        user_prompt = (
            f"KONTEKS:\n{context_text}\n\n"
            f"Pertanyaan pelanggan:\n{question}\n\n"
            "Jawaban singkat dan ramah sebagai pegawai toko (sapaan 'Kak'):"
        )

        llm = self._get_llm()
        try:
            raw_reply = llm.generate(user_prompt, system_instruction=self._system_prompt)
            reply = raw_reply.strip()
            # Pastikan sapaan ramah diawali dengan Kak bila belum ada
            if not reply.startswith("Halo Kak") and not reply.startswith("Kak"):
                reply = f"Halo Kak, {reply}"
            return reply, sources, top_score, False
        except Exception as exc:
            logger.error(f"Gagal memanggil LLM untuk RAG: {exc}")
            # Fallback jika LLM error
            fallback_reply = (
                f"Halo Kak, {top_chunk.content} "
                "Untuk info lebih lengkap silakan hubungi pegawai toko ya."
            )
            return fallback_reply, sources, top_score, False


_rag_service_instance: RAGService | None = None


def get_rag_service() -> RAGService:
    """Mengambil instance singleton RAGService."""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance
