"""Router endpoint API untuk percakapan chat sesuai PRD Bagian 8."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.errors import InvalidInputError
from app.core.security import verify_service_key
from app.schemas.chat import (
    AskRequest,
    AskResponse,
    ChatRequest,
    ChatResponse,
    ClassifyRequest,
    ClassifyResponse,
)
from app.schemas.common import IntentEnum
from app.services.intent import get_intent_classifier
from app.services.rag import get_rag_service
from app.services.router import get_router

router = APIRouter(
    prefix="/chat",
    tags=["Chat & Percakapan"],
    dependencies=[Depends(verify_service_key)],
)


@router.post(
    "/message",
    response_model=ChatResponse,
    summary="Pintu Utama Chat & Perutean Layanan Gen AI",
    description=(
        "Menerima pesan chat pelanggan, mengklasifikasikan intent, "
        "memvalidasi batas konteks melalui guardrails, dan mengarahkan aksi "
        "sesuai matriks perutean (channel x intent)."
    ),
)
async def chat_message(request: ChatRequest) -> ChatResponse:
    """Endpoint utama untuk seluruh interaksi pesan chat toko."""
    if not request.message.strip():
        raise InvalidInputError(
            message_user="Pesan tidak boleh kosong.",
            message_dev="Pesan kosong atau hanya berisi spasi",
        )
    return get_router().route_message(request)


@router.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="Uji Klasifikasi Intent Pesan",
    description="Menguji klasifikasi maksud pesan (5 kelas) tanpa melakukan perutean penuh.",
)
async def classify_message(request: ClassifyRequest) -> ClassifyResponse:
    """Endpoint pengujian untuk model Intent Classifier."""
    classifier = get_intent_classifier()
    intent_label, confidence, is_low = classifier.predict(request.message)

    try:
        intent_enum = IntentEnum(intent_label)
    except ValueError:
        intent_enum = IntentEnum.lainnya

    return ClassifyResponse(
        intent=intent_enum,
        confidence=confidence,
        low_confidence=is_low,
    )


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Uji Tanya-Jawab RAG Informasi Toko",
    description="Menguji pipeline RAG informasi toko berbasis basis pengetahuan (KB).",
)
async def ask_info(request: AskRequest) -> AskResponse:
    """Endpoint pengujian untuk tanya-jawab RAG toko."""
    rag = get_rag_service()
    reply_text, sources, top_score, forwarded = rag.ask(request.question)
    return AskResponse(
        reply_text=reply_text,
        sources=sources,
    )
