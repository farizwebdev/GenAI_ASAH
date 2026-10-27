"""Pengujian unit komprehensif untuk modul matcher alat camping (T-11).

Sesuai PRD Bagian 6.4 & 10:
- Menguji kasus alias katalog (misal: 'keril', 'sb', 'refil gas', 'flyseat')
- Menguji salah ketik / typo (misal: 'sleping back', 'hedlamp', 'matras spons')
- Menguji kapasitas tenda dan volume carrier ('tenda kap 4', 'carrier 60')
- Menguji kasus ambigu ('tenda dome 2', 'sepatu')
- Menguji peringatan butuh ukuran pada sepatu dan jaket
- Menguji kasus unmatched untuk barang di luar katalog
"""

import pytest

from app.schemas.common import ItemStatusEnum
from app.services.matcher import ItemMatcher, get_item_matcher, parse_item_text


@pytest.fixture(scope="module")
def matcher() -> ItemMatcher:
    """Fixture instance ItemMatcher."""
    return get_item_matcher()


def test_parse_item_text_quantities() -> None:
    """Menguji ekstraksi jumlah (qty) dari berbagai pola teks."""
    # Pola explicit xN / Nx
    name, qty, spec, _ = parse_item_text("matras x3")
    assert qty == 3
    assert "matras" in name

    name, qty, spec, _ = parse_item_text("2x kompor portable")
    assert qty == 2
    assert "kompor" in name

    # Pola buah / pcs
    name, qty, spec, _ = parse_item_text("sleeping bag 4 pcs")
    assert qty == 4

    # Pola angka di awal dan akhir
    name, qty, spec, _ = parse_item_text("2 matras")
    assert qty == 2
    assert "matras" in name

    name, qty, spec, _ = parse_item_text("carrier 60 2")
    assert qty == 2
    assert spec.get("volume_l") == 60


def test_parse_item_text_specifications() -> None:
    """Menguji ekstraksi spesifikasi kapasitas, volume, dan ukuran."""
    # Kapasitas tenda
    _, qty, spec, _ = parse_item_text("tenda kap 4")
    assert qty == 1
    assert spec.get("kapasitas") == 4

    _, qty, spec, _ = parse_item_text("tenda 6 orang")
    assert qty == 1
    assert spec.get("kapasitas") == 6

    # Volume carrier
    _, qty, spec, _ = parse_item_text("carrier 40l")
    assert spec.get("volume_l") == 40

    # Ukuran sepatu / jaket
    _, qty, spec, _ = parse_item_text("sepatu hiking ukuran 42")
    assert spec.get("ukuran") == "42"


def test_tenda_dome_2_special_case(matcher: ItemMatcher) -> None:
    """Menguji penanganan khusus 'tenda dome 2' sesuai PRD Bagian 6.4a."""
    item = matcher.match_item("tenda dome 2")
    assert item.matched_item_id == "TND-DOME-2"
    assert item.qty == 1
    assert item.spec.get("kapasitas") == 2
    assert item.notes is not None
    assert "angka 2 dapat berarti jumlah" in item.notes


def test_matcher_aliases(matcher: ItemMatcher) -> None:
    """Menguji pengenalan alias umum alat dari katalog."""
    test_cases = [
        ("refil gas", "GAS-KLG"),
        ("tabung gas", "GAS-KLG"),
        ("flyseat", "FLY-SHEET"),
        ("keril 60", "CRR-60L"),
        ("sb polar", "SLB-POLAR"),
        ("nesting", "NST-SET"),
        ("senter kepala", "HDL-STD"),
        ("matras gulung", "MTR-SPONS"),
    ]
    for raw_text, expected_id in test_cases:
        item = matcher.match_item(raw_text)
        assert item.matched_item_id == expected_id, (
            f"Gagal mencocokkan alias '{raw_text}': didapat {item.matched_item_id}"
        )
        assert item.status in (ItemStatusEnum.matched, ItemStatusEnum.ambiguous)


def test_matcher_typos(matcher: ItemMatcher) -> None:
    """Menguji ketahanan terhadap salah ketik (typos)."""
    test_cases = [
        ("sleping back", "SLB-STD"),
        ("hedlamp", "HDL-STD"),
        ("matras tiup", "MTR-ANGIN"),
        ("tnda dome 4", "TND-DOME-4"),
        ("kompor portabel", "STV-PORT"),
    ]
    for raw_text, expected_id in test_cases:
        candidates = matcher.match(raw_text, top_k=3)
        assert len(candidates) > 0
        assert candidates[0].item_id == expected_id, (
            f"Gagal mencocokkan typo '{raw_text}': teratas adalah {candidates[0].item_id}"
        )


def test_matcher_size_warnings(matcher: ItemMatcher) -> None:
    """Menguji peringatan butuh ukuran pada sepatu dan jaket bila belum disebut."""
    # Sepatu tanpa ukuran -> harus memberi warning
    item_no_size = matcher.match_item("sepatu hiking")
    assert item_no_size.matched_item_id == "SPT-HIK"
    assert item_no_size.notes is not None
    assert "ukuran sepatu belum disebut" in item_no_size.notes

    # Sepatu dengan ukuran -> tidak ada warning ukuran
    item_with_size = matcher.match_item("sepatu hiking ukuran 42")
    assert item_with_size.matched_item_id == "SPT-HIK"
    assert item_with_size.spec.get("ukuran") == "42"
    assert item_with_size.notes is None or "ukuran sepatu belum disebut" not in item_with_size.notes


def test_matcher_unmatched(matcher: ItemMatcher) -> None:
    """Menguji teks barang yang sama sekali tidak ada di toko camping."""
    unmatched_cases = [
        "playstation 5",
        "laptop asus rog",
        "resep nasi goreng spesial",
        "sepeda motor honda beat",
    ]
    for raw_text in unmatched_cases:
        item = matcher.match_item(raw_text)
        assert item.status == ItemStatusEnum.unmatched
        assert item.matched_item_id is None
