"""Layanan Perutean Pesan (Router Service) sesuai PRD Bagian 6.9 & 8.3.

Mengimplementasikan matriks perutean (channel x intent):
1. web_widget & telegram:
   - booking_sewa -> route=open_catalog, action={"type":"open_catalog"}, tanpa ekstraksi
   - tanya_info    -> route=answer_info, memanggil RAG
   - ubah_batal    -> route=handoff_staff, balasan sopan diteruskan ke staf
   - keluhan       -> route=handoff_staff, balasan empati diteruskan ke staf
   - lainnya       -> route=refuse (atau balasan sapaan ramah via Guardrails)
2. staff_paste:
   - booking_sewa  -> route=extract_order, mengekstraksi draf pesanan
   - tanya_info    -> route=suggest_reply, RAG menghasilkan saran balasan untuk staf
   - lainnya/other -> route=handoff_staff, catatan bukan pesan booking
3. force_extract:
   - langsung ke route=extract_order tanpa memandang intent.
"""

from __future__ import annotations

import time
import uuid

from app.core.logging import get_logger
from app.schemas.chat import ChatAction, ChatMeta, ChatRequest, ChatResponse
from app.schemas.common import ChannelEnum, IntentEnum, RouteEnum
from app.schemas.order import ExtractedOrder
from app.services.extractor import OrderExtractor, get_order_extractor
from app.services.guardrails import (
    DEFAULT_REFUSAL_MESSAGE,
    GuardrailsService,
    get_guardrails,
)
from app.services.intent import IntentClassifier, get_intent_classifier
from app.services.rag import RAGService, get_rag_service

logger = get_logger(__name__)

# Pesan standar perutean web_widget & telegram
OPEN_CATALOG_REPLY = (
    "Halo Kak! Untuk melakukan booking sewa alat camping di Sabana Adventure, "
    "silakan langsung pilih alat yang dibutuhkan pada katalog website dan masukkan "
    "ke keranjang sewa ya Kak. Staf kami siap menyiapkan perlengkapan camping terbaik untuk Kakak!"
)

UBAH_BATAL_REPLY = (
    "Halo Kak, permohonan perubahan atau pembatalan sewa telah kami teruskan langsung ke "
    "staf toko Sabana Adventure agar segera dibantu verifikasi dan proses lanjutannya ya Kak."
)

KELUHAN_REPLY = (
    "Halo Kak, mohon maaf atas ketidaknyamanan yang dialami. Keluhan Kakak segera kami sampaikan "
    "ke tim pengelola toko Sabana Adventure untuk ditindaklanjuti dengan prioritas ya Kak."
)

STAFF_EXTRACT_REPLY = (
    "Draf pesanan berhasil diekstraksi dari chat pelanggan. Silakan tinjau rincian alat dan "
    "jadwal sewa sebelum konfirmasi pesanan ke sistem toko."
)


