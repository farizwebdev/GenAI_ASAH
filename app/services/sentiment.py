"""Layanan Inferensi Model Analisis Sentimen (P2) sesuai PRD Bagian 6.12."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.core.logging import get_logger
from app.services.preprocessing import normalize

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "sentiment_best.joblib"


class SentimentClassifier:
    """Layanan inferensi untuk mendeteksi sentimen pesan pelanggan (fitur P2)."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = model_path or MODEL_PATH
        self.artifact: dict[str, Any] | None = None
        self._load_model()

    def _load_model(self) -> None:
        """Memuat artefak model sentimen jika berkas tersedia."""
        if not self.model_path.is_file():
            logger.info(
                f"Model sentimen {self.model_path.name} belum tersedia (menunggu dataset T-22)."
            )
            self.artifact = None
            return

        try:
            self.artifact = joblib.load(self.model_path)
            model_name = self.artifact.get("model_name", "sentiment-model")
            logger.info(f"Model sentimen berhasil dimuat: {model_name} dari {self.model_path}")
        except Exception as exc:
            logger.error(f"Gagal memuat model sentimen: {exc}")
            self.artifact = None

    def predict(self, raw_text: str) -> tuple[str | None, float]:
        """Menganalisis dan memprediksi kelas sentimen dari teks masukan.

        Args:
            raw_text: Teks mentah masukan pengguna/pelanggan.

        Returns:
            tuple: (label_sentimen, confidence) atau (None, 0.0) jika model belum ada.
        """
        if self.artifact is None:
            return None, 0.0

        clean_text = normalize(raw_text, mode="for_intent")
        if not clean_text:
            return None, 0.0

        model = self.artifact["model"]
        try:
            probs = model.predict_proba([clean_text])[0]
            classes = model.classes_
            best_idx = int(np.argmax(probs))
            label = str(classes[best_idx])
            confidence = float(probs[best_idx])
            return label, confidence
        except Exception as exc:
            logger.error(f"Gagal melakukan inferensi sentimen: {exc}")
            return None, 0.0


_sentiment_instance: SentimentClassifier | None = None


def get_sentiment_classifier() -> SentimentClassifier:
    """Mengambil instance singleton SentimentClassifier."""
    global _sentiment_instance
    if _sentiment_instance is None:
        _sentiment_instance = SentimentClassifier()
    return _sentiment_instance
