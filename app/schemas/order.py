"""Skema Pydantic untuk ekstraksi draf pesanan sewa alat camping."""

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ItemStatusEnum


class OrderItem(BaseModel):
    """Satu baris alat sewa yang diekstraksi dari pesan pelanggan."""

    raw_text: str = Field(..., description="Teks mentah nama alat dalam pesan")
    qty: int = Field(default=1, ge=1, description="Jumlah unit alat yang disewa")
    spec: dict[str, Any] = Field(
        default_factory=dict,
        description="Spesifikasi alat yang terdeteksi (kapasitas, ukuran, volume)",
    )
    matched_item_id: str | None = Field(
        default=None,
        description="ID alat pada katalog toko jika cocok (contoh: TND-DOME-4)",
    )
    matched_name: str | None = Field(
        default=None,
        description="Nama resmi alat pada katalog toko",
    )
    match_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Skor keyakinan pencocokan nama alat (0.0 sampai 1.0)",
    )
    status: ItemStatusEnum = Field(
        default=ItemStatusEnum.unmatched,
        description="Status pencocokan: matched, ambiguous, atau unmatched",
    )
    notes: str | None = Field(
        default=None,
        description="Catatan khusus terkait item alat ini",
    )


class ExtractedOrder(BaseModel):
    """Draf pesanan sewa hasil ekstraksi dari pesan booking WhatsApp."""

    customer_name: str | None = Field(
        default=None,
        description="Nama pelanggan jika disebutkan di pesan (null jika sesuai nomor WA)",
    )
    pickup_date: str | None = Field(
        default=None,
        description="Tanggal ambil barang format YYYY-MM-DD",
    )
    pickup_time_start: str | None = Field(
        default=None,
        description="Awal kisaran jam ambil barang format HH:MM",
    )
    pickup_time_end: str | None = Field(
        default=None,
        description="Akhir kisaran jam ambil barang format HH:MM jika ada rentang",
    )
    pickup_time_raw: str | None = Field(
        default=None,
        description="Teks mentah jam ambil dari pesan pelanggan",
    )
    return_date: str | None = Field(
        default=None,
        description="Tanggal pengembalian barang jika disebutkan (format toko tidak mewajibkan)",
    )
    items: list[OrderItem] = Field(
        default_factory=list,
        description="Daftar alat-alat sewa yang diekstraksi",
    )
    extra_note: str | None = Field(
        default=None,
        description="Catatan tambahan (contoh: penambahan barang saat di toko)",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Daftar field wajib booking yang belum lengkap",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Peringatan untuk staf (misal: ukuran sepatu belum disebut)",
    )
    needs_review: bool = Field(
        default=True,
        description="Wajib True bila butuh pemeriksaan manual pegawai sebelum disimpan",
    )
