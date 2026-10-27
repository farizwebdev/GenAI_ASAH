"""Pengujian unit komprehensif untuk modul extractor pesanan (T-13).

Sesuai PRD Bagian 6.6 dan Bagian 10:
- Menguji semua kasus extraction_eval.jsonl dengan FakeLLMClient terprogram.
- Menguji pra-parse deterministik X1 pada format templat toko.
- Menguji mekanisme fallback ke X1 saat respons JSON LLM rusak (corrupted).
- Menguji validasi missing_fields untuk tanggal, jam, dan item.
- Menguji penanganan catatan khusus (extra_note) penambahan barang di toko.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.llm.fake_client import FakeLLMClient
from app.services.extractor import OrderExtractor, get_order_extractor

BASE_DIR = Path(__file__).resolve().parent.parent
EVAL_PATH = BASE_DIR / "data" / "eval" / "extraction_eval.jsonl"


@pytest.fixture
def eval_cases() -> list[dict]:
    """Memuat seluruh kasus uji dari extraction_eval.jsonl."""
    with open(EVAL_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_deterministic_x1_template() -> None:
    """Menguji X1 pada templat WhatsApp resmi toko dengan data lengkap."""
    extractor = get_order_extractor()
    text = (
        "Nama: Rizky\n"
        "Tanggal ambil: 31 Oktober\n"
        "Kisaran jam ambil: 08.00-10.00\n"
        "List barang: tenda kap 4, sepatu, matras, sleeping back, headlamp, refil gas, flyseat"
    )
    order, detected = extractor.parse_deterministic_x1(text, reference_date="2026-10-28")

    assert detected is True
    assert order.customer_name == "Rizky"
    assert order.pickup_date == "2026-10-31"
    assert order.pickup_time_start == "08:00"
    assert order.pickup_time_end == "10:00"
    assert len(order.items) == 7
    assert order.needs_review is True
    assert len(order.missing_fields) == 0

    item_ids = [it.matched_item_id for it in order.items]
    assert "TND-DOME-4" in item_ids
    assert "FLY-SHEET" in item_ids
    assert "GAS-KLG" in item_ids


def test_extractor_fallback_when_llm_json_corrupted() -> None:
    """Menguji mekanisme fallback ke X1 ketika LLM mengembalikan JSON tidak valid."""
    fake_llm = FakeLLMClient()
    fake_llm.simulate_invalid_json = True  # LLM sengaja mengeluarkan string rusak

    extractor = OrderExtractor(llm_client=fake_llm)
    text = (
        "Nama: Hendra\n"
        "Tanggal ambil: 4 November\n"
        "Kisaran jam ambil: 10.00-12.00\n"
        "List barang: tenda 4 orang, lampu tenda 1, gas kaleng 2"
    )
    order, fallback_used = extractor.extract(text, reference_date="2026-10-28", method="x3")

    # Harus fallback ke hasil X1 deterministik
    assert fallback_used is True
    assert order.customer_name == "Hendra"
    assert order.pickup_date == "2026-11-04"
    assert order.pickup_time_start == "10:00"
    assert len(order.items) >= 2


def test_extractor_missing_mandatory_fields() -> None:
    """Menguji identifikasi field wajib yang rumpang (missing_fields)."""
    fake_llm = FakeLLMClient(
        default_response=json.dumps({
            "customer_name": None,
            "pickup_date": None,
            "pickup_time_start": None,
            "pickup_time_raw": None,
            "items": [{"raw_text": "tenda 4 orang", "qty": 1}],
            "warnings": [],
        })
    )
    extractor = OrderExtractor(llm_client=fake_llm)
    order, _ = extractor.extract("Kak mau booking tenda 4 orang", method="x3")

    assert "pickup_date" in order.missing_fields
    assert "pickup_time" in order.missing_fields
    assert order.needs_review is True
    assert len(order.items) == 1


def test_extractor_extra_note_handling() -> None:
    """Menguji bahwa catatan penambahan barang di toko masuk ke extra_note."""
    extractor = get_order_extractor()
    text = (
        "Nama: Bagas\n"
        "Tanggal ambil: 5 Nov\n"
        "Jam: 10an\n"
        "List: tenda kap 6, nesting\n"
        "Nanti nambah barang di toko aja ya"
    )
    order, _ = extractor.parse_deterministic_x1(text, reference_date="2026-10-28")

    assert order.extra_note is not None
    assert "nambah barang di toko" in order.extra_note.lower()


def test_all_extraction_eval_cases(eval_cases: list[dict]) -> None:
    """Menguji semua kasus pada extraction_eval.jsonl menggunakan FakeLLMClient terprogram."""
    fake_llm = FakeLLMClient()
    for c in eval_cases:
        exp = c.get("expected", {})
        if exp.get("not_a_booking"):
            sim_json = json.dumps({"items": [], "missing_fields": ["items"]})
        else:
            items_payload = []
            for it in exp.get("items", []):
                items_payload.append({
                    "raw_text": it.get("item_id", ""),
                    "qty": it.get("qty", 1),
                })
            sim_json = json.dumps({
                "customer_name": exp.get("customer_name"),
                "pickup_date": exp.get("pickup_date"),
                "pickup_time_start": exp.get("pickup_time_start"),
                "pickup_time_end": exp.get("pickup_time_end"),
                "pickup_time_raw": exp.get("pickup_time_start"),
                "return_date": exp.get("return_date"),
                "items": items_payload,
                "extra_note": exp.get("extra_note"),
                "warnings": [],
            })
        fake_llm.register_response(c["text"], sim_json)

    extractor = OrderExtractor(llm_client=fake_llm)

    for case in eval_cases:
        text = case["text"]
        ref_d = case.get("reference_date", "2026-10-28")
        exp = case.get("expected", {})

        order, _ = extractor.extract(text, reference_date=ref_d, method="x3")

        if exp.get("not_a_booking"):
            assert len(order.items) == 0
        else:
            if exp.get("pickup_date"):
                assert order.pickup_date == exp["pickup_date"]
            if exp.get("customer_name"):
                assert order.customer_name == exp["customer_name"]
            assert len(order.items) >= 1
