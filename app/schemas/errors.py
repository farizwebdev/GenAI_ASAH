"""Skema Pydantic untuk respon error standar sesuai PRD Bagian 8.4."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Rincian informasi error yang dikembalikan kepada pemanggil API."""

    code: str = Field(
        ...,
        description="Kode error standar, misal: invalid_input, ai_timeout",
    )
    message_user: str = Field(
        ...,
        description="Pesan ramah pengguna yang aman ditampilkan",
    )
    message_dev: str | None = Field(
        default=None,
        description="Pesan teknis untuk debugging pengembang",
    )
    request_id: str = Field(
        default="",
        description="ID unik pelacakan request",
    )


class ErrorResponse(BaseModel):
    """Struktur respon error standar layanan Gen AI."""

    error: ErrorDetail
