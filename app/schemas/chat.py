"""Skema Pydantic untuk permintaan dan respon chat sesuai PRD Bagian 8."""

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ChannelEnum, IntentEnum, RouteEnum
from app.schemas.order import ExtractedOrder


class ChatMeta(BaseModel):
    """Metadata eksekusi untuk pencatatan dan evaluasi teknis."""

    model_version: str | None = Field(
        default=None,
        description="Versi model intent yang digunakan",
    )
    prompt_version: str | None = Field(
        default=None,
        description="Versi template prompt sistem",
    )
    latency_ms: int = Field(
        default=0,
        ge=0,
        description="Waktu respons layanan dalam milidetik",
    )
    fallback_used: bool = Field(
        default=False,
        description="Apakah fallback digunakan jika AI gagal",
    )
    low_confidence: bool = Field(
        default=False,
        description="Apakah keyakinan model di bawah ambang batas",
    )
    sentiment: str | None = Field(
        default=None,
        description="Sentimen pesan pelanggan (fitur P2)",
    )


class ChatAction(BaseModel):
    """Aksi kontekstual untuk frontend/backend (contoh: membuka katalog)."""

    type: str = Field(..., description="Jenis aksi, misal: open_catalog")
    payload: dict[str, Any] | None = Field(default=None, description="Data pendukung aksi")


class ChatRequest(BaseModel):
    """Format permintaan pesan chat ke endpoint POST /chat/message."""

    request_id: str | None = Field(default=None, description="ID unik request (opsional)")
    session_id: str | None = Field(default=None, description="ID sesi percakapan (opsional)")
    channel: ChannelEnum = Field(
        default=ChannelEnum.web_widget,
        description="Saluran masuk: web_widget, staff_paste, atau telegram",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Isi teks pesan pelanggan (1-1000 karakter)",
    )
    reference_date: str | None = Field(
        default=None,
        description="Tanggal acuan (YYYY-MM-DD) untuk resolusi tanggal relatif",
    )
    force_extract: bool = Field(
        default=False,
        description="Jika true, langsung lakukan ekstraksi pesanan tanpa memandang intent",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "request_id": "req-12345",
                "session_id": "sess-user-01",
                "channel": "web_widget",
                "message": "sewa 3 hari dihitung berapa hari kak?",
                "reference_date": "2026-10-28",
                "force_extract": False,
            }
        }
    }


class ChatResponse(BaseModel):
    """Format standar respon layanan Gen AI untuk POST /chat/message."""

    request_id: str = Field(..., description="ID unik request")
    intent: IntentEnum = Field(..., description="Klasifikasi maksud pesan")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Skor keyakinan model (0.0 - 1.0)")
    route: RouteEnum = Field(..., description="Rute tindakan yang diambil")
    reply_text: str = Field(..., description="Teks balasan ramah untuk pengguna / staf")
    action: ChatAction | dict[str, Any] | None = Field(
        default=None,
        description="Aksi spesifik untuk UI klien (misal open_catalog)",
    )
    result: ExtractedOrder | None = Field(
        default=None,
        description="Hasil draf pesanan jika route=extract_order, selain itu null",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Daftar ID sumber pengetahuan yang dijadikan rujukan (misal KB-03)",
    )
    meta: ChatMeta = Field(..., description="Metadata performa dan pelacakan model")


class ClassifyRequest(BaseModel):
    """Format permintaan untuk endpoint POST /chat/classify."""

    message: str = Field(..., min_length=1, max_length=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "bisa sewa tenda dome 4 orang untuk besok?",
            }
        }
    }


class ClassifyResponse(BaseModel):
    """Format respon untuk endpoint POST /chat/classify."""

    intent: IntentEnum
    confidence: float
    low_confidence: bool


class AskRequest(BaseModel):
    """Format permintaan untuk endpoint POST /chat/ask."""

    question: str = Field(..., min_length=1, max_length=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "jaminan sewa alat camping apa saja kak?",
            }
        }
    }


class AskResponse(BaseModel):
    """Format respon untuk endpoint POST /chat/ask."""

    reply_text: str
    sources: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Format respon untuk endpoint GET /health."""

    status: str = Field(default="ok")
    model_version: str = Field(default="intent-v1")
    prompt_version: str = Field(default="v1")
