"""Unit test untuk memvalidasi tugas T-00, T-01, dan T-02 sesuai PRD."""

from pathlib import Path
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.errors import (
    AITimeoutError,
    AppError,
    InvalidInputError,
    UnauthorizedError,
)
from app.main import app
from app.schemas.chat import ChatMeta, ChatRequest, ChatResponse
from app.schemas.common import ChannelEnum, IntentEnum, ItemStatusEnum, RouteEnum
from app.schemas.errors import ErrorResponse
from app.schemas.order import ExtractedOrder, OrderItem
from app.utils.pii import mask_pii

client = TestClient(app)


# ============================================================================
# T-00: Kerangka Repo dan Struktur Folder
# ============================================================================
def test_t00_directory_structure_exists() -> None:
    """Memastikan struktur direktori utama sesuai PRD Bagian 4 ada."""
    base_dir = Path(__file__).resolve().parent.parent
    expected_dirs = [
        "app/api",
        "app/core",
        "app/schemas",
        "app/llm",
        "app/embeddings",
        "app/services",
        "app/utils",
        "app/training",
        "configs",
        "data/raw",
        "data/synthetic",
        "data/catalog",
        "data/kb",
        "data/eval",
        "data/external",
        "models",
        "prompts",
        "reports",
        "scripts",
        "tests",
        "docs",
    ]
    for rel_path in expected_dirs:
        dir_path = base_dir / rel_path
        assert dir_path.is_dir(), f"Direktori {rel_path} belum dibuat"


def test_t00_essential_files_exist() -> None:
    """Memastikan file konfigurasi utama ada di root repo."""
    base_dir = Path(__file__).resolve().parent.parent
    essential_files = [
        "requirements.txt",
        ".env.example",
        "Makefile",
        "pyproject.toml",
        "TODO_HUMAN.md",
    ]
    for filename in essential_files:
        file_path = base_dir / filename
        assert file_path.is_file(), f"File {filename} tidak ditemukan"


# ============================================================================
# T-01: Modul Inti (Config, PII Masking, Logging, Middleware, Errors)
# ============================================================================
def test_t01_settings_load() -> None:
    """Memastikan konfigurasi Pydantic Settings berhasil dimuat."""
    settings = get_settings()
    assert settings.TIMEZONE == "Asia/Jakarta"
    assert settings.SEED == 42
    assert settings.LLM_TIMEOUT_S > 0


def test_t01_pii_masking_phone_and_names() -> None:
    """Memastikan mask_pii berhasil menyensor nomor HP, NIK, dan nama pelanggan."""
    # Test nomor HP
    text_wa = "Hubungi saya di 081234567890 atau +6281987654321 ya"
    censored_wa = mask_pii(text_wa)
    assert "081234567890" not in censored_wa
    assert "+6281987654321" not in censored_wa
    assert "[MASKED_PHONE]" in censored_wa

    # Test NIK 16 digit
    text_nik = "Jaminan NIK 3404012345678901 diserahkan saat ambil barang"
    censored_nik = mask_pii(text_nik)
    assert "3404012345678901" not in censored_nik
    assert "[MASKED_NIK]" in censored_nik

    # Test label format booking "Nama: Rizky"
    text_booking = "Nama: Rizky Ramadhan\nTanggal ambil: 31 Oktober"
    censored_booking = mask_pii(text_booking)
    assert "Rizky Ramadhan" not in censored_booking
    assert "[MASKED_NAME]" in censored_booking


def test_t01_request_id_middleware_and_health() -> None:
    """Memastikan middleware menambahkan X-Request-ID pada setiap respons."""
    # Tanpa mengirim header (otomatis dibuat UUID)
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0

    # Dengan mengirim header kustom
    custom_id = "custom-test-id-999"
    response_custom = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response_custom.status_code == 200
    assert response_custom.headers["X-Request-ID"] == custom_id


