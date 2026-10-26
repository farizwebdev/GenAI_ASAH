"""Skrip validator data otomatis sesuai PRD Bagian 5 dan Kriteria Penerimaan T-05 & T-06.

Memvalidasi integritas katalog alat, basis pengetahuan toko, data evaluasi, dan data sintetis.
"""

import csv
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CATALOG_PATH = BASE_DIR / "data" / "catalog" / "katalog_alat.csv"
KB_PATH = BASE_DIR / "data" / "kb" / "kb_toko.md"
OOD_PATH = BASE_DIR / "data" / "eval" / "ood_questions.csv"
RAG_EVAL_PATH = BASE_DIR / "data" / "eval" / "rag_eval.csv"
EXTRACTION_EVAL_PATH = BASE_DIR / "data" / "eval" / "extraction_eval.jsonl"
INTENT_DATASET_PATH = BASE_DIR / "data" / "synthetic" / "intent_dataset.csv"
ITEM_PAIRS_PATH = BASE_DIR / "data" / "synthetic" / "item_pairs.csv"

VALID_CATEGORIES = {
    "tenda",
    "tidur",
    "tas",
    "masak",
    "penerangan",
    "alas_kaki",
    "pakaian",
    "aksesori",
    "habis_pakai",
}

VALID_INTENTS = {
    "booking_sewa",
    "tanya_info",
    "ubah_batal",
    "keluhan",
    "lainnya",
}


