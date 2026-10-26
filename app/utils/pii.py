"""Utilitas penyembunyian data pribadi (PII) untuk logging dan pemrosesan aman."""

import re

# Pola nomor telepon Indonesia (+62..., 08..., 628...) dengan panjang 9-15 digit
_PHONE_PATTERN = re.compile(
    r"(?:\+?62|0)8[1-9][0-9]{7,11}\b|\b08\d{8,11}\b",
    re.IGNORECASE,
)

# Pola nomor identitas (NIK / KTP 16 digit)
_NIK_PATTERN = re.compile(r"\b\d{16}\b")

# Pola nama dalam format booking WhatsApp (contoh: "Nama: Rizky")
_NAME_FIELD_PATTERN = re.compile(
    r"(?i)(nama\s*:\s*)([^\r\n,]+)",
)


def mask_pii(text: str) -> str:
    """Menyensor data pribadi seperti nomor telepon, NIK, dan nama dari teks.

    Args:
        text: Teks mentah yang mungkin mengandung data pribadi pelanggan.

    Returns:
        Teks yang sudah disensor untuk keperluan logging aman.
    """
    if not text:
        return text

    # Sensor nomor telepon
    censored = _PHONE_PATTERN.sub("[MASKED_PHONE]", text)

    # Sensor NIK / identitas angka 16 digit
    censored = _NIK_PATTERN.sub("[MASKED_NIK]", censored)

    # Sensor isian label nama
    censored = _NAME_FIELD_PATTERN.sub(r"\1[MASKED_NAME]", censored)

    return censored