def test_t01_error_format_prd_section_8_4() -> None:
    """Memastikan struktur error sesuai Bagian 8.4 PRD."""
    timeout_err = AITimeoutError(
        message_user="Asisten sedang sibuk. Silakan isi pesanan manual.",
        message_dev="LLM timeout 10s",
    )
    err_dict = timeout_err.to_dict(request_id="test-uuid-123")

    # Validasi struktur dengan ErrorResponse Pydantic
    parsed = ErrorResponse.model_validate(err_dict)
    assert parsed.error.code == "ai_timeout"
    assert parsed.error.message_user == "Asisten sedang sibuk. Silakan isi pesanan manual."
    assert parsed.error.message_dev == "LLM timeout 10s"
    assert parsed.error.request_id == "test-uuid-123"


# ============================================================================
# T-02: Skema Pydantic Sesuai Bagian 8 PRD
# ============================================================================
def test_t02_validate_chat_request_schema() -> None:
    """Memastikan contoh ChatRequest dari Bagian 8.2 PRD lolos validasi."""
    payload = {
        "request_id": "uuid-opsional",
        "session_id": "opsional",
        "channel": "web_widget",
        "message": "sewa 3 hari dihitung berapa hari kak?",
        "reference_date": "2026-10-28",
        "force_extract": False,
    }
    req = ChatRequest.model_validate(payload)
    assert req.channel == ChannelEnum.web_widget
    assert req.message == "sewa 3 hari dihitung berapa hari kak?"
    assert req.reference_date == "2026-10-28"
    assert req.force_extract is False


def test_t02_validate_chat_response_schema() -> None:
    """Memastikan contoh ChatResponse dari Bagian 8.3 PRD lolos validasi."""
    payload = {
        "request_id": "uuid-1234",
        "intent": "tanya_info",
        "confidence": 0.94,
        "route": "answer_info",
        "reply_text": "Kak, masa sewa dihitung per 2 hari = 1 hari sewa ya.",
        "action": None,
        "result": None,
        "sources": ["KB-03"],
        "meta": {
            "model_version": "intent-e3-v1",
            "prompt_version": "rag_v1",
            "latency_ms": 1380,
            "fallback_used": False,
            "low_confidence": False,
            "sentiment": None,
        },
    }
    res = ChatResponse.model_validate(payload)
    assert res.intent == IntentEnum.tanya_info
    assert res.route == RouteEnum.answer_info
    assert res.confidence == 0.94
    assert res.sources == ["KB-03"]
    assert res.meta.latency_ms == 1380


def test_t02_validate_extracted_order_schema() -> None:
    """Memastikan contoh ExtractedOrder dari Bagian 8.3 PRD lolos validasi."""
    payload = {
        "customer_name": "Rizky",
        "pickup_date": "2026-10-31",
        "pickup_time_start": "08:00",
        "pickup_time_end": "10:00",
        "pickup_time_raw": "08.00-10.00",
        "return_date": None,
        "items": [
            {
                "raw_text": "tenda kap 4",
                "qty": 1,
                "spec": {"kapasitas": 4},
                "matched_item_id": "TND-DOME-4",
                "matched_name": "Tenda Dome Kapasitas 4",
                "match_score": 0.97,
                "status": "matched",
                "notes": None,
            },
            {
                "raw_text": "sepatu",
                "qty": 1,
                "spec": {},
                "matched_item_id": "SPT-HIK",
                "matched_name": "Sepatu Hiking",
                "match_score": 0.78,
                "status": "ambiguous",
                "notes": None,
            },
        ],
        "extra_note": None,
        "missing_fields": [],
        "warnings": ["ukuran sepatu belum disebut"],
        "needs_review": True,
    }
    order = ExtractedOrder.model_validate(payload)
    assert order.customer_name == "Rizky"
    assert order.pickup_date == "2026-10-31"
    assert len(order.items) == 2
    assert order.items[0].matched_item_id == "TND-DOME-4"
    assert order.items[0].status == ItemStatusEnum.matched
    assert order.items[1].status == ItemStatusEnum.ambiguous
    assert order.needs_review is True
