"""Pengujian unit komprehensif untuk modul utils/dates.py dan utils/times.py.

Sesuai PRD Bagian 6.5 dan Bagian 10 (T-12):
- Pengujian tabel (minimal 30 kasus uji).
- Menguji zona waktu Asia/Jakarta dan reference_date.
- Menguji tanggal relatif (besok, lusa, sabtu ini, sabtu depan, minggu depan).
- Menguji tanggal tanpa bulan (tanggal 5 lewat -> bulan depan).
- Menguji variasi jam (rentang, pagi/siang/sore/malam, 10an, di luar jam operasional toko).
"""

import pytest

from app.utils.dates import parse_date
from app.utils.times import parse_time

# Tanggal acuan standar pengujian sesuai PRD: 2026-10-28 (Rabu)
REF_DATE = "2026-10-28"

# -------------------------------------------------------------
# TABEL KASUS UJI TANGGAL (≥ 20 kasus)
# -------------------------------------------------------------
DATE_TEST_CASES = [
    # (input_text, expected_iso, expected_warning_substring)
    ("2026-10-31", "2026-10-31", None),
    ("31 Oktober", "2026-10-31", None),
    ("31 okt", "2026-10-31", None),
    ("31/10", "2026-10-31", None),
    ("31/10/2026", "2026-10-31", None),
    ("tgl 2/11", "2026-11-02", None),
    ("tanggal 2/11", "2026-11-02", None),
    ("5 Nov", "2026-11-05", None),
    ("5 november 2026", "2026-11-05", None),
    ("25 Desember", "2026-12-25", None),
    ("hari ini", "2026-10-28", None),
    ("besok", "2026-10-29", None),
    ("lusa", "2026-10-30", None),
    ("minggu depan", "2026-11-04", None),  # +7 hari dari Rabu 28 Okt
    ("sabtu ini", "2026-10-31", None),     # Sabtu terdekat
    ("sabtu depan", "2026-11-07", None),   # Sabtu pekan berikutnya (+10 hari)
    ("senin besok", "2026-11-02", None),   # Senin pekan depan
    ("jumat ini", "2026-10-30", None),     # Jumat terdekat
    ("tanggal 5", "2026-11-05", None),     # Tanggal 5 sudah lewat di Okt (28 Okt), jadi 5 Nov
    ("tgl 30", "2026-10-30", None),        # Tanggal 30 belum lewat di Okt -> 30 Okt
    ("15/01/2027", "2027-01-15", None),
    ("29 Februari 2026", None, "tidak valid"),  # 2026 bukan tahun kabisat
]


@pytest.mark.parametrize("date_text, expected_iso, expected_warning", DATE_TEST_CASES)
def test_parse_date_table(
    date_text: str, expected_iso: str | None, expected_warning: str | None
) -> None:
    """Menguji berbagai variasi format teks tanggal terhadap reference_date 2026-10-28."""
    result_iso, warnings = parse_date(date_text, reference_date=REF_DATE)

    assert result_iso == expected_iso, f"Gagal pada '{date_text}': dapat {result_iso}"
    if expected_warning:
        assert any(expected_warning in w for w in warnings), (
            f"Peringatan '{expected_warning}' tidak ditemukan pada '{date_text}': {warnings}"
        )


# -------------------------------------------------------------
# TABEL KASUS UJI WAKTU & JAM BUKA (≥ 20 kasus)
# -------------------------------------------------------------
TIME_TEST_CASES = [
    # (input_text, expected_start, expected_end, expected_warning_substring)
    ("08.00-10.00", "08:00", "10:00", None),
    ("08:00 - 10:00", "08:00", "10:00", None),
    ("08.00 s/d 11.00", "08:00", "11:00", None),
    ("09.30 sampai 12.00", "09:30", "12:00", None),
    ("jam 9 pagi", "09:00", None, None),
    ("jam 4 sore", "16:00", None, None),
    ("jam 7 malem", "19:00", None, None),
    ("jam 7 malam", "19:00", None, None),
    ("jam 1 siang", "13:00", None, None),
    ("jam 12 siang", "12:00", None, None),
    ("jam 11 siang", "11:00", None, None),
    ("10an", "10:00", None, "rentang jam perkiraan"),
    ("jam 10an", "10:00", None, "rentang jam perkiraan"),
    ("pagi", "08:00", "11:00", "rentang jam perkiraan"),
    ("siang", "11:00", "15:00", "rentang jam perkiraan"),
    ("sore", "15:00", "18:00", "rentang jam perkiraan"),
    ("malam", "18:00", "21:00", "rentang jam perkiraan"),
    ("jam 08.00", "08:00", None, None),
    ("jam 14:00", "14:00", None, None),
    # Kasus di luar jam buka toko (08:00-21:00) -> Menghasilkan warning, bukan error
    ("jam 6 pagi", "06:00", None, "di luar jam buka toko"),
    ("jam 10 malam", "22:00", None, "di luar jam buka toko"),
    ("22:00 - 23:00", "22:00", "23:00", "di luar jam buka toko"),
    ("06.00-08.00", "06:00", "08:00", "di luar jam buka toko"),
]


@pytest.mark.parametrize(
    "time_text, expected_start, expected_end, expected_warning", TIME_TEST_CASES
)
def test_parse_time_table(
    time_text: str,
    expected_start: str | None,
    expected_end: str | None,
    expected_warning: str | None,
) -> None:
    """Menguji berbagai variasi format teks jam dan validasi jam operasional toko."""
    start_t, end_t, warnings = parse_time(time_text)

    assert start_t == expected_start, f"Start time gagal pada '{time_text}': {start_t}"
    assert end_t == expected_end, f"End time gagal pada '{time_text}': {end_t}"

    if expected_warning:
        assert any(expected_warning in w for w in warnings), (
            f"Peringatan '{expected_warning}' tidak ditemukan pada '{time_text}': {warnings}"
        )
