"""Pengujian unit otomatis untuk memvalidasi seluruh dataset T-05 dan T-06."""

from scripts.validate_data import (
    validate_catalog,
    validate_extraction_eval,
    validate_intent_dataset,
    validate_item_pairs,
    validate_kb,
    validate_ood,
    validate_rag_eval,
)


def test_t05_and_t06_datasets_are_valid() -> None:
    """Memastikan seluruh dataset dasar dan sintetis lulus validasi PRD."""
    cat_ok, valid_item_ids = validate_catalog()
    assert cat_ok, "Validasi katalog_alat.csv gagal"
    assert len(valid_item_ids) >= 20, "Jumlah alat dalam katalog kurang dari 20"

    kb_ok, valid_kb_ids = validate_kb()
    assert kb_ok, "Validasi kb_toko.md gagal"
    assert len(valid_kb_ids) >= 12, "Jumlah topik KB kurang dari 12"

    assert validate_ood(), "Validasi ood_questions.csv gagal"
    assert validate_rag_eval(valid_kb_ids), "Validasi rag_eval.csv gagal"
    assert validate_extraction_eval(), "Validasi extraction_eval.jsonl gagal"
    assert validate_intent_dataset(), "Validasi intent_dataset.csv gagal"
    assert validate_item_pairs(valid_item_ids), "Validasi item_pairs.csv gagal"
