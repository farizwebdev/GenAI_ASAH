"""Pengujian unit komprehensif untuk modul preprocessing teks (T-07)."""

import pytest

from app.services.preprocessing import normalize


def test_normalize_lowercase_and_whitespace() -> None:
    """Memastikan teks diubah menjadi huruf kecil dan spasi ganda dirapikan."""
    raw = "  HALO   KAK   SAYA   MAU   SEWA  "
    res = normalize(raw, mode="for_intent")
    assert res == "halo kak saya mau sewa"


def test_normalize_common_slang_rules() -> None:
    """Memastikan singkatan umum diubah ke bentuk baku."""
    # tgl -> tanggal
    assert "tanggal" in normalize("sewa tgl 31 oktober", mode="for_intent")
    # yg -> yang
    assert "yang" in normalize("alat yg disewa apa aja", mode="for_intent")
    # ga / gak / nggak -> tidak
    assert "tidak" in normalize("saya ga jadi naik gunung", mode="for_intent")
    assert "tidak" in normalize("tenda gak ada ya", mode="for_intent")
    assert "tidak" in normalize("nggak bisa kak", mode="for_intent")
    # bwt -> buat, sy -> saya, klo -> kalau
    res = normalize("sy mo sewa bwt besok klo ada", mode="for_intent")
    assert "saya" in res
    assert "buat" in res
    assert "kalau" in res


def test_normalize_sleeping_bag_context() -> None:
    """Memastikan singkatan 'sb' diubah menjadi 'sleeping bag'."""
    res = normalize("sewa sb polar 2 sama matras", mode="for_intent")
    assert "sleeping bag" in res
    assert "sb polar" not in res


def test_normalize_preserve_numbers_and_units() -> None:
    """Memastikan angka dan satuan (60l, kap 4, 08.00) tidak terpotong atau rusak."""
    text = "sewa carrier 60l sama tenda kap 4 jam 08.00-10.00"
    res = normalize(text, mode="for_intent")
    assert "60l" in res
    assert "kap 4" in res
    assert "08 00 10 00" in res or "08" in res


def test_normalize_mode_for_intent() -> None:
    """Mode for_intent harus meratakan baris baru dan menghapus tanda baca berlebih."""
    raw = "Nama: Rizky!\nTanggal ambil: 31 Okt???\nBarang: tenda kap 4."
    res = normalize(raw, mode="for_intent")
    assert "\n" not in res
    assert "!" not in res
    assert "?" not in res
    assert "tenda kap 4" in res


def test_normalize_mode_for_extract() -> None:
    """Mode for_extract harus mempertahankan baris baru dan label booking."""
    raw = (
        "Nama: Rizky Ramadhan\nTanggal ambil: 31 Oktober\n"
        "Kisaran jam: 08.00-10.00\nList: tenda kap 4"
    )
    res = normalize(raw, mode="for_extract")
    lines = res.splitlines()
    assert len(lines) == 4
    assert lines[0].startswith("nama: rizky ramadhan")
    assert lines[1].startswith("tanggal ambil: 31 oktober")
    assert lines[2].startswith("kisaran jam: 08.00-10.00")
    assert lines[3].startswith("list: tenda kap 4")


def test_normalize_invalid_mode() -> None:
    """Memastikan mode yang salah melempar ValueError."""
    with pytest.raises(ValueError):
        normalize("halo", mode="mode_ngawur")
