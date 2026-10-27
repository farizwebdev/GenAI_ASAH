"""Skrip pelatihan dan perbandingan model intent klasifikasi E1 - E3 sesuai PRD Bagian 6.2."""

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from app.embeddings.base import get_embedder
from app.services.preprocessing import normalize

SEED = 42
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "synthetic" / "intent_dataset.csv"
MODEL_DIR = BASE_DIR / "models"
REPORT_DIR = BASE_DIR / "reports"


def load_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Memuat dan memisahkan dataset intent berdasarkan split."""
    df = pd.read_csv(DATA_PATH)
    # Terapkan normalisasi teks for_intent
    df["clean_text"] = df["text"].apply(lambda t: normalize(str(t), mode="for_intent"))

    train_df = df[df["split"] == "train"].copy()
    val_df = df[df["split"] == "val"].copy()
    test_df = df[df["split"] == "test"].copy()

    return train_df, val_df, test_df


def train_e1(X_train: list[str], y_train: list[str]) -> Pipeline:
    """E1: TF-IDF kata+karakter n-gram + LogisticRegression (Baseline)."""
    pipe = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
            ),
        ),
        (
            "clf",
            LogisticRegression(
                random_state=SEED,
                max_iter=1000,
                C=1.0,
            ),
        ),
    ])
    pipe.fit(X_train, y_train)
    return pipe


def train_e2(X_train: list[str], y_train: list[str]) -> Pipeline:
    """E2: TF-IDF + LinearSVC (dikalibrasi dengan CalibratedClassifierCV untuk probabilitas)."""
    base_svc = LinearSVC(random_state=SEED, C=1.0, dual="auto")
    calibrated_svc = CalibratedClassifierCV(estimator=base_svc, cv=3)

    pipe = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
            ),
        ),
        ("clf", calibrated_svc),
    ])
    pipe.fit(X_train, y_train)
    return pipe


def train_e3(
    X_train: list[str], y_train: list[str], embedder
) -> tuple[LogisticRegression, object]:
    """E3: Teks Embedding + LogisticRegression."""
    X_train_vecs = np.array(embedder.embed_batch(X_train))
    clf = LogisticRegression(random_state=SEED, max_iter=1000, C=1.0)
    clf.fit(X_train_vecs, y_train)
    return clf, embedder


def evaluate_model(model_tuple, X_texts: list[str], y_true: list[str], is_e3: bool = False):
    """Evaluasi model: menghitung macro-F1, F1 per kelas, dan latensi inferensi."""
    start_t = time.perf_counter()

    if is_e3:
        clf, embedder = model_tuple
        X_vecs = np.array(embedder.embed_batch(X_texts))
        y_pred = clf.predict(X_vecs)
    else:
        y_pred = model_tuple.predict(X_texts)

    elapsed_ms = (time.perf_counter() - start_t) * 1000 / len(X_texts)

    classes = sorted(set(y_true))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))
    class_f1s = f1_score(y_true, y_pred, labels=classes, average=None)
    f1_per_class = {cls: float(score) for cls, score in zip(classes, class_f1s, strict=False)}

    return macro_f1, f1_per_class, elapsed_ms, y_pred


def build_markdown_report(best_name: str, classes: list[str], results: dict, best_cm) -> str:
    """Menyusun teks laporan Markdown yang rapi dan compliant dengan batas baris."""
    lines = [
        "# Laporan Pelatihan Model Intent Klasifikasi (E1 - E3)",
        "",
        "Diproduksi secara otomatis oleh `app/training/train_intent.py` sesuai PRD Bagian 6.2.",
        "",
        "## 1. Tabel Perbandingan Model",
        "",
        "| Konfigurasi | Arsitektur | Val Macro-F1 | Test Macro-F1 | Latensi (ms) | Status |",
        "|---|---|---|---|---|---|",
    ]

    names_map = {
        "E1": "TF-IDF + LogisticRegression",
        "E2": "TF-IDF + LinearSVC",
        "E3": "Embedding + LogisticRegression",
    }

    for cfg, info in results.items():
        status = "⭐ **Terpilih**" if cfg == best_name else "Kandidat"
        desc = names_map.get(cfg, cfg)
        val_f1 = f"{info['val_macro_f1']:.4f}"
        test_f1 = f"{info['test_macro_f1']:.4f}"
        lat = f"{info['latency_ms_per_sample']:.3f} ms"
        lines.append(f"| **{cfg}** | {desc} | {val_f1} | {test_f1} | {lat} | {status} |")

    lines.extend([
        "",
        "*Model terbaik dipilih berdasarkan skor tertinggi pada dataset **Validation (Val)**.*",
        "",
        f"## 2. Kinerja per Kelas Model Terbaik ({best_name})",
        "",
        "| Kelas Intent | F1-Score pada Test |",
        "|---|---|",
    ])

    for cls in classes:
        score = results[best_name]["test_f1_per_class"].get(cls, 0.0)
        lines.append(f"| `{cls}` | {score:.4f} |")

    lines.extend([
        "",
        f"## 3. Matriks Kebingungan (Confusion Matrix) Model Terbaik ({best_name})",
        "",
        f"Kelas: `{', '.join(classes)}`",
        "",
        "```text",
        np.array2string(best_cm, separator=", "),
        "```",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    """Melatih konfigurasi E1, E2, E3, memilih terbaik via val, dan melaporkan di test."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Memuat dataset intent...")
    train_df, val_df, test_df = load_dataset()
    print(f"Data split: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    X_train, y_train = train_df["clean_text"].tolist(), train_df["label"].tolist()
    X_val, y_val = val_df["clean_text"].tolist(), val_df["label"].tolist()
    X_test, y_test = test_df["clean_text"].tolist(), test_df["label"].tolist()

    classes = sorted(set(y_train))

    # 1. Latih E1
    print("\nMelatih E1 (TF-IDF + LogisticRegression)...")
    model_e1 = train_e1(X_train, y_train)
    val_f1_e1, _, _, _ = evaluate_model(model_e1, X_val, y_val, is_e3=False)

    # 2. Latih E2
    print("Melatih E2 (TF-IDF + LinearSVC)...")
    model_e2 = train_e2(X_train, y_train)
    val_f1_e2, _, _, _ = evaluate_model(model_e2, X_val, y_val, is_e3=False)

    # 3. Latih E3
    print("Melatih E3 (Embedding + LogisticRegression)...")
    embedder = get_embedder()
    model_e3 = train_e3(X_train, y_train, embedder)
    val_f1_e3, _, _, _ = evaluate_model(model_e3, X_val, y_val, is_e3=True)

    val_scores = {
        "E1": (val_f1_e1, model_e1, False),
        "E2": (val_f1_e2, model_e2, False),
        "E3": (val_f1_e3, model_e3, True),
    }

    # Aturan PRD: Pilih model terbaik memakai VAL, laporkan di TEST
    best_name = max(val_scores, key=lambda k: val_scores[k][0])
    best_val_f1, best_model_obj, best_is_e3 = val_scores[best_name]

    print(
        f"\nHasil Val Macro-F1: E1={val_f1_e1:.4f}, E2={val_f1_e2:.4f}, E3={val_f1_e3:.4f}"
    )
    print(f"Model terbaik yang dipilih (via Val): {best_name} (Macro-F1: {best_val_f1:.4f})")

    # Evaluasi semua model pada TEST untuk pelaporan objektif
    results = {}
    best_cm = None

    for name, (_, model_obj, is_e3) in val_scores.items():
        macro_f1, f1_per_class, latency_ms, y_pred = evaluate_model(
            model_obj, X_test, y_test, is_e3=is_e3
        )
        results[name] = {
            "val_macro_f1": round(val_scores[name][0], 4),
            "test_macro_f1": round(macro_f1, 4),
            "test_f1_per_class": {k: round(v, 4) for k, v in f1_per_class.items()},
            "latency_ms_per_sample": round(latency_ms, 3),
        }
        if name == best_name:
            best_cm = confusion_matrix(y_test, y_pred, labels=classes)

    # Simpan model terbaik ke models/intent_best.joblib
    artifact = {
        "model_name": best_name,
        "is_e3": best_is_e3,
        "model": best_model_obj[0] if best_is_e3 else best_model_obj,
        "classes": classes,
        "metrics": results[best_name],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    model_output_path = MODEL_DIR / "intent_best.joblib"
    joblib.dump(artifact, model_output_path)
    print(f"Model terbaik berhasil disimpan ke: {model_output_path}")

    # Simpan laporan JSON
    report_data = {
        "best_model": best_name,
        "classes": classes,
        "comparison": results,
        "confusion_matrix_best": best_cm.tolist() if best_cm is not None else [],
    }
    json_path = REPORT_DIR / "intent_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Simpan laporan Markdown
    md_content = build_markdown_report(best_name, classes, results, best_cm)
    md_path = REPORT_DIR / "intent_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Laporan berhasil dibuat di: {json_path} dan {md_path}")


if __name__ == "__main__":
    main()
