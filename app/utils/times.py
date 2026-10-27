"""Utilitas parsing jam dan validasi jam buka toko untuk Sabana Adventure.

Sesuai PRD Bagian 6.5:
- Jam operasional toko: 08:00 - 21:00.
- Di luar jam operasional -> ditandai dalam warnings (bukan error).
- Mendukung: '08.00-10.00', 'jam 9 pagi', 'jam 4 sore', 'jam 7 malem', '10an', 'siang'.
- Kata 'pagi/siang/sore/malam' tanpa jam -> rentang jam perkiraan bawaan:
  pagi (08:00-11:00), siang (11:00-15:00), sore (15:00-18:00), malam (18:00-21:00).
"""

from __future__ import annotations

import re

STORE_OPEN_TIME = "08:00"
STORE_CLOSE_TIME = "21:00"

# Rentang jam perkiraan bawaan sesuai PRD 6.5
DEFAULT_PERIOD_RANGES: dict[str, tuple[str, str]] = {
    "pagi": ("08:00", "11:00"),
    "siang": ("11:00", "15:00"),
    "sore": ("15:00", "18:00"),
    "malam": ("18:00", "21:00"),
    "malem": ("18:00", "21:00"),
}


def _check_store_hours(start: str | None, end: str | None, warnings: list[str]) -> None:
    """Memeriksa apakah jam berada di luar jam operasional toko 08:00-21:00."""
    out_of_hours = False
    if start and (start < STORE_OPEN_TIME or start > STORE_CLOSE_TIME):
        out_of_hours = True
    if end and (end < STORE_OPEN_TIME or end > STORE_CLOSE_TIME):
        out_of_hours = True

    if out_of_hours:
        warnings.append(f"di luar jam buka toko ({STORE_OPEN_TIME}-{STORE_CLOSE_TIME})")


def _format_time_component(hour: int, minute: int) -> str:
    """Memformat jam dan menit menjadi HH:MM."""
    return f"{hour:02d}:{minute:02d}"


def parse_time(time_text: str) -> tuple[str | None, str | None, list[str]]:
    """Mem-parsing teks jam menjadi format (start_time, end_time, warnings).

    Format output: (HH:MM | None, HH:MM | None, list[str]).

    Args:
        time_text: Teks mentah waktu (misal: '08.00-10.00', 'jam 4 sore', '10an', 'pagi').

    Returns:
        tuple[str | None, str | None, list[str]]: (start_time, end_time, warnings)
    """
    if not time_text or not time_text.strip():
        return None, None, ["teks jam kosong"]

    text = time_text.strip().lower()
    warnings: list[str] = []

    # 1. Cek rentang eksplisit: "08.00-10.00", "08:00 - 10:00", dsb.
    range_match = re.search(
        r"(\d{1,2})[:.](\d{2})\s*(?:-|–|s/d|sd|sampai|hingga)\s*(\d{1,2})[:.](\d{2})",
        text,
    )
    if range_match:
        h1, m1 = int(range_match.group(1)), int(range_match.group(2))
        h2, m2 = int(range_match.group(3)), int(range_match.group(4))
        start_t = _format_time_component(h1, m1)
        end_t = _format_time_component(h2, m2)
        _check_store_hours(start_t, end_t, warnings)
        return start_t, end_t, warnings

    # 2. Cek jam perkiraan akhiran "-an" (misal: "10an", "jam 10an", "14an")
    approx_match = re.search(r"(?:jam\s*)?(\d{1,2})\s*an\b", text)
    if approx_match:
        h = int(approx_match.group(1))
        # Jika ada indikator sore/malam
        if ("sore" in text or "malam" in text or "malem" in text) and h < 12:
            h += 12
        elif "siang" in text and h <= 5:
            h += 12
        start_t = _format_time_component(h, 0)
        warnings.append("rentang jam perkiraan")
        _check_store_hours(start_t, None, warnings)
        return start_t, None, warnings

    # 3. Cek format jam dengan periode: "jam 9 pagi", "jam 4 sore", "jam 7 malem"
    period_hour_match = re.search(
        r"(?:jam\s*)?(\d{1,2})(?:[:.](\d{2}))?\s*(pagi|siang|sore|malam|malem)",
        text,
    )
    if period_hour_match:
        h = int(period_hour_match.group(1))
        m = int(period_hour_match.group(2)) if period_hour_match.group(2) else 0
        period = period_hour_match.group(3)

        if period == "pagi":
            # 1-11 pagi tetap
            if h == 12:
                h = 0
        elif period == "siang":
            if 1 <= h <= 4:
                h += 12
        elif period in ("sore", "malam", "malem"):
            if 1 <= h < 12:
                h += 12

        start_t = _format_time_component(h, m)
        _check_store_hours(start_t, None, warnings)
        return start_t, None, warnings

    # 4. Cek jam standar HH:MM atau HH.MM (contoh: "jam 09.00", "14:30")
    exact_time_match = re.search(r"(?:jam\s*)?(\d{1,2})[:.](\d{2})\b", text)
    if exact_time_match:
        h = int(exact_time_match.group(1))
        m = int(exact_time_match.group(2))
        start_t = _format_time_component(h, m)
        _check_store_hours(start_t, None, warnings)
        return start_t, None, warnings

    # 5. Cek jam angka saja (contoh: "jam 9", "jam 16")
    hour_only_match = re.search(r"\bjam\s*(\d{1,2})\b", text)
    if hour_only_match:
        h = int(hour_only_match.group(1))
        start_t = _format_time_component(h, 0)
        _check_store_hours(start_t, None, warnings)
        return start_t, None, warnings

    # 6. Kata periode tanpa jam (contoh: "pagi", "siang", "sore", "malam")
    # PRD 6.5: kata tanpa jam -> rentang bawaan dan tandai warnings 'rentang jam perkiraan'
    for period_name, (start_default, end_default) in DEFAULT_PERIOD_RANGES.items():
        if period_name in text:
            warnings.append("rentang jam perkiraan")
            _check_store_hours(start_default, end_default, warnings)
            return start_default, end_default, warnings

    return None, None, [f"format jam tidak dikenali: '{time_text}'"]
