"""Modul preprocessing teks untuk normalisasi percakapan chat sesuai PRD Bagian 6.1."""

import re

# Kamus singkatan dan variasi kata percakapan santai ke bentuk baku
_SLANG_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\btgl\b", re.IGNORECASE), "tanggal"),
    (re.compile(r"\byg\b", re.IGNORECASE), "yang"),
    (re.compile(r"\b(?:ga|gak|ngga|nggak)\b", re.IGNORECASE), "tidak"),
    (re.compile(r"\bbwt\b", re.IGNORECASE), "buat"),
    (re.compile(r"\bsy\b", re.IGNORECASE), "saya"),
    (re.compile(r"\bklo\b", re.IGNORECASE), "kalau"),
    (re.compile(r"\butk\b", re.IGNORECASE), "untuk"),
    (re.compile(r"\bdgn\b", re.IGNORECASE), "dengan"),
    (re.compile(r"\bsdh\b", re.IGNORECASE), "sudah"),
    (re.compile(r"\bblm\b", re.IGNORECASE), "belum"),
    # Konteks alat: "sb" -> "sleeping bag"
    (re.compile(r"\bsb\b", re.IGNORECASE), "sleeping bag"),
]

# Regex pembersih tanda baca berlebih untuk intent (menyisakan huruf, angka, spasi)
_PUNCTUATION_INTENT_PATTERN = re.compile(r"[^\w\s]")


def normalize(text: str, mode: str = "for_intent") -> str:
    """Melakukan normalisasi teks pesan pelanggan.

    Aturan normalisasi:
    - Huruf kecil (lowercase).
    - Merapikan spasi berlebih.
    - Mengubah singkatan umum (tgl->tanggal, yg->yang, ga/gak->tidak, sb->sleeping bag).
    - Mempertahankan angka dan satuan ukuran/kapasitas (misal: 60l, kap 4).

    Mode:
    - for_intent: Menghapus tanda baca berlebih dan meratakan baris baru menjadi spasi.
    - for_extract: Mempertahankan baris baru dan label seperti "nama:", "tanggal ambil:".

    Args:
        text: Teks mentah masukan pengguna.
        mode: Mode normalisasi ('for_intent' atau 'for_extract').

    Returns:
        str: Teks hasil normalisasi.
    """
    if not text:
        return ""

    normalized = text.lower()

    # Terapkan kamus singkatan dengan word boundary
    for pattern, replacement in _SLANG_MAP:
        normalized = pattern.sub(replacement, normalized)

    if mode == "for_intent":
        # Hilangkan baris baru menjadi spasi
        normalized = normalized.replace("\r", " ").replace("\n", " ")
        # Hapus tanda baca berlebih untuk pemrosesan klasifikasi n-gram
        normalized = _PUNCTUATION_INTENT_PATTERN.sub(" ", normalized)
        # Rapikan spasi ganda
        normalized = re.sub(r"\s+", " ", normalized).strip()
    elif mode == "for_extract":
        # Rapikan spasi horizontal tanpa menghapus baris baru (\n)
        lines = []
        for line in normalized.splitlines():
            line_clean = re.sub(r"[ \t]+", " ", line).strip()
            if line_clean:
                lines.append(line_clean)
        normalized = "\n".join(lines)
    else:
        raise ValueError(f"Mode normalisasi tidak dikenal: {mode}")

    return normalized
