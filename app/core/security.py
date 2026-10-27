"""Komponen Keamanan dan Autentikasi Layanan Gen AI sesuai PRD Bagian 8.

Layanan ini dirancang khusus untuk dipanggil oleh Backend Full-Stack,
sehingga setiap endpoint wajib menyertakan header `X-Service-Key`.
"""

from __future__ import annotations

from fastapi import Security
from fastapi.security import APIKeyHeader

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Definisi skema API Key Header untuk dokumentasi Swagger
API_KEY_HEADER = APIKeyHeader(
    name="X-Service-Key",
    description="Kunci otorisasi layanan internal untuk komunikasi backend-to-service",
    auto_error=False,
)


async def verify_service_key(
    service_key: str | None = Security(API_KEY_HEADER),
) -> str:
    """Memvalidasi keberadaan dan kebenaran header X-Service-Key.

    Args:
        service_key: Nilai kunci dari header X-Service-Key.

    Returns:
        str: Nilai service key yang valid.

    Raises:
        UnauthorizedError: Jika kunci tidak disediakan atau tidak cocok.
    """
    settings = get_settings()
    expected_key = settings.SERVICE_API_KEY

    if not service_key or service_key != expected_key:
        logger.warning("Upaya akses tidak sah: header X-Service-Key salah atau tidak ada.")
        raise UnauthorizedError(
            message_user="Akses ditolak. Layanan hanya dapat diakses oleh backend.",
            message_dev="Header X-Service-Key tidak valid atau tidak disediakan",
        )

    return service_key
