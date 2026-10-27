"""Pengujian unit otomatis untuk memvalidasi hasil tugas T-09 dan T-10."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"
MODEL_PATH = BASE_DIR / "models" / "intent_best.joblib"


def test_t09_reports_exist() -> None:
    """Memastikan laporan keseimbangan kelas dan improvement (T-09) dibuat."""
    cb_path = REPORT_DIR / "class_balance.md"
    imp_path = REPORT_DIR / "improvement.md"

    assert cb_path.is_file(), "File reports/class_balance.md tidak ditemukan"
    assert imp_path.is_file(), "File reports/improvement.md tidak ditemukan"

    cb_content = cb_path.read_text(encoding="utf-8")
    assert "booking_sewa" in cb_content
    assert "Rasio Peningkatan" in cb_content

    imp_content = imp_path.read_text(encoding="utf-8")
    assert "Perbandingan Sebelum vs Sesudah Tuning" in imp_content


def test_t10_evaluation_report() -> None:
    """Memastikan laporan evaluasi data uji (T-10) valid dan memiliki F1 tinggi."""
    json_path = REPORT_DIR / "test_evaluation_report.json"
    md_path = REPORT_DIR / "test_evaluation_report.md"

    assert json_path.is_file(), "File reports/test_evaluation_report.json tidak ditemukan"
    assert md_path.is_file(), "File reports/test_evaluation_report.md tidak ditemukan"

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    assert "macro_f1" in data
    assert data["macro_f1"] >= 0.85, f"Macro F1 pada test split terlalu rendah: {data['macro_f1']}"
    assert data["n_test_samples"] > 0
    assert len(data["classes"]) == 5
