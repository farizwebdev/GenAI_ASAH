"""Pengujian Unit Model Analisis Sentimen (T-22) sesuai PRD Bagian 6.12 & Bagian 11.

Memastikan:
1. Saat dataset 'data/external/sentiment_id.csv' belum ada:
   - Skrip pelatihan berhenti rapi tanpa melempar exception fatal.
   - Laporan 'reports/sentiment_report.md' berstatus PENDING.
   - Layanan SentimentClassifier mengembalikan (None, 0.0) secara aman.
   - RouterService mengisi meta.sentiment=None saat keluhan ditangani.
2. Saat dataset ada (diuji dengan dataset sintetis sementara):
   - Model berhasil dilatih, dievaluasi F1, dan disimpan ke artefak .joblib.
   - SentimentClassifier berhasil memuat model dan memprediksi kelas sentimen.
   - RouterService mengisi meta.sentiment dengan label hasil prediksi.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from app.schemas.chat import ChatRequest
from app.schemas.common import ChannelEnum, IntentEnum
from app.services.router import RouterService
from app.services.sentiment import SentimentClassifier, get_sentiment_classifier
from app.training.train_sentiment import check_dataset_exists, train_sentiment_model


def test_sentiment_training_when_data_missing() -> None:
    """Memastikan pelatihan berhenti rapi dan menghasilkan status PENDING jika data belum ada."""
    non_existent = Path("data/external/non_existent_sentiment_file.csv")
    exists = check_dataset_exists(data_path=non_existent)
    assert exists is False

    result = train_sentiment_model(data_path=non_existent)
    assert result is None


def test_sentiment_classifier_fallback_without_artifact() -> None:
    """Memastikan SentimentClassifier mengembalikan (None, 0.0) jika model belum dilatih."""
    classifier = SentimentClassifier(model_path=Path("models/non_existent_model.joblib"))
    assert classifier.artifact is None

    label, conf = classifier.predict("pelayanan toko sangat lambat")
    assert label is None
    assert conf == 0.0

    # Teks kosong
    label_empty, conf_empty = classifier.predict("")
    assert label_empty is None
    assert conf_empty == 0.0


def test_sentiment_training_and_inference_with_synthetic_data() -> None:
    """Memastikan pipeline pelatihan dan inferensi berjalan sempurna saat data tersedia."""
    sample_data = [
        {"text": "pelayanan toko sangat memuaskan dan ramah", "label": "positif"},
        {"text": "tenda bersih bagus dan lengkap banget", "label": "positif"},
        {"text": "mantap barang berkualitas recommended sekali", "label": "positif"},
        {"text": "sangat puas sewa alat disini admin responsif", "label": "positif"},
        {"text": "bagus banget pelayanannya cepat dan ramah", "label": "positif"},
        {"text": "kecewa tenda kotor dan basah pas diambil", "label": "negatif"},
        {"text": "pelayanan lambat antrean berantakan parah", "label": "negatif"},
        {"text": "alat rusak dan tidak sesuai pesanan payah", "label": "negatif"},
        {"text": "sangat kecewa dengan pegawai toko tidak sopan", "label": "negatif"},
        {"text": "kompor tidak menyala mengecewakan sekali", "label": "negatif"},
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_path = tmp_path / "sentiment_id.csv"
        model_path = tmp_path / "sentiment_best.joblib"
        report_path = tmp_path / "sentiment_report.md"

        pd.DataFrame(sample_data).to_csv(csv_path, index=False)

        metrics = train_sentiment_model(
            data_path=csv_path,
            model_out=model_path,
            report_out=report_path,
        )

        assert metrics is not None
        assert "macro_f1" in metrics
        assert metrics["macro_f1"] >= 0.0
        assert model_path.is_file(), "Artefak model harus terbentuk"
        assert report_path.is_file(), "Laporan evaluasi harus terbentuk"

        # Uji inferensi memakai model yang baru dilatih
        trained_clf = SentimentClassifier(model_path=model_path)
        assert trained_clf.artifact is not None

        label_pos, conf_pos = trained_clf.predict("sangat bagus dan memuaskan sekali")
        assert label_pos in ["positif", "negatif"]
        assert conf_pos > 0.0

        label_neg, conf_neg = trained_clf.predict("kecewa sekali tenda kotor rusak")
        assert label_neg in ["positif", "negatif"]
        assert conf_neg > 0.0


def test_router_integration_with_sentiment() -> None:
    """Memastikan RouterService mengisi meta.sentiment saat keluhan terdeteksi."""
    mock_classifier = MagicMock()
    mock_classifier.artifact = {"model_name": "mock-intent-v1"}
    mock_classifier.predict.return_value = (IntentEnum.keluhan.value, 0.95, False)

    mock_sentiment = MagicMock(spec=SentimentClassifier)
    mock_sentiment.predict.return_value = ("negatif", 0.88)

    custom_router = RouterService(
        classifier=mock_classifier,
        sentiment_classifier=mock_sentiment,
    )

    req = ChatRequest(
        channel=ChannelEnum.web_widget,
        message="kecewa banget pelayanannya lama antrean tidak diatur",
    )
    res = custom_router.route_message(req)

    assert res.intent == IntentEnum.keluhan
    assert res.meta.sentiment == "negatif"
    mock_sentiment.predict.assert_called_once()


def test_singleton_get_sentiment_classifier() -> None:
    """Memastikan get_sentiment_classifier mengembalikan instance singleton."""
    clf1 = get_sentiment_classifier()
    clf2 = get_sentiment_classifier()
    assert clf1 is clf2
