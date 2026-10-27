"""Layanan inferensi Intent Classifier Sabana Adventure sesuai PRD Bagian 6.2."""

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger
from app.embeddings.base import get_embedder
from app.services.preprocessing import normalize

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "intent_best.joblib"


class IntentClassifier:
    """Model klasifikasi maksud pesan (5 kelas) dengan penanganan ambang batas confidence."""

    def __init__(self, model_path: Path | None = None) -> None:
        settings = get_settings()
        self.min_confidence = settings.INTENT_MIN_CONF
        self.model_path = model_path or MODEL_PATH
        self.artifact: dict[str, Any] | None = None
        self._load_model()

    def _load_model(self) -> None:
        """Memuat artefak model terbaik yang telah dilatih."""
        if not self.model_path.is_file():
            logger.warning(
                f"Artefak model {self.model_path} tidak ditemukan. "
                "Jalankan train_intent.py terlebih dahulu."
            )
            return

        try:
            self.artifact = joblib.load(self.model_path)
            logger.info(
                f"Model intent berhasil dimuat: {self.artifact.get('model_name')} "
                f"dari {self.model_path}"
            )
        except Exception as exc:
            logger.error(f"Gagal memuat model intent: {exc}")
            self.artifact = None

    def predict(self, raw_text: str) -> tuple[str, float, bool]:
        """Memprediksi kelas intent dari teks pesan pelanggan.

        Args:
            raw_text: Teks mentah masukan pengguna.

        Returns:
            tuple: (label_intent, confidence, low_confidence_flag)
        """
        clean_text = normalize(raw_text, mode="for_intent")
        if not clean_text:
            return "lainnya", 0.0, True

        if self.artifact is None:
            # Fallback jika model belum dilatih
            logger.warning("Model intent belum tersedia, menggunakan fallback 'lainnya'")
            return "lainnya", 0.0, True

        model = self.artifact["model"]
        is_e3 = self.artifact.get("is_e3", False)

        try:
            if is_e3:
                embedder = get_embedder()
                vec = np.array([embedder.embed_text(clean_text)])
                probs = model.predict_proba(vec)[0]
                classes = model.classes_
            else:
                probs = model.predict_proba([clean_text])[0]
                classes = model.classes_

            best_idx = int(np.argmax(probs))
            confidence = float(probs[best_idx])
            predicted_label = str(classes[best_idx])

            # PRD 6.2: Bila confidence < INTENT_MIN_CONF,
            # kembalikan 'lainnya' dengan flag low_confidence=True
            if confidence < self.min_confidence:
                return "lainnya", confidence, True

            return predicted_label, confidence, False

        except Exception as exc:
            logger.error(f"Error saat inferensi intent: {exc}")
            return "lainnya", 0.0, True


_classifier_instance: IntentClassifier | None = None


def get_intent_classifier() -> IntentClassifier:
    """Mengambil instance singleton IntentClassifier."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier()
    return _classifier_instance