class RouterService:
    """Komponen perutean pesan berdasarkan kanal masuk dan klasifikasi maksud percakapan."""

    def __init__(
        self,
        classifier: IntentClassifier | None = None,
        guardrails: GuardrailsService | None = None,
        rag_service: RAGService | None = None,
        extractor: OrderExtractor | None = None,
    ) -> None:
        self._classifier = classifier
        self._guardrails = guardrails
        self._rag = rag_service
        self._extractor = extractor

    @property
    def classifier(self) -> IntentClassifier:
        """Mengambil instance IntentClassifier secara lazy."""
        if self._classifier is None:
            self._classifier = get_intent_classifier()
        return self._classifier

    @property
    def guardrails(self) -> GuardrailsService:
        """Mengambil instance GuardrailsService secara lazy."""
        if self._guardrails is None:
            self._guardrails = get_guardrails()
        return self._guardrails

    @property
    def rag(self) -> RAGService:
        """Mengambil instance RAGService secara lazy."""
        if self._rag is None:
            self._rag = get_rag_service()
        return self._rag

    @property
    def extractor(self) -> OrderExtractor:
        """Mengambil instance OrderExtractor secara lazy."""
        if self._extractor is None:
            self._extractor = get_order_extractor()
        return self._extractor

    def route_message(self, request: ChatRequest) -> ChatResponse:
        """Mengeksekusi perutean pesan lengkap dan mengembalikan ChatResponse standar.

        Args:
            request: Objek ChatRequest berisi teks pesan, channel, dan opsi force_extract.

        Returns:
            ChatResponse: Respons berformat lengkap sesuai PRD Bagian 8.3.
        """
        start_time = time.perf_counter()
        req_id = request.request_id or str(uuid.uuid4())
        channel = request.channel
        message = request.message.strip()

        model_version: str | None = None
        if self.classifier.artifact:
            model_version = str(self.classifier.artifact.get("model_name", "intent-e1-v1"))

        # 1. Pengecekan Keamanan Awal (Lapis 3: Injeksi Prompt)
        is_inj, inj_pattern = self.guardrails.check_injection(message)
        if is_inj:
            logger.warning(f"Injeksi prompt terdeteksi [{inj_pattern}] pada request {req_id}")
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return ChatResponse(
                request_id=req_id,
                intent=IntentEnum.lainnya,
                confidence=1.0,
                route=RouteEnum.refuse,
                reply_text=DEFAULT_REFUSAL_MESSAGE,
                action=None,
                result=None,
                sources=[],
                meta=ChatMeta(
                    model_version=model_version,
                    prompt_version=None,
                    latency_ms=latency_ms,
                    fallback_used=False,
                    low_confidence=False,
                    sentiment=None,
                ),
            )

        # 2. Pengecekan Flag force_extract (PRD 8.1 & 8.2)
        if request.force_extract:
            logger.info(f"force_extract aktif untuk request {req_id}, melewati klasifikasi intent")
            extracted_order, fallback_used = self.extractor.extract(
                message, reference_date=request.reference_date
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return ChatResponse(
                request_id=req_id,
                intent=IntentEnum.booking_sewa,
                confidence=1.0,
                route=RouteEnum.extract_order,
                reply_text=STAFF_EXTRACT_REPLY,
                action=None,
                result=extracted_order,
                sources=[],
                meta=ChatMeta(
                    model_version=model_version,
                    prompt_version="extract_v1",
                    latency_ms=latency_ms,
                    fallback_used=fallback_used,
                    low_confidence=False,
                    sentiment=None,
                ),
            )

        # 3. Klasifikasi Intent
        intent_label, confidence, is_low_conf = self.classifier.predict(message)
        try:
            intent_enum = IntentEnum(intent_label)
        except ValueError:
            intent_enum = IntentEnum.lainnya

        # 4. Perutean Matriks Channel x Intent (PRD Bagian 6.9)
        if channel in (ChannelEnum.web_widget, ChannelEnum.telegram):
            response = self._handle_web_or_telegram(
                req_id=req_id,
                message=message,
                intent=intent_enum,
                confidence=confidence,
                is_low_conf=is_low_conf,
                model_version=model_version,
                start_time=start_time,
            )
        else:
            # channel == ChannelEnum.staff_paste
            response = self._handle_staff_paste(
                req_id=req_id,
                message=message,
                intent=intent_enum,
                confidence=confidence,
                is_low_conf=is_low_conf,
                reference_date=request.reference_date,
                model_version=model_version,
                start_time=start_time,
            )

        return response

    def _handle_web_or_telegram(
        self,
        req_id: str,
        message: str,
        intent: IntentEnum,
        confidence: float,
        is_low_conf: bool,
        model_version: str | None,
        start_time: float,
    ) -> ChatResponse:
        """Menangani perutean untuk web_widget dan bot telegram."""
        route: RouteEnum
        reply_text: str
        action: ChatAction | None = None
        result: ExtractedOrder | None = None
        sources: list[str] = []
        prompt_version: str | None = None

        if intent == IntentEnum.booking_sewa:
            # PRD 6.9: Arahkan memilih alat di katalog dan keranjang. action={"type":"open_catalog"}
            route = RouteEnum.open_catalog
            action = ChatAction(type="open_catalog")
            reply_text = OPEN_CATALOG_REPLY

        elif intent == IntentEnum.tanya_info:
            # PRD 6.9: route=answer_info -> RAG
            route = RouteEnum.answer_info
            rag_reply, rag_sources, top_score, forwarded = self.rag.ask(message)
            reply_text = rag_reply
            sources = rag_sources
            prompt_version = "rag_v1"

        elif intent == IntentEnum.ubah_batal:
            # PRD 6.9: route=handoff_staff
            route = RouteEnum.handoff_staff
            reply_text = UBAH_BATAL_REPLY

        elif intent == IntentEnum.keluhan:
            # PRD 6.9: route=handoff_staff (+ sentimen P2)
            route = RouteEnum.handoff_staff
            reply_text = KELUHAN_REPLY

        else:
            # intent == IntentEnum.lainnya
            # PRD 6.9: route=refuse atau sapaan. Sapaan dijawab ramah, selebihnya ditolak sopan
            guardrail_res = self.guardrails.validate_input(
                message=message,
                intent=intent.value,
                confidence=confidence,
            )
            route = RouteEnum.refuse
            reply_text = guardrail_res.reply_text or DEFAULT_REFUSAL_MESSAGE

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return ChatResponse(
            request_id=req_id,
            intent=intent,
            confidence=confidence,
            route=route,
            reply_text=reply_text,
            action=action,
            result=result,
            sources=sources,
            meta=ChatMeta(
                model_version=model_version,
                prompt_version=prompt_version,
                latency_ms=latency_ms,
                fallback_used=False,
                low_confidence=is_low_conf,
                sentiment=None,
            ),
        )

    def _handle_staff_paste(
        self,
        req_id: str,
        message: str,
        intent: IntentEnum,
        confidence: float,
        is_low_conf: bool,
        reference_date: str | None,
        model_version: str | None,
        start_time: float,
    ) -> ChatResponse:
        """Menangani perutean untuk panel admin staff_paste."""
        route: RouteEnum
        reply_text: str
        action: ChatAction | None = None
        result: ExtractedOrder | None = None
        sources: list[str] = []
        prompt_version: str | None = None

        fallback_used = False
        if intent == IntentEnum.booking_sewa:
            # PRD 6.9: route=extract_order -> Ekstraksi, hasil needs_review
            route = RouteEnum.extract_order
            extracted_order, fallback_used = self.extractor.extract(
                message, reference_date=reference_date
            )
            result = extracted_order
            reply_text = STAFF_EXTRACT_REPLY
            prompt_version = "extract_v1"

        elif intent == IntentEnum.tanya_info:
            # PRD 6.9: route=suggest_reply -> RAG menghasilkan saran balasan untuk disalin staf
            route = RouteEnum.suggest_reply
            rag_reply, rag_sources, top_score, forwarded = self.rag.ask(message)
            reply_text = rag_reply
            sources = rag_sources
            prompt_version = "rag_v1"

        else:
            # PRD 6.9: intent selain booking_sewa dan tanya_info
            # Kembalikan intent saja dengan catatan 'bukan pesan booking'
            route = RouteEnum.handoff_staff
            reply_text = (
                f"Pesan ini terdeteksi sebagai maksud '{intent.value}' (bukan pesan booking). "
                "Silakan tangani secara langsung sesuai keperluan pelanggan."
            )

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return ChatResponse(
            request_id=req_id,
            intent=intent,
            confidence=confidence,
            route=route,
            reply_text=reply_text,
            action=action,
            result=result,
            sources=sources,
            meta=ChatMeta(
                model_version=model_version,
                prompt_version=prompt_version,
                latency_ms=latency_ms,
                fallback_used=fallback_used,
                low_confidence=is_low_conf,
                sentiment=None,
            ),
        )


_router_instance: RouterService | None = None


def get_router() -> RouterService:
    """Mengambil instance singleton RouterService."""
    global _router_instance
    if _router_instance is None:
        _router_instance = RouterService()
    return _router_instance
