"""Skrip evaluasi model intent pada data uji independen (Test Split) sesuai PRD T-10."""

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from app.services.preprocessing import normalize

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "synthetic" / "intent_dataset.csv"
MODEL_PATH = BASE_DIR / "models" / "intent_best.joblib"
REPORT_DIR = BASE_DIR / "reports"


def main() -> None:
    """Mengevaluasi model terbaik pada data uji test split dan menyimpan laporannya."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Artefak model {MODEL_PATH} tidak ditemukan. "
            "Jalankan train_intent.py atau augment_and_tune.py terlebih dahulu."
        )

    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    model_name = artifact.get("model_name", "intent_model")
    classes = artifact["classes"]

    df = pd.read_csv(DATA_PATH)
    test_df = df[df["split"] == "test"].copy()

    X_test_clean = test_df["text"].apply(
        lambda t: normalize(str(t), mode="for_intent")
    ).tolist()
    y_true = test_df["label"].tolist()

    start_t = time.perf_counter()
    y_pred = model.predict(X_test_clean)
    elapsed_ms = (time.perf_counter() - start_t) * 1000 / len(X_test_clean)

    # Hitung metrik evaluasi
    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted"))
    clf_report_dict = classification_report(
        y_true, y_pred, labels=classes, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=classes)

    # Simpan laporan JSON
    report_json = {
        "model_name": model_name,
        "n_test_samples": len(test_df),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "latency_ms_per_sample": round(elapsed_ms, 3),
        "classification_report": clf_report_dict,
        "confusion_matrix": cm.tolist(),
        "classes": classes,
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    json_path = REPORT_DIR / "test_evaluation_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    # Simpan laporan Markdown
    lines = [
        "# Laporan Evaluasi Data Uji Final (T-10)",
        "",
        "Diproduksi otomatis oleh `app/training/evaluate.py` sesuai PRD Bagian 11 (T-10).",
        "Evaluasi dilakukan murni pada data uji (*test split*) yang tidak pernah disentuh",
        "saat proses pelatihan.",
        "",
        "## 1. Ringkasan Metrik Evaluasi Data Uji",
        "",
        f"- **Model Dievaluasi:** `{model_name}`",
        f"- **Jumlah Sampel Uji:** {len(test_df)}",
        f"- **Test Macro-F1:** `{macro_f1:.4f}`",
        f"- **Test Weighted-F1:** `{weighted_f1:.4f}`",
        f"- **Latensi Inferensi:** `{elapsed_ms:.3f} ms/sampel`",
        "",
        "## 2. Rincian Metrik per Kelas",
        "",
        "| Kelas Intent | Precision | Recall | F1-Score | Support |",
        "|---|---|---|---|---|",
    ]

    for cls in classes:
        cls_metrics = clf_report_dict.get(cls, {})
        p = cls_metrics.get("precision", 0.0)
        r = cls_metrics.get("recall", 0.0)
        f1 = cls_metrics.get("f1-score", 0.0)
        supp = cls_metrics.get("support", 0)
        lines.append(f"| `{cls}` | {p:.4f} | {r:.4f} | {f1:.4f} | {supp} |")

    lines.extend([
        "",
        "## 3. Matriks Kebingungan (Confusion Matrix) pada Data Uji",
        "",
        f"Kelas: `{', '.join(classes)}`",
        "",
        "```text",
        np.array2string(cm, separator=", "),
        "```",
        "",
    ])

    md_path = REPORT_DIR / "test_evaluation_report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Evaluasi selesai! Laporan dibuat di: {json_path} dan {md_path}")
    print(f"Hasil Test Macro-F1: {macro_f1:.4f} (Support: {len(test_df)} sampel)")


if __name__ == "__main__":
    main()
