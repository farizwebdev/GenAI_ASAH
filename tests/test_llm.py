"""Pengujian unit komprehensif untuk antarmuka LLM dan penanganan error (T-03)."""

import pytest

from app.core.errors import (
    AITimeoutError,
    AIUnavailableError,
    AppError,
    QuotaExceededError,
)
from app.llm.base import get_llm_client
from app.llm.fake_client import FakeLLMClient
from app.llm.gemini_client import GeminiLLMClient
from app.llm.json_utils import clean_and_parse_json, extract_json_str


def test_fake_llm_default_response() -> None:
    """Memastikan FakeLLMClient mengembalikan respons default."""
    client = FakeLLMClient(default_response="Halo, ada yang bisa dibantu?")
    resp = client.generate("Halo toko")
    assert resp == "Halo, ada yang bisa dibantu?"
    assert client.call_count == 1


def test_fake_llm_registered_response() -> None:
    """Memastikan FakeLLMClient mengembalikan respons sesuai kata kunci terdaftar."""
    client = FakeLLMClient()
    client.register_response("tenda", '{"item": "TND-DOME-4", "status": "matched"}')
    resp = client.generate("Saya mau sewa tenda kap 4")
    assert resp == '{"item": "TND-DOME-4", "status": "matched"}'


def test_fake_llm_in_memory_caching() -> None:
    """Memastikan pemanggilan prompt identik memanfaatkan in-memory LRU cache."""
    client = FakeLLMClient(enable_cache=True)
    prompt = "Tes pesan berulang"

    # Panggilan pertama (cache miss)
    resp1 = client.generate(prompt)
    assert client.call_count == 1

    # Panggilan kedua (cache hit, call_count tidak bertambah)
    resp2 = client.generate(prompt)
    assert client.call_count == 1
    assert resp1 == resp2


def test_json_utils_clean_and_parse() -> None:
    """Memastikan json_utils dapat membersihkan markdown code block dan parse JSON."""
    # JSON murni
    clean = '{"status": "ok", "qty": 2}'
    assert clean_and_parse_json(clean) == {"status": "ok", "qty": 2}

    # JSON dalam markdown code block ```json ... ```
    wrapped = """```json
    {
        "customer_name": "Rizky",
        "pickup_date": "2026-10-31"
    }
    ```"""
    data = clean_and_parse_json(wrapped)
    assert data["customer_name"] == "Rizky"
    assert data["pickup_date"] == "2026-10-31"

    # Ekstraksi string mentah
    extracted = extract_json_str("```\n{\"a\": 1}\n```")
    assert extracted == '{"a": 1}'


def test_json_utils_invalid_json_raises_app_error() -> None:
    """Memastikan teks non-JSON memicu AppError dengan format standar."""
    with pytest.raises(AppError) as exc_info:
        clean_and_parse_json("Ini bukan json sama sekali")
    assert exc_info.value.code == "invalid_ai_json"


def test_fake_llm_generate_json() -> None:
    """Memastikan method generate_json langsung menghasilkan dict."""
    client = FakeLLMClient(default_response='{"matched": true, "score": 0.95}')
    data = client.generate_json("cek kecocokan")
    assert data["matched"] is True
    assert data["score"] == 0.95


def test_fake_llm_simulated_errors() -> None:
    """Memastikan simulasi error memicu exception standar PRD Bagian 8.4."""
    client = FakeLLMClient(enable_cache=False)

    # 1. Timeout -> AITimeoutError (504)
    client.simulate_timeout = True
    with pytest.raises(AITimeoutError) as exc_timeout:
        client.generate("halo")
    assert exc_timeout.value.status_code == 504
    client.simulate_timeout = False

    # 2. Quota Exceeded -> QuotaExceededError (429)
    client.simulate_quota_exceeded = True
    with pytest.raises(QuotaExceededError) as exc_quota:
        client.generate("halo")
    assert exc_quota.value.status_code == 429
    client.simulate_quota_exceeded = False

    # 3. AI Unavailable -> AIUnavailableError (503)
    client.simulate_unavailable = True
    with pytest.raises(AIUnavailableError) as exc_unavail:
        client.generate("halo")
    assert exc_unavail.value.status_code == 503
    client.simulate_unavailable = False

    # 4. Invalid JSON
    client.simulate_invalid_json = True
    with pytest.raises(AppError) as exc_json:
        client.generate_json("halo")
    assert exc_json.value.code == "invalid_ai_json"


def test_gemini_client_missing_key_raises_error() -> None:
    """Memastikan Gemini client menolak jalan jika API key kosong."""
    client = GeminiLLMClient(api_key="")
    with pytest.raises(AIUnavailableError) as exc:
        client.generate("halo")
    assert "LLM_API_KEY kosong" in str(exc.value.message_dev)


def test_get_llm_client_factory() -> None:
    """Memastikan factory function get_llm_client mengembalikan instance BaseLLMClient."""
    client = get_llm_client()
    assert isinstance(client, FakeLLMClient)