def validate_catalog() -> tuple[bool, set[str]]:
    """Validasi format dan integritas katalog_alat.csv."""
    errors = []
    item_ids = set()

    if not CATALOG_PATH.is_file():
        return False, set()

    expected_cols = {
        "item_id",
        "nama",
        "kategori",
        "alias",
        "butuh_ukuran",
        "spec_kapasitas",
        "tipe",
        "harga_per_hari_contoh",
        "stok_contoh",
        "source",
    }

    with open(CATALOG_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not expected_cols.issubset(set(reader.fieldnames or [])):
            errors.append(f"Header katalog tidak sesuai: {reader.fieldnames}")

        for i, row in enumerate(reader, start=2):
            iid = row["item_id"].strip()
            if not iid:
                errors.append(f"Baris {i}: item_id kosong")
            elif iid in item_ids:
                errors.append(f"Baris {i}: duplikat item_id '{iid}'")
            item_ids.add(iid)

            kat = row["kategori"].strip()
            if kat not in VALID_CATEGORIES:
                errors.append(f"Baris {i}: kategori '{kat}' tidak valid")

    if errors:
        print("[FAIL] Katalog alat:")
        for err in errors:
            print(f"  - {err}")
        return False, item_ids

    print(f"[OK] Katalog alat: {len(item_ids)} item valid.")
    return True, item_ids


def validate_kb() -> tuple[bool, set[str]]:
    """Validasi format berkas kb_toko.md."""
    if not KB_PATH.is_file():
        print("[FAIL] File kb_toko.md tidak ditemukan.")
        return False, set()

    content = KB_PATH.read_text(encoding="utf-8")
    blocks = [b.strip() for b in content.split("---") if b.strip()]

    kb_ids = set()
    errors = []

    # Setiap entri KB terdiri dari header metadata dan teks isi (dipisah ---)
    for b in blocks:
        for line in b.splitlines():
            if line.startswith("id:"):
                found_id = line.split(":", 1)[1].strip()
                kb_ids.add(found_id)
                break

    # Pastikan minimal 12 topik (KB-01 s/d KB-12)
    expected_kbs = {f"KB-{i:02d}" for i in range(1, 13)}
    missing_kbs = expected_kbs - kb_ids
    if missing_kbs:
        errors.append(f"Topik KB wajib belum lengkap: {missing_kbs}")

    if errors:
        print("[FAIL] Knowledge Base toko:")
        for err in errors:
            print(f"  - {err}")
        return False, kb_ids

    print(f"[OK] Knowledge Base: {len(kb_ids)} topik valid (KB-01 s/d KB-12).")
    return True, kb_ids


def validate_ood() -> bool:
    """Validasi dataset pertanyaan di luar domain (ood_questions.csv)."""
    if not OOD_PATH.is_file():
        print("[FAIL] File ood_questions.csv tidak ditemukan.")
        return False

    with open(OOD_PATH, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if len(reader) < 15:
        print(f"[FAIL] ood_questions.csv minimal 15 baris, ditemukan {len(reader)}.")
        return False

    for row in reader:
        if row.get("expect") != "refuse":
            print(f"[FAIL] ood_questions baris '{row.get('id')}' expect bukan 'refuse'")
            return False

    print(f"[OK] OOD questions: {len(reader)} baris valid.")
    return True


def validate_rag_eval(valid_kb_ids: set[str]) -> bool:
    """Validasi dataset evaluasi RAG (rag_eval.csv)."""
    if not RAG_EVAL_PATH.is_file():
        print("[FAIL] File rag_eval.csv tidak ditemukan.")
        return False

    with open(RAG_EVAL_PATH, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if len(reader) < 20:
        print(f"[FAIL] rag_eval.csv minimal 20 baris, ditemukan {len(reader)}.")
        return False

    for row in reader:
        kb_ref = row.get("expected_kb_ids", "").strip()
        if kb_ref and kb_ref not in valid_kb_ids:
            print(f"[FAIL] RAG eval ID '{row.get('id')}' mereferensikan KB tidak dikenal: {kb_ref}")
            return False

    print(f"[OK] RAG eval: {len(reader)} pertanyaan in-context valid.")
    return True


def validate_extraction_eval() -> bool:
    """Validasi dataset evaluasi ekstraksi draf pesanan booking (extraction_eval.jsonl)."""
    if not EXTRACTION_EVAL_PATH.is_file():
        print("[FAIL] File extraction_eval.jsonl tidak ditemukan.")
        return False

    lines = EXTRACTION_EVAL_PATH.read_text(encoding="utf-8").strip().splitlines()
    if len(lines) < 40:
        print(f"[FAIL] extraction_eval.jsonl minimal 40 kasus, ditemukan {len(lines)}.")
        return False

    for i, line in enumerate(lines, start=1):
        try:
            data = json.loads(line)
            if "id" not in data or "text" not in data or "expected" not in data:
                print(f"[FAIL] extraction_eval baris {i} kehilangan kolom wajib")
                return False
        except Exception as exc:
            print(f"[FAIL] extraction_eval baris {i} bukan format JSON valid: {exc}")
            return False

    print(f"[OK] Extraction eval: {len(lines)} kasus uji valid.")
    return True


def validate_intent_dataset() -> bool:
    """Validasi dataset intent sintetis (intent_dataset.csv)."""
    if not INTENT_DATASET_PATH.is_file():
        print("[FAIL] File intent_dataset.csv tidak ditemukan.")
        return False

    with open(INTENT_DATASET_PATH, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if len(reader) < 500:
        print(f"[FAIL] intent_dataset.csv minimal 500 baris, ditemukan {len(reader)}.")
        return False

    counts: dict[str, int] = {}
    splits: dict[str, int] = {}

    for row in reader:
        lbl = row.get("label", "").strip()
        if lbl not in VALID_INTENTS:
            print(f"[FAIL] Label intent '{lbl}' tidak valid pada ID {row.get('id')}")
            return False
        counts[lbl] = counts.get(lbl, 0) + 1

        s = row.get("split", "").strip()
        splits[s] = splits.get(s, 0) + 1

    for intent in VALID_INTENTS:
        if counts.get(intent, 0) < 100:
            print(f"[FAIL] Intent '{intent}' memiliki sampel < 100 ({counts.get(intent, 0)})")
            return False

    print(
        f"[OK] Intent dataset: {len(reader)} baris valid. "
        f"Distribusi label: {counts}, Splits: {splits}"
    )
    return True


def validate_item_pairs(valid_item_ids: set[str]) -> bool:
    """Validasi dataset pasangan alat (item_pairs.csv)."""
    if not ITEM_PAIRS_PATH.is_file():
        print("[FAIL] File item_pairs.csv tidak ditemukan.")
        return False

    with open(ITEM_PAIRS_PATH, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if len(reader) < 150:
        print(f"[FAIL] item_pairs.csv minimal 150 baris, ditemukan {len(reader)}.")
        return False

    n_test = sum(1 for r in reader if r.get("split") == "test")
    test_ratio = n_test / len(reader)
    if test_ratio < 0.30:
        print(f"[FAIL] Split test item_pairs < 30% ({test_ratio:.2%})")
        return False

    for r in reader:
        iid = r.get("item_id", "").strip()
        if iid not in valid_item_ids:
            print(f"[FAIL] item_pairs memuat item_id tidak valid: '{iid}'")
            return False

    print(
        f"[OK] Item pairs: {len(reader)} baris valid "
        f"(Test: {n_test} / {test_ratio:.1%}, Train: {len(reader) - n_test})."
    )
    return True


def main() -> None:
    """Menjalankan seluruh validasi dataset T-05 dan T-06."""
    print("=== Memulai Validasi Data Proyek Sabana Adventure ===")
    cat_ok, valid_item_ids = validate_catalog()
    kb_ok, valid_kb_ids = validate_kb()
    ood_ok = validate_ood()
    rag_ok = validate_rag_eval(valid_kb_ids)
    ext_ok = validate_extraction_eval()
    intent_ok = validate_intent_dataset()
    pairs_ok = validate_item_pairs(valid_item_ids)

    all_passed = (
        cat_ok
        and kb_ok
        and ood_ok
        and rag_ok
        and ext_ok
        and intent_ok
        and pairs_ok
    )

    if all_passed:
        print("\n>>> SEMUA DATASET LULUS VALIDASI DENGAN SUKSES! (100% OK) <<<")
        sys.exit(0)
    else:
        print("\n>>> DITEMUKAN KESALAHAN PADA DATASET! <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
