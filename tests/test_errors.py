"""Pengujian Skenario Gagal dan Kode Error sesuai PRD Bagian 6.10, 8.4, & 10.

Memastikan seluruh skenario error diuji secara komprehensif:
1. HTTP 400 (invalid_input): Pesan kosong, spasi saja, atau > 1000 karakter.
2. HTTP 401 (unauthorized): Header X-Service-Key salah atau tidak disertakan.
3. HTTP 422 (validation_error): Skema JSON salah, channel tidak dikenal, tipe data salah.
4. HTTP 429 (rate_limited / quota_exceeded): Kuota habis, fallback ke X1 bila relevan.
5. HTTP 503 (ai_unavailable): Layanan AI / model tidak dapat dihubungi.
6. HTTP 504 (ai_timeout): Waktu permintaan melampaui batas LLM_TIMEOUT_S.
7. Respon JSON LLM rusak: Retry otomatis dan fallback aman ke deterministik X1.
8. Format payload error: Memiliki kunci error.{code, message_user, message_dev, request_id}.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.errors import (
    AITimeoutError,
    AIUnavailableError,
    InvalidInputError,
    QuotaExceededError,
    RateLimitedError,
    UnauthorizedError,
    ValidationError,
)
from app.llm.fake_client import FakeLLMClient
from app.main import app
from app.services.extractor import OrderExtractor

VALID_KEY = get_settings().SERVICE_API_KEY
AUTH_HEADERS = {"X-Service-Key": VALID_KEY}


@pytest.fixture
def client() -> TestClient:
    """Fixture HTTP TestClient untuk FastAPI app."""
    return TestClient(app)


# ==============================================================================
# 1. HTTP 400: invalid_input (Pesan kosong, spasi saja, atau > 1000 karakter)
# ==============================================================================


def test_error_400_empty_message(client: TestClient) -> None:
    """Menguji penolakan HTTP 400 saat pesan chat berupa string kosong."""
    payload = {"channel": "web_widget", "message": ""}
    res = client.post("/api/v1/chat/message", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 400
    err = res.json().get("error", {})
    assert err.get("code") == "invalid_input"
    assert "request_id" in err
    assert "message_user" in err


def test_error_400_whitespace_only_message(client: TestClient) -> None:
    """Menguji penolakan HTTP 400 saat pesan hanya berisi spasi/whitespace."""
    payload = {"channel": "web_widget", "message": "    \n\t   "}
    res = client.post("/api/v1/chat/message", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 400
    err = res.json().get("error", {})
    assert err.get("code") == "invalid_input"


def test_error_400_message_too_long(client: TestClient) -> None:
    """Menguji penolakan HTTP 400 saat pesan melebihi batas 1000 karakter."""
    payload = {"channel": "web_widget", "message": "a" * 1005}
    res = client.post("/api/v1/chat/message", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 400
    err = res.json().get("error", {})
    assert err.get("code") == "invalid_input"


def test_error_400_order_extract_empty(client: TestClient) -> None:
    """Menguji penolakan HTTP 400 pada endpoint orders/extract saat teks kosong."""
    payload = {"message": "   "}
    res = client.post("/api/v1/orders/extract", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 400
    err = res.json().get("error", {})
    assert err.get("code") == "invalid_input"


# ==============================================================================
# 2. HTTP 401: unauthorized (Header X-Service-Key salah atau tidak disediakan)
# ==============================================================================


def test_error_401_missing_key(client: TestClient) -> None:
    """Menguji HTTP 401 unauthorized ketika header X-Service-Key tidak disertakan."""
    res = client.post("/api/v1/chat/message", json={"channel": "web_widget", "message": "halo"})
    assert res.status_code == 401
    err = res.json().get("error", {})
    assert err.get("code") == "unauthorized"
    assert err.get("message_user") == "Akses ditolak. Layanan hanya dapat diakses oleh backend."


def test_error_401_invalid_key(client: TestClient) -> None:
    """Menguji HTTP 401 unauthorized ketika kunci tidak cocok."""
    res = client.post(
        "/api/v1/chat/message",
        json={"channel": "web_widget", "message": "halo"},
        headers={"X-Service-Key": "wrong_key_123"},
    )
    assert res.status_code == 401
    err = res.json().get("error", {})
    assert err.get("code") == "unauthorized"


# ==============================================================================
# 3. HTTP 422: validation_error (Skema permintaan salah)
# ==============================================================================


def test_error_422_invalid_channel(client: TestClient) -> None:
    """Menguji HTTP 422 saat nilai channel di luar enum (bukan web_widget/staff_paste/telegram)."""
    payload = {"channel": "invalid_channel", "message": "halo kak"}
    res = client.post("/api/v1/chat/message", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 422
    err = res.json().get("error", {})
    assert err.get("code") == "validation_error"
    assert "message_dev" in err


def test_error_422_invalid_json_body(client: TestClient) -> None:
    """Menguji HTTP 422 saat payload bukan format JSON yang valid."""
    res = client.post(
        "/api/v1/chat/message",
        content="{invalid_json_syntax: true",
        headers={**AUTH_HEADERS, "Content-Type": "application/json"},
    )
    assert res.status_code == 422
    err = res.json().get("error", {})
    assert err.get("code") == "validation_error"


def test_error_422_missing_required_fields(client: TestClient) -> None:
    """Menguji HTTP 422 saat field wajib (message) tidak dikirim."""
    payload = {"channel": "web_widget"}
    res = client.post("/api/v1/chat/message", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 422
    err = res.json().get("error", {})
    assert err.get("code") == "validation_error"


# ==============================================================================
# 4. HTTP 429: rate_limited / quota_exceeded & Fallback X1
# ==============================================================================


def test_error_429_quota_exceeded_exception() -> None:
    """Menguji payload dictionary dan status code untuk QuotaExceededError."""
    err = QuotaExceededError()
    assert err.status_code == 429
    assert err.code == "quota_exceeded"
    d = err.to_dict(request_id="test-req-429")
    assert d["error"]["code"] == "quota_exceeded"
    assert d["error"]["request_id"] == "test-req-429"


def test_error_429_rate_limited_exception() -> None:
    """Menguji payload dictionary dan status code untuk RateLimitedError."""
    err = RateLimitedError()
    assert err.status_code == 429
    assert err.code == "rate_limited"


def test_error_429_quota_fallback_to_x1() -> None:
    """Menguji bahwa saat LLM terkena kuota (429), ekstraksi beralih ke cadangan X1 (PRD 8.4)."""
    fake_llm = FakeLLMClient()
    fake_llm.simulate_quota_exceeded = True
    extractor = OrderExtractor(llm_client=fake_llm)
    chat_text = (
        "Format Booking Sabana Adventure:\n"
        "Nama: Maya Putri\n"
        "Tanggal Ambil: 31 Oktober 2026\n"
        "Jam: 09.00-11.00\n"
        "List: tenda dome kap 4"
    )

    extracted, fallback_used = extractor.extract(
        chat_text, reference_date="2026-10-28", method="x3"
    )

    assert extracted.customer_name == "Maya Putri"
    assert extracted.pickup_date == "2026-10-31"
    assert fallback_used is True


# ==============================================================================
# 5. HTTP 503: ai_unavailable (Layanan AI atau vector store mati)
# ==============================================================================


def test_error_503_ai_unavailable_exception() -> None:
    """Menguji payload dictionary dan status code untuk AIUnavailableError."""
    err = AIUnavailableError(
        message_user="Layanan asisten AI sedang tidak dapat diakses. Silakan hubungi pegawai toko.",
        message_dev="Vector store connection failed",
    )
    assert err.status_code == 503
    assert err.code == "ai_unavailable"
    d = err.to_dict(request_id="test-req-503")
    assert d["error"]["code"] == "ai_unavailable"
    assert "Vector store" in d["error"]["message_dev"]


def test_error_503_fake_llm_simulation() -> None:
    """Menguji bahwa FakeLLMClient melemparkan AIUnavailableError saat disimulasikan."""
    fake_llm = FakeLLMClient()
    fake_llm.simulate_unavailable = True

    with pytest.raises(AIUnavailableError) as exc_info:
        fake_llm.generate("Halo bot")
    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "ai_unavailable"


# ==============================================================================
# 6. HTTP 504: ai_timeout (Melebihi LLM_TIMEOUT_S)
# ==============================================================================


def test_error_504_ai_timeout_exception() -> None:
    """Menguji payload dan pesan user sesuai PRD Bagian 8.4 untuk AITimeoutError."""
    err = AITimeoutError(
        message_user="Asisten sedang sibuk. Silakan isi pesanan manual.",
        message_dev="LLM timeout 10s",
    )
    assert err.status_code == 504
    assert err.code == "ai_timeout"
    d = err.to_dict(request_id="test-req-504")
    assert d["error"]["code"] == "ai_timeout"
    # Sesuai contoh persis PRD 8.4
    assert d["error"]["message_user"] == "Asisten sedang sibuk. Silakan isi pesanan manual."
    assert d["error"]["message_dev"] == "LLM timeout 10s"


def test_error_504_fake_llm_timeout_simulation() -> None:
    """Menguji bahwa FakeLLMClient melemparkan AITimeoutError saat disimulasikan."""
    fake_llm = FakeLLMClient()
    fake_llm.simulate_timeout = True

    with pytest.raises(AITimeoutError) as exc_info:
        fake_llm.generate("Hitung pesanan")
    assert exc_info.value.status_code == 504
    assert exc_info.value.code == "ai_timeout"


# ==============================================================================
# 7. Respon JSON LLM Rusak -> Retry dan Fallback Aman ke X1
# ==============================================================================


def test_invalid_json_fallback_to_x1() -> None:
    """Menguji bahwa jika LLM mengembalikan JSON rusak, sistem fallback ke X1 deterministik."""
    fake_llm = FakeLLMClient()
    fake_llm.simulate_invalid_json = True
    extractor = OrderExtractor(llm_client=fake_llm)
    chat_text = (
        "Format Booking Sabana Adventure:\n"
        "Nama: Hendra\n"
        "Tanggal Ambil: 31 Oktober 2026\n"
        "Jam: 09.00-11.00\n"
        "List: tenda dome kap 4, matras 2"
    )

    extracted, fallback_used = extractor.extract(
        chat_text, reference_date="2026-10-28", method="x3"
    )

    assert extracted.customer_name == "Hendra"
    assert extracted.pickup_date == "2026-10-31"
    assert len(extracted.items) >= 2
    assert fallback_used is True


# ==============================================================================
# 8. Verifikasi Format Standar Seluruh Exception
# ==============================================================================


def test_all_app_errors_conform_to_prd_schema() -> None:
    """Memverifikasi bahwa seluruh turunan AppError mematuhi skema PRD Bagian 8.4."""
    errors = [
        InvalidInputError(),
        UnauthorizedError(),
        ValidationError(),
        RateLimitedError(),
        QuotaExceededError(),
        AIUnavailableError(),
        AITimeoutError(),
    ]

    for err in errors:
        d = err.to_dict(request_id="req-verify-schema")
        assert "error" in d
        err_payload = d["error"]
        assert "code" in err_payload
        assert "message_user" in err_payload
        assert "message_dev" in err_payload
        assert err_payload["request_id"] == "req-verify-schema"
        assert isinstance(err.status_code, int)
        assert 400 <= err.status_code <= 599
