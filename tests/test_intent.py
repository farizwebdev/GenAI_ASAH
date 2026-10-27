"""Pengujian unit untuk modul Intent Classifier dan inferensi (T-08)."""

from app.services.intent import IntentClassifier, get_intent_classifier


def test_intent_classifier_prediction_classes() -> None:
    """Memastikan IntentClassifier dapat mengenali kelas intent utama."""
    classifier = get_intent_classifier()

    # 1. Booking sewa
    text_booking = (
        "Nama: Rizky\nTanggal ambil: 31 Oktober\nJam: 09.00\n"
        "List barang: tenda kap 4, carrier 60L"
    )
    label, conf, low_conf = classifier.predict(text_booking)
    assert label == "booking_sewa"
    assert conf >= 0.5
    assert low_conf is False

    # 2. Tanya info
    text_info = "sewa 3 hari dihitung berapa hari ya kak?"
    label, conf, low_conf = classifier.predict(text_info)
    assert label == "tanya_info"
    assert conf >= 0.5
    assert low_conf is False

    # 3. Ubah / Batal
    text_ubah = "kak saya mau ubah tanggal ambil sewa kemarin jadi besok minggu bisa?"
    label, conf, low_conf = classifier.predict(text_ubah)
    assert label == "ubah_batal"
    assert conf >= 0.5
    assert low_conf is False

    # 4. Keluhan
    text_keluhan = "kak tenda yang kemarin disewa bocor pas hujan, air masuk semua!"
    label, conf, low_conf = classifier.predict(text_keluhan)
    assert label == "keluhan"
    assert conf >= 0.5
    assert low_conf is False

    # 5. Lainnya (sapaan / ucapan terima kasih)
    text_lainnya = "terima kasih banyak ya kak atas bantuannya"
    label, conf, low_conf = classifier.predict(text_lainnya)
    assert label == "lainnya"
    assert conf >= 0.5
    assert low_conf is False


def test_intent_classifier_low_confidence_fallback() -> None:
    """Memastikan pesan ambigu atau confidence rendah jatuh ke fallback 'lainnya'."""
    classifier = IntentClassifier()
    # Atur min_confidence sangat tinggi (misal 0.999) untuk menguji kondisi batas
    classifier.min_confidence = 0.999

    label, conf, low_conf = classifier.predict("halo")
    assert label == "lainnya"
    assert low_conf is True


def test_intent_classifier_empty_text() -> None:
    """Memastikan teks kosong langsung mengembalikan 'lainnya'."""
    classifier = get_intent_classifier()
    label, conf, low_conf = classifier.predict("")
    assert label == "lainnya"
    assert conf == 0.0
    assert low_conf is True
