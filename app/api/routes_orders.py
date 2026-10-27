"""Router endpoint API untuk ekstraksi pesanan booking sesuai PRD Bagian 8."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.errors import InvalidInputError
from app.core.security import verify_service_key
from app.schemas.order import ExtractedOrder, ExtractOrderRequest
from app.services.extractor import get_order_extractor

router = APIRouter(
    prefix="/orders",
    tags=["Pesanan & Ekstraksi"],
    dependencies=[Depends(verify_service_key)],
)


@router.post(
    "/extract",
    response_model=ExtractedOrder,
    summary="Ekstraksi Pesanan Langsung (Staf Admin)",
    description=(
        "Mengekstrak draf pesanan sewa secara langsung dari teks chat WhatsApp "
        "yang ditempel pegawai toko (force_extract melewati klasifikasi intent)."
    ),
)
async def extract_order(request: ExtractOrderRequest) -> ExtractedOrder:
    """Endpoint ekstraksi pesanan langsung untuk staf toko."""
    if not request.message.strip():
        raise InvalidInputError(
            message_user="Pesan tidak boleh kosong.",
            message_dev="Pesan kosong atau hanya berisi spasi",
        )
    extractor = get_order_extractor()
    extracted_order, fallback_used = extractor.extract(
        request.message,
        reference_date=request.reference_date,
    )
    return extracted_order
