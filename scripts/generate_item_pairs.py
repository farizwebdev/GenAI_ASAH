"""Skrip pembuat dataset pasangan nama alat (item pairs) sesuai PRD Bagian 5.5.

Menghasilkan minimal 150 pasangan variasi teks mentah pelanggan dan item_id katalog toko
dengan variasi salah ketik, singkatan, jumlah unit (qty), dan kapasitas/ukuran.
"""

import csv
import random
from pathlib import Path

SEED = 42
random.seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOG_FILE = BASE_DIR / "data" / "catalog" / "katalog_alat.csv"
OUTPUT_FILE = BASE_DIR / "data" / "synthetic" / "item_pairs.csv"


def inject_typo(word: str) -> str:
    """Menyisipkan variasi salah ketik umum dalam bahasa percakapan santai."""
    replacements = {
        "sleeping bag": "sleeping back",
        "flysheet": "flyseat",
        "headlamp": "hedlamp",
        "carrier": "keril",
        "nesting": "nesteng",
        "matras": "matres",
        "hammock": "hamok",
        "kompor": "kompr",
        "refill": "refil",
        "sepatu": "spatu",
        "tenda": "tnda",
    }
    for orig, typo in replacements.items():
        if orig in word:
            return word.replace(orig, typo)
    return word


def main() -> None:
    """Membaca katalog dan menghasilkan dataset item_pairs.csv minimal 150 baris."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    items = []
    with open(CATALOG_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)

    pairs = []

    # 1. Pasangan berbasis nama resmi dan alias katalog
    for row in items:
        item_id = row["item_id"]
        nama = row["nama"].lower()
        aliases = [a.strip() for a in row["alias"].split("|") if a.strip()]
        kap = row.get("spec_kapasitas") or ""

        # Pasang nama resmi
        pairs.append({"raw_text": nama, "item_id": item_id, "qty_hint": "1", "spec_hint": kap})

        # Pasang alias asli
        for alias in aliases:
            pairs.append({"raw_text": alias, "item_id": item_id, "qty_hint": "1", "spec_hint": kap})

            # Variasi typo
            typo_alias = inject_typo(alias)
            if typo_alias != alias:
                pairs.append({"raw_text": typo_alias, "item_id": item_id, "qty_hint": "1", "spec_hint": kap})

            # Variasi tanpa spasi (contoh "sleepingbag")
            if " " in alias:
                no_space = alias.replace(" ", "")
                pairs.append({"raw_text": no_space, "item_id": item_id, "qty_hint": "1", "spec_hint": kap})

            # Variasi penambahan kuantitas (qty)
            for q in ["2", "3", "4"]:
                pairs.append({
                    "raw_text": f"{alias} {q}",
                    "item_id": item_id,
                    "qty_hint": q,
                    "spec_hint": kap,
                })
                pairs.append({
                    "raw_text": f"{alias} x{q}",
                    "item_id": item_id,
                    "qty_hint": q,
                    "spec_hint": kap,
                })
                pairs.append({
                    "raw_text": f"{q} {alias}",
                    "item_id": item_id,
                    "qty_hint": q,
                    "spec_hint": kap,
                })

    # Hapus duplikat teks mentah
    seen_texts = set()
    unique_pairs = []
    for p in pairs:
        txt = p["raw_text"].strip().lower()
        if txt not in seen_texts:
            seen_texts.add(txt)
            unique_pairs.append(p)

    # Acak dan bagi train (65%) dan test (35%)
    random.shuffle(unique_pairs)
    n_test = int(len(unique_pairs) * 0.35)

    for i, p in enumerate(unique_pairs):
        p["split"] = "test" if i < n_test else "train"

    fieldnames = ["raw_text", "item_id", "qty_hint", "spec_hint", "split"]
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_pairs)

    print(
        f"Berhasil menghasilkan {len(unique_pairs)} baris pasangan item di {OUTPUT_FILE} "
        f"(Test: {n_test}, Train: {len(unique_pairs) - n_test})"
    )


if __name__ == "__main__":
    main()
