"""Router endpoint API untuk operasi administratif dan reload data toko."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.core.logging import get_logger
from app.core.security import verify_service_key
from app.services.matcher import get_item_matcher
from app.services.rag import get_rag_service

logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Administratif"],
    dependencies=[Depends(verify_service_key)],
)


@router.post(
    "/reload-data",
    summary="Muat Ulang Katalog dan Knowledge Base Toko",
    description=(
        "Memuat ulang data katalog alat (katalog_alat.csv) dan potongan "
        "basis pengetahuan toko (kb_toko.md) ke dalam memori layanan secara dinamis."
    ),
)
async def reload_data() -> dict[str, Any]:
    """Endpoint reload data katalog dan knowledge base toko."""
    try:
        matcher = get_item_matcher()
        matcher._load_catalog()

        rag = get_rag_service()
        rag._initialize_kb()

        logger.info("Data katalog alat dan KB toko berhasil dimuat ulang.")
        return {
            "status": "ok",
            "message": "Katalog alat dan Knowledge Base toko berhasil dimuat ulang.",
        }
    except Exception as exc:
        logger.error(f"Gagal memuat ulang data toko: {exc}")
        return {
            "status": "error",
            "message": f"Gagal memuat ulang data: {exc}",
        }
