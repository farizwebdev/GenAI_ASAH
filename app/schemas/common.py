"""Tipe umum dan enum untuk layanan Gen AI Sabana Adventure Jombor."""

from enum import Enum


class ChannelEnum(str, Enum):
    """Titik masuk layanan chat."""

    web_widget = "web_widget"
    staff_paste = "staff_paste"
    telegram = "telegram"


class IntentEnum(str, Enum):
    """5 kelas maksud percakapan sesuai PRD Bagian 3."""

    booking_sewa = "booking_sewa"
    tanya_info = "tanya_info"
    ubah_batal = "ubah_batal"
    keluhan = "keluhan"
    lainnya = "lainnya"


class RouteEnum(str, Enum):
    """Tujuan routing eksekusi aksi berdasarkan channel x intent."""

    open_catalog = "open_catalog"
    answer_info = "answer_info"
    handoff_staff = "handoff_staff"
    refuse = "refuse"
    extract_order = "extract_order"
    suggest_reply = "suggest_reply"


class ItemStatusEnum(str, Enum):
    """Status pencocokan nama alat terhadap katalog toko."""

    matched = "matched"
    ambiguous = "ambiguous"
    unmatched = "unmatched"
