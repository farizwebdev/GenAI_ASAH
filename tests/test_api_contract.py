"""Pengujian Kontrak API dan Keamanan Layanan Gen AI sesuai PRD Bagian 8 & 10.

Memastikan:
1. Autentikasi header X-Service-Key berfungsi ketat (401 jika salah/tidak ada).
2. Endpoint POST /api/v1/chat/message menghasilkan respon sesuai skema ChatResponse.
3. Endpoint POST /api/v1/orders/extract mengekstrak pesanan langsung (ExtractedOrder).
4. Endpoint POST /api/v1/chat/classify mengembalikan hasil klasifikasi intent.
5. Endpoint POST /api/v1/chat/ask mengembalikan jawaban RAG dan sources.
6. Endpoint POST /api/v1/admin/reload-data berhasil memuat ulang data katalog dan KB.
7. Endpoint GET /health mengembalikan status, versi model, dan prompt.
8. Skema OpenAPI Swagger memuat dokumentasi skema dan skema keamanan X-Service-Key.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

VALID_SERVICE_KEY = get_settings().SERVICE_API_KEY
AUTH_HEADERS = {"X-Service-Key": VALID_SERVICE_KEY}


@pytest.fixture
def client() -> TestClient:
    """Fixture HTTP TestClient untuk FastAPI app."""
    return TestClient(app)


def test_health_endpoints(client: TestClient) -> None:
    """Menguji endpoint health check sistem."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model_version" in data
    assert "prompt_version" in data

    # Endpoint v1 health juga harus 200
    resp_v1 = client.get("/api/v1/health")
    assert resp_v1.status_code == 200


def test_unauthorized_without_service_key(client: TestClient) -> None:
    """Memastikan pemanggilan API tanpa header X-Service-Key ditolak dengan HTTP 401."""
    endpoints = [
        ("POST", "/api/v1/chat/message", {"channel": "web_widget", "message": "halo"}),
        ("POST", "/api/v1/orders/extract", {"message": "Format: tenda"}),
        ("POST", "/api/v1/chat/classify", {"message": "halo"}),
        ("POST", "/api/v1/chat/ask", {"question": "buka jam berapa?"}),
        ("POST", "/api/v1/admin/reload-data", {}),
    ]

    for method, path, payload in endpoints:
        if method == "POST":
            res = client.post(path, json=payload)
        else:
            res = client.get(path)

        assert res.status_code == 401, f"Endpoint {path} seharusnya ditolak 401"
        err = res.json().get("error", {})
        assert err.get("code") == "unauthorized"
        assert "X-Service-Key" in err.get("message_dev", "")


def test_unauthorized_with_wrong_service_key(client: TestClient) -> None:
    """Memastikan pemanggilan API dengan header X-Service-Key salah ditolak HTTP 401."""
    bad_headers = {"X-Service-Key": "kunci_layanan_palsu_12345"}
    res = client.post(
        "/api/v1/chat/message",
        json={"channel": "web_widget", "message": "halo"},
        headers=bad_headers,
    )
    assert res.status_code == 401
    err = res.json().get("error", {})
    assert err.get("code") == "unauthorized"


def test_chat_message_endpoint_valid_key(client: TestClient) -> None:
    """Menguji endpoint utama POST /api/v1/chat/message dengan header kunci valid."""
    req_body = {
        "channel": "web_widget",
        "message": "sewa 3 hari dihitung berapa hari ya kak?",
        "reference_date": "2026-10-28",
        "force_extract": False,
    }
    res = client.post("/api/v1/chat/message", json=req_body, headers=AUTH_HEADERS)
    assert res.status_code == 200

    data = res.json()
    assert "request_id" in data
    assert data["intent"] == "tanya_info"
    assert data["route"] == "answer_info"
    assert "reply_text" in data
    assert "KB-03" in data["sources"]
    assert "meta" in data
    assert data["meta"]["prompt_version"] == "rag_v1"


def test_orders_extract_endpoint(client: TestClient) -> None:
    """Menguji endpoint POST /api/v1/orders/extract untuk ekstraksi pesanan langsung."""
    chat_text = (
        "Format Booking Sabana Adventure:\n"
        "Nama: Rizky Pratama\n"
        "Tanggal Ambil: 31 Oktober 2026\n"
        "Jam: 09.00-11.00\n"
        "List: tenda dome kap 4, matras 2"
    )
    req_body = {
        "message": chat_text,
        "reference_date": "2026-10-28",
    }
    res = client.post("/api/v1/orders/extract", json=req_body, headers=AUTH_HEADERS)
    assert res.status_code == 200

    data = res.json()
    assert data["customer_name"] == "Rizky Pratama"
    assert data["pickup_date"] == "2026-10-31"
    assert data["pickup_time_start"] == "09:00"
    assert len(data["items"]) >= 2
    assert data["needs_review"] is True


def test_chat_classify_endpoint(client: TestClient) -> None:
    """Menguji endpoint POST /api/v1/chat/classify untuk uji intent."""
    req_body = {"message": "alamat lengkap toko sabana adventure jombor di mana ya?"}
    res = client.post("/api/v1/chat/classify", json=req_body, headers=AUTH_HEADERS)
    assert res.status_code == 200

    data = res.json()
    assert data["intent"] == "tanya_info"
    assert isinstance(data["confidence"], float)
    assert isinstance(data["low_confidence"], bool)


def test_chat_ask_endpoint(client: TestClient) -> None:
    """Menguji endpoint POST /api/v1/chat/ask untuk uji RAG info toko."""
    req_body = {"question": "sewa 3 hari dihitung berapa hari kak?"}
    res = client.post("/api/v1/chat/ask", json=req_body, headers=AUTH_HEADERS)
    assert res.status_code == 200

    data = res.json()
    assert "reply_text" in data
    assert len(data["sources"]) > 0
    assert "KB-03" in data["sources"]


def test_admin_reload_data_endpoint(client: TestClient) -> None:
    """Menguji endpoint POST /api/v1/admin/reload-data."""
    res = client.post("/api/v1/admin/reload-data", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "berhasil dimuat ulang" in data["message"]


def test_openapi_schema_and_security(client: TestClient) -> None:
    """Memastikan skema OpenAPI (Swagger) mendeklarasikan rute dan keamanan X-Service-Key."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()

    # Periksa ketersediaan seluruh path endpoint PRD
    paths = schema.get("paths", {})
    expected_paths = [
        "/api/v1/chat/message",
        "/api/v1/orders/extract",
        "/api/v1/chat/classify",
        "/api/v1/chat/ask",
        "/api/v1/admin/reload-data",
        "/health",
    ]
    for p in expected_paths:
        assert p in paths, f"Path {p} belum terdaftar di dokumentasi OpenAPI"

    # Periksa deklarasi keamanan X-Service-Key
    components = schema.get("components", {})
    sec_schemes = components.get("securitySchemes", {})
    assert any("X-Service-Key" in str(v) for v in sec_schemes.values())
