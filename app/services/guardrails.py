"""Layanan Guardrails (Perlindungan Batas Wilayah dan Keamanan AI) sesuai PRD Bagian 6.8.

Tiga Lapis Perlindungan:
1. Lapis 1 (Intent Guard): Deteksi maksud di luar domain (intent 'lainnya' non-sapaan).
2. Lapis 2 (Retrieval Score Guard): Deteksi pertanyaan relevansi rendah (skor < RAG_MIN_SCORE).
3. Lapis 3 (Injection & Adversarial Guard): Penyaring pola percobaan prompt injection dan jailbreak.

Menyediakan balasan penolakan sopan yang menjelaskan cakupan toko dan menawarkan topik yang dibantu.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.services.intent import IntentClassifier
    from app.services.rag import RAGService

logger = get_logger(__name__)

# Pesan penolakan sopan standar (PRD Bagian 6.8)
DEFAULT_REFUSAL_MESSAGE = (
    "Maaf Kak, asisten virtual Sabana Adventure hanya dapat melayani informasi "
    "dan persewaan alat camping toko kami. Saya dapat membantu seputar katalog alat, "
    "tarif dan durasi sewa, persyaratan jaminan, serta panduan booking. "
    "Ada yang bisa kami bantu terkait persewaan alat outdoor kami?"
)

# Pesan penerusan ke staf toko bila informasi toko tidak mencukupi (skor rendah)
STAFF_FORWARD_MESSAGE = (
    "Halo Kak, mohon maaf untuk pertanyaan tersebut belum tercakup dalam informasi "
    "toko kami dan akan kami teruskan ke pegawai toko agar dapat dibantu lebih lanjut ya."
)

# Pesan sapaan dan ucapan terima kasih ramah
GREETING_MESSAGE = (
    "Halo Kak! Selamat datang di Sabana Adventure Jombor. "
    "Ada yang bisa kami bantu seputar persewaan alat camping hari ini?"
)

THANKS_MESSAGE = (
    "Sama-sama Kak! Senang bisa membantu. Jika ada pertanyaan lain seputar alat camping "
    "atau booking di Sabana Adventure, jangan ragu untuk bertanya ya."
)

# Pola regex untuk deteksi Prompt Injection / Jailbreak (Lapis 3)
INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "ignore_instructions",
        re.compile(
            r"\b(abaikan|lupakan|hapus)\s+(semua\s+)?"
            r"(instruksi|perintah|aturan|prompt|arahan)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ignore_instructions_en",
        re.compile(
            r"\b(ignore|forget|override|bypass)\s+(all\s+)?(previous\s+)?"
            r"(instructions|prompts|rules|commands)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "show_prompt",
        re.compile(
            r"\b(tampilkan|bocorkan|cetak|lihatkan)\s+(semua\s+)?"
            r"(prompt|instruksi|system prompt|aturan|konteks)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "show_prompt_en",
        re.compile(
            r"\b(show|leak|reveal|print|display)\s+(the\s+)?(system\s+)?"
            r"(prompt|instructions)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "system_prompt_direct",
        re.compile(
            r"\b(system\s+prompt|developer\s+mode|jailbreak|bypass\s+mode)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "persona_override",
        re.compile(
            r"\b(kamu\s+sekarang\s+adalah|you\s+are\s+now|pretend\s+to\s+be|berpura-pura(lah)?)\b",
            re.IGNORECASE,
        ),
    ),
]

# Pola sapaan dan ucapan terima kasih
GREETING_PATTERN = re.compile(
    r"^(halo|hai|hei|helo|assalamu['a]?laikum|selamat\s+(pagi|siang|sore|malam)|"
    r"permisi|pagi\s+kak|siang\s+kak|sore\s+kak|malam\s+kak|halo\s+kak|hai\s+kak|"
    r"halo\s+min|min|admin|tes|test|ping)$",
    re.IGNORECASE,
)

THANKS_PATTERN = re.compile(
    r"\b(terima\s*kasih|makasih|matur\s*nuwun|thanks|thank\s*you|makasi|tengkyu)\b",
    re.IGNORECASE,
)


@dataclass
class GuardrailResult:
    """Hasil verifikasi guardrail terhadap pesan pengguna."""

    passed: bool
    reason: str | None = None  # "injection_detected" | "ood_intent" | "low_retrieval_score"
    matched_pattern: str | None = None
    reply_text: str | None = None
    is_greeting_or_thanks: bool = False


class GuardrailsService:
    """Komponen filter 3 lapis untuk keamanan dan batas konteks toko Sabana Adventure."""

    def __init__(
        self,
        min_rag_score: float | None = None,
        min_intent_conf: float | None = None,
    ) -> None:
        settings = get_settings()
        self.min_rag_score = min_rag_score or settings.RAG_MIN_SCORE
        self.min_intent_conf = min_intent_conf or settings.INTENT_MIN_CONF
        self.refusal_message = DEFAULT_REFUSAL_MESSAGE
        self.staff_forward_message = STAFF_FORWARD_MESSAGE
        self.greeting_message = GREETING_MESSAGE
        self.thanks_message = THANKS_MESSAGE

        self._intent_classifier: IntentClassifier | None = None
        self._rag_service: RAGService | None = None

    def _get_classifier(self) -> IntentClassifier:
        """Mengambil instance IntentClassifier secara lazy."""
        if self._intent_classifier is None:
            from app.services.intent import get_intent_classifier

            self._intent_classifier = get_intent_classifier()
        return self._intent_classifier

    def _get_rag_service(self) -> RAGService:
        """Mengambil instance RAGService secara lazy."""
        if self._rag_service is None:
            from app.services.rag import get_rag_service

            self._rag_service = get_rag_service()
        return self._rag_service

    def check_injection(self, text: str) -> tuple[bool, str | None]:
        """Lapis 3: Memeriksa apakah teks memuat pola prompt injection / adversarial attack.

        Args:
            text: Teks masukan pengguna.

        Returns:
            tuple: (is_injection, matched_pattern_name)
        """
        for name, pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                logger.warning(
                    f"Prompt injection terdeteksi: '{name}' pada pesan: '{text[:60]}...'"
                )
                return True, name
        return False, None

    def is_greeting(self, text: str) -> bool:
        """Memeriksa apakah teks merupakan sapaan umum."""
        cleaned = text.strip().strip(".!?,")
        return bool(GREETING_PATTERN.match(cleaned))

    def is_thanks(self, text: str) -> bool:
        """Memeriksa apakah teks merupakan ucapan terima kasih."""
        return bool(THANKS_PATTERN.search(text))

    def is_greeting_or_thanks(self, text: str) -> bool:
        """Memeriksa apakah pesan adalah sapaan atau ucapan terima kasih."""
        return self.is_greeting(text) or self.is_thanks(text)

    def validate_input(
        self,
        message: str,
        intent: str | None = None,
        confidence: float | None = None,
        retrieval_score: float | None = None,
    ) -> GuardrailResult:
        """Memvalidasi pesan melalui 3 lapis perlindungan Guardrails.

        Alur:
        1. Lapis 3: Cek injeksi prompt. Jika terdeteksi -> Ditolak sopan.
        2. Cek sapaan / terima kasih. Jika terdeteksi -> Lolos (ditandai ramah).
        3. Lapis 1: Cek intent 'lainnya'. Bila yakin 'lainnya' -> Ditolak sopan.
        4. Lapis 2: Cek skor retrieval RAG. Bila skor rendah -> Diteruskan / ditolak.
        5. Bila semua lulus -> Pesan aman dan dalam konteks (passed=True).

        Args:
            message: Teks masukan pelanggan.
            intent: Label intent opsional (jika sudah diklasifikasikan sebelumnya).
            confidence: Skor confidence intent opsional.
            retrieval_score: Skor retrieval relevansi dokumen opsional.

        Returns:
            GuardrailResult: Status kelulusan, alasan penolakan, dan draf balasan.
        """
        clean_msg = message.strip()
        if not clean_msg:
            return GuardrailResult(
                passed=False,
                reason="empty_message",
                reply_text=self.refusal_message,
            )

        # 1. Lapis 3: Prompt Injection & Adversarial Attack Filter
        is_inj, inj_pattern = self.check_injection(clean_msg)
        if is_inj:
            return GuardrailResult(
                passed=False,
                reason="injection_detected",
                matched_pattern=inj_pattern,
                reply_text=self.refusal_message,
            )

        # 2. Periksa sapaan atau terima kasih (Pengecualian khusus PRD 6.8 & 6.9)
        if self.is_greeting(clean_msg):
            return GuardrailResult(
                passed=True,
                is_greeting_or_thanks=True,
                reply_text=self.greeting_message,
            )
        if self.is_thanks(clean_msg):
            return GuardrailResult(
                passed=True,
                is_greeting_or_thanks=True,
                reply_text=self.thanks_message,
            )

        # 3. Lapis 1: Intent Guard
        low_confidence = False
        if intent is None:
            clf = self._get_classifier()
            intent, conf, low_confidence = clf.predict(clean_msg)
            if confidence is None:
                confidence = conf
        else:
            if confidence is not None:
                low_confidence = confidence < self.min_intent_conf

        # Jika model percaya diri bahwa ini adalah topik 'lainnya' (bukan alat camping)
        if intent == "lainnya" and not low_confidence:
            return GuardrailResult(
                passed=False,
                reason="ood_intent",
                reply_text=self.refusal_message,
            )

        # 4. Lapis 2: Retrieval Score Guard (Kemiripan semantik & leksikal dengan KB toko)
        top_score = retrieval_score
        if top_score is None:
            rag = self._get_rag_service()
            search_results = rag.vector_store.search(clean_msg, top_k=1)
            top_score = search_results[0][1] if search_results else 0.0

        if top_score < self.min_rag_score:
            # Jika pertanyaan sama sekali tidak relevan dengan katalog/KB toko
            # atau memiliki intent lainnya dengan low confidence
            logger.info(
                f"Guardrail Lapis 2 memblokir pesan (skor {top_score:.3f} < {self.min_rag_score}): "
                f"'{clean_msg[:50]}...'"
            )
            # Jika skor sangat rendah (< 0.25) atau intent 'lainnya', gunakan penolakan OOD toko
            if top_score < 0.25 or intent == "lainnya":
                return GuardrailResult(
                    passed=False,
                    reason="ood_intent",
                    reply_text=self.refusal_message,
                )

            # Jika skor antara 0.25 dan 0.35, pertanyaannya mungkin tentang toko namun di luar KB
            return GuardrailResult(
                passed=False,
                reason="low_retrieval_score",
                reply_text=self.staff_forward_message,
            )

        # 5. Semua lapis perlindungan terpenuhi
        return GuardrailResult(
            passed=True,
            reason=None,
            reply_text=None,
        )


_guardrails_instance: GuardrailsService | None = None


def get_guardrails() -> GuardrailsService:
    """Mengambil instance singleton GuardrailsService."""
    global _guardrails_instance
    if _guardrails_instance is None:
        _guardrails_instance = GuardrailsService()
    return _guardrails_instance
