"""Skrip Pelatihan Model Analisis Sentimen (P2) sesuai PRD Bagian 6.12 & Bagian 11 (T-22).

Aturan PRD:
1. Membaca dataset eksternal: data/external/sentiment_id.csv (kolom 'text', 'label').
2. Jika berkas data tidak ada: skrip berhenti rapi (tanpa crash), memberikan pesan jelas,
   dan mencatat di TODO_HUMAN.md (jangan mengunduh dataset sendiri tanpa lisensi).
3. Jika berkas data ada: latih model klasifikasi sentimen biner (positif/negatif),
   evaluasi metrik Macro F1, simpan model ke models/sentiment_best.joblib,
   serta buat laporan evaluasi di reports/sentiment_report.md.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.core.logging import get_logger
from app.services.preprocessing import normalize

logger = get_logger(__name__)

SEED = 42
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "external" / "sentiment_id.csv"
MODEL_PATH = BASE_DIR / "models" / "sentiment_best.joblib"
REPORT_PATH = BASE_DIR / "reports" / "sentiment_report.md"
TODO_PATH = BASE_DIR / "TODO_HUMAN.md"


def check_dataset_exists(data_path: Path | None = None) -> bool:
    """Memeriksa keberadaan berkas dataset sentimen eksternal.

    Jika berkas tidak ditemukan, skrip mencatat instruksi pada TODO_HUMAN.md
    dan menghasilkan laporan berstatus PENDING di reports/sentiment_report.md.
    """
    path = data_path or DATA_PATH
    if path.is_file():
        return True

    try:
        rel_path = str(path.resolve().relative_to(BASE_DIR.resolve()))
    except ValueError:
        rel_path = path.name

    msg = (
        f"[PERINGATAN T-22] Berkas dataset sentimen '{rel_path}' belum tersedia.\n"
        "Sesuai PRD Bagian 6.12 & Bagian 15, agen dilarang mengunduh dataset publik sendiri.\n"
        "Dataset bahasa Indonesia berlisensi jelas harus disediakan secara manual oleh manusia."
    )
    print("=" * 70)
    print(msg)
    print("=" * 70)
    logger.warning(msg)

    # Pastikan status tercatat di reports/sentiment_report.md
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report_content = (
        "# Laporan Model Analisis Sentimen Pelanggan (P2)\n\n"
        f"**Tanggal Pemeriksaan:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "**Status:** MENUNGGU DATASET MANUSIA (`PENDING`)\n\n"
        "## Catatan Kepatuhan PRD Bagian 6.12 & 15\n"
        "Berkas `data/external/sentiment_id.csv` belum disediakan. AI coding agent "
        "tidak diperbolehkan mengunduh dataset eksternal tanpa verifikasi lisensi oleh manusia.\n\n"
        "### Tindakan yang Dibutuhkan:\n"
        "1. Sediakan dataset di `data/external/sentiment_id.csv` dengan kolom `text,label`.\n"
        "2. Label yang didukung: `positif`, `negatif`.\n"
        "3. Cantumkan sumber dan lisensi data pada `README.md`.\n"
        "4. Jalankan ulang pelatihan dengan: `python -m app.training.train_sentiment`\n"
    )
    REPORT_PATH.write_text(report_content, encoding="utf-8")

    # Pastikan TODO_HUMAN.md mencatat kebutuhan dataset ini
    if TODO_PATH.is_file():
        todo_text = TODO_PATH.read_text(encoding="utf-8")
        if "sentiment_id.csv" not in todo_text:
            append_entry = (
                "| H-07 | Dataset Sentimen Bahasa Indonesia (P2) | Menunggu | "
                "Bagian 6.12 & T-22: File `data/external/sentiment_id.csv` harus disediakan "
                "manual dengan lisensi jelas. |\n"
            )
            TODO_PATH.write_text(todo_text + append_entry, encoding="utf-8")

    return False


def train_sentiment_model(
    data_path: Path | None = None,
    model_out: Path | None = None,
    report_out: Path | None = None,
) -> dict[str, Any] | None:
    """Melatih pipeline klasifikasi sentimen jika data tersedia.

    Args:
        data_path: Path kustom ke dataset CSV (opsional).
        model_out: Path penyimpanan model artifact (opsional).
        report_out: Path penyimpanan laporan evaluasi (opsional).

    Returns:
        dict berisi metrik evaluasi atau None jika data belum ada.
    """
    target_data = data_path or DATA_PATH
    target_model = model_out or MODEL_PATH
    target_report = report_out or REPORT_PATH

    if not check_dataset_exists(target_data):
        return None

    logger.info(f"Membaca dataset sentimen dari {target_data}...")
    df = pd.read_csv(target_data)

    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError(
            f"Dataset di {target_data} wajib memiliki kolom 'text' dan 'label'. "
            f"Kolom ditemukan: {list(df.columns)}"
        )

    # Bersihkan nilai NaN dan normalisasi teks
    df = df.dropna(subset=["text", "label"]).copy()
    df["clean_text"] = df["text"].apply(lambda t: normalize(str(t), mode="for_intent"))
    df = df[df["clean_text"].str.strip() != ""].copy()

    total_samples = len(df)
    logger.info(f"Total sampel valid untuk pelatihan sentimen: {total_samples}")

    X = df["clean_text"].tolist()
    y = df["label"].astype(str).str.lower().str.strip().tolist()

    # Split dataset 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=SEED,
        stratify=y if len(set(y)) > 1 else None,
    )

    # Bangun Pipeline TF-IDF + LogisticRegression
    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=4000,
                sublinear_tf=True,
            ),
        ),
        (
            "clf",
            LogisticRegression(
                C=1.0,
                random_state=SEED,
                max_iter=500,
            ),
        ),
    ])

    logger.info("Memulai pelatihan model sentimen...")
    pipeline.fit(X_train, y_train)

    # Prediksi dan evaluasi
    y_pred = pipeline.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    macro_precision = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    macro_recall = float(recall_score(y_test, y_pred, average="macro", zero_division=0))

    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    metrics: dict[str, Any] = {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "classes": list(pipeline.classes_),
    }

    # Simpan Artefak Model
    target_model.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": pipeline,
        "model_name": "sentiment-logreg-v1",
        "classes": list(pipeline.classes_),
        "metrics": metrics,
        "trained_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    joblib.dump(artifact, target_model)
    logger.info(f"Artefak model sentimen berhasil disimpan di {target_model}")

    # Buat Laporan Evaluasi Markdown
    target_report.parent.mkdir(parents=True, exist_ok=True)
    rows_md: list[str] = []
    for cls_name in pipeline.classes_:
        cls_metrics = report_dict.get(cls_name, {})
        p = cls_metrics.get("precision", 0.0)
        r = cls_metrics.get("recall", 0.0)
        f = cls_metrics.get("f1-score", 0.0)
        sup = int(cls_metrics.get("support", 0))
        rows_md.append(f"| `{cls_name}` | {p:.4f} | {r:.4f} | {f:.4f} | {sup} |")

    report_content = (
        "# Laporan Evaluasi Model Analisis Sentimen (P2)\n\n"
        f"**Model Name:** `sentiment-logreg-v1`  \n"
        f"**Waktu Pelatihan:** {artifact['trained_at']}  \n"
        f"**Total Data:** {total_samples} sampel (Train: {len(X_train)}, Test: {len(X_test)})  \n"
        f"**Algoritma:** TF-IDF (1-2 gram) + LogisticRegression (C=1.0, random_state={SEED})  \n\n"
        "## Ringkasan Kinerja Utama\n\n"
        f"- **Akurasi:** `{accuracy * 100:.2f}%`\n"
        f"- **Macro F1:** `{macro_f1:.4f}`\n"
        f"- **Weighted F1:** `{weighted_f1:.4f}`\n"
        f"- **Macro Precision:** `{macro_precision:.4f}`\n"
        f"- **Macro Recall:** `{macro_recall:.4f}`\n\n"
        "## Kinerja Per-Kelas\n\n"
        "| Kelas Sentimen | Precision | Recall | F1-Score | Support |\n"
        "|---|---|---|---|---|\n"
        + "\n".join(rows_md)
        + "\n\n"
        "## Catatan Integrasi Produk\n"
        "- Model ini digunakan secara kondisional saat intent percakapan terklasifikasi sebagai "
        "`keluhan` (PRD Bagian 6.9 & 6.12).\n"
        "- Hasil prediksi dicantumkan pada field `meta.sentiment` dalam respons API.\n"
    )
    target_report.write_text(report_content, encoding="utf-8")
    logger.info(f"Laporan evaluasi sentimen berhasil ditulis di {target_report}")

    print("\n" + "=" * 65)
    print("  PELATIHAN MODEL SENTIMEN BERHASIL!")
    print(f"  Macro F1 : {macro_f1:.4f}")
    print(f"  Akurasi  : {accuracy * 100:.2f}%")
    print(f"  Model    : {target_model.name}")
    print(f"  Laporan  : {target_report.name}")
    print("=" * 65 + "\n")

    return metrics


def main() -> None:
    """Entry point CLI untuk pelatihan model sentimen."""
    metrics = train_sentiment_model()
    if metrics is None:
        # Berhenti rapi dengan kode 0 sesuai instruksi PRD
        sys.exit(0)


if __name__ == "__main__":
    main()
