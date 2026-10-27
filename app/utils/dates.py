"""Utilitas parsing tanggal bahasa Indonesia untuk reservasi Sabana Adventure.

Mendukung zona waktu Asia/Jakarta dan berbagai ekspresi tanggal relatif/absolut:
- 31 Oktober, 31 okt, 31/10, tgl 2/11, 5 Nov
- besok, lusa, hari ini
- sabtu ini, sabtu depan, minggu depan, senin besok
- tanggal 5 / tgl 5 (otomatis bulan berikutnya jika tanggal sudah lewat)
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

MONTH_MAP: dict[str, int] = {
    "januari": 1,
    "jan": 1,
    "februari": 2,
    "feb": 2,
    "maret": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "mei": 5,
    "juni": 6,
    "jun": 6,
    "juli": 7,
    "jul": 7,
    "agustus": 8,
    "agu": 8,
    "ags": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "oktober": 10,
    "okt": 10,
    "november": 11,
    "nov": 11,
    "desember": 12,
    "des": 12,
}

DAY_MAP: dict[str, int] = {
    "senin": 0,
    "selasa": 1,
    "rabu": 2,
    "kamis": 3,
    "jumat": 4,
    "jum'at": 4,
    "sabtu": 5,
    "minggu": 6,
    "ahad": 6,
}


def _resolve_reference_date(reference_date: date | datetime | str | None) -> date:
    """Mengubah reference_date menjadi objek datetime.date."""
    if reference_date is None:
        return datetime.now(JAKARTA_TZ).date()
    if isinstance(reference_date, datetime):
        return reference_date.date()
    if isinstance(reference_date, date):
        return reference_date
    if isinstance(reference_date, str):
        return date.fromisoformat(reference_date.strip())
    return datetime.now(JAKARTA_TZ).date()


def parse_date(
    date_text: str,
    reference_date: date | datetime | str | None = None,
) -> tuple[str | None, list[str]]:
    """Mem-parsing teks tanggal dalam bahasa Indonesia menjadi format YYYY-MM-DD.

    Args:
        date_text: Teks mentah tanggal dari pesan (misal: '31 Oktober', 'besok', 'tgl 2/11').
        reference_date: Tanggal acuan untuk menghitung tanggal relatif.

    Returns:
        tuple[str | None, list[str]]: (iso_date_string, list_of_warnings)
    """
    if not date_text or not date_text.strip():
        return None, ["teks tanggal kosong"]

    ref_date = _resolve_reference_date(reference_date)
    text = date_text.strip().lower()
    warnings: list[str] = []

    # 1. Cek format ISO langsung YYYY-MM-DD
    iso_match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        try:
            return date(y, m, d).isoformat(), warnings
        except ValueError:
            return None, [f"tanggal ISO tidak valid: {text}"]

    # 2. Relatif hari: hari ini, besok, lusa, kemarin
    if "hari ini" in text:
        return ref_date.isoformat(), warnings
    day_keywords = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]
    if "besok" in text and not any(k in text for k in day_keywords):
        return (ref_date + timedelta(days=1)).isoformat(), warnings
    if "lusa" in text:
        return (ref_date + timedelta(days=2)).isoformat(), warnings

    # 3. Relatif pekan: "minggu depan" (tanpa hari tertentu)
    weekdays_no_sun = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu"]
    if "minggu depan" in text and not any(k in text for k in weekdays_no_sun):
        return (ref_date + timedelta(days=7)).isoformat(), warnings

    # 4. Pola nama hari: "<hari> ini", "<hari> depan", "<hari> besok"
    # Contoh: "sabtu ini", "sabtu depan", "senin besok"
    for day_name, target_weekday in DAY_MAP.items():
        if day_name in text:
            ref_weekday = ref_date.weekday()
            days_ahead = (target_weekday - ref_weekday) % 7

            if "depan" in text:
                # Jika sabtu depan: lewati pekan ini (+7 hari)
                days_ahead = 7 if days_ahead == 0 else days_ahead + 7
            elif "ini" in text:
                # Hari yang dimaksud dalam pekan berjalan
                if days_ahead == 0:
                    pass  # hari ini
            elif "besok" in text:
                # Contoh: senin besok
                if days_ahead == 0:
                    days_ahead = 7
            else:
                # Hanya nama hari saja (misal: "sabtu")
                if days_ahead == 0:
                    days_ahead = 7

            target_date = ref_date + timedelta(days=days_ahead)
            return target_date.isoformat(), warnings

    # 5. Pola D/M atau D/M/YYYY (contoh: "31/10", "tgl 2/11", "2/11/2026")
    slash_match = re.search(r"(?:tgl|tanggal)?\s*(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", text)
    if slash_match:
        d = int(slash_match.group(1))
        m = int(slash_match.group(2))
        raw_year = slash_match.group(3)
        if raw_year:
            y = int(raw_year) if len(raw_year) == 4 else 2000 + int(raw_year)
        else:
            y = ref_date.year
            # Jika sudah lewat dalam tahun ini, geser ke tahun berikutnya
            try:
                if date(y, m, d) < ref_date:
                    y += 1
            except ValueError:
                pass

        try:
            return date(y, m, d).isoformat(), warnings
        except ValueError:
            return None, [f"tanggal tidak valid: {text}"]

    # 6. Pola D <nama_bulan> atau D <nama_bulan> <YYYY> (contoh: "31 Oktober", "31 okt", "5 Nov")
    # Urutkan nama bulan berdasarkan panjang menurun agar 'september' dicocokkan sebelum 'sep'
    months_pattern = "|".join(sorted(MONTH_MAP.keys(), key=len, reverse=True))
    month_regex = rf"(?:tgl|tanggal)?\s*(\d{{1,2}})\s+({months_pattern})(?:\s+(\d{{4}}))?"
    month_match = re.search(month_regex, text)
    if month_match:
        d = int(month_match.group(1))
        m_name = month_match.group(2)
        m = MONTH_MAP[m_name]
        raw_year = month_match.group(3)
        if raw_year:
            y = int(raw_year)
        else:
            y = ref_date.year
            try:
                if date(y, m, d) < ref_date:
                    y += 1
            except ValueError:
                pass

        try:
            return date(y, m, d).isoformat(), warnings
        except ValueError:
            return None, [f"tanggal tidak valid: {text}"]

    # 7. Pola "tanggal D" atau "tgl D" tanpa bulan (contoh: "tanggal 5", "tgl 5")
    # PRD 6.5: "Jika bulan tidak disebut dan tanggal sudah lewat, pakai bulan berikutnya."
    tgl_only_match = re.search(r"(?:tgl|tanggal)\s+(\d{1,2})\b", text)
    if tgl_only_match:
        d = int(tgl_only_match.group(1))
        m = ref_date.month
        y = ref_date.year
        if d < ref_date.day:
            m += 1
            if m > 12:
                m = 1
                y += 1

        try:
            return date(y, m, d).isoformat(), warnings
        except ValueError:
            return None, [f"tanggal tidak valid: {text}"]

    return None, [f"format tanggal tidak dikenali: '{date_text}'"]
