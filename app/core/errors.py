"""Definisi error kustom dan penanganan exception terpusat sesuai PRD Bagian 8.4."""

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import request_id_ctx


class AppError(Exception):
    """Kelas dasar exception aplikasi dengan format standar PRD."""

    def __init__(
        self,
        code: str,
        message_user: str,
        message_dev: str | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message_user)
        self.code = code
        self.message_user = message_user
        self.message_dev = message_dev or message_user
        self.status_code = status_code

    def to_dict(self, request_id: str | None = None) -> dict[str, Any]:
        """Format payload dictionary error standar."""
        return {
            "error": {
                "code": self.code,
                "message_user": self.message_user,
                "message_dev": self.message_dev,
                "request_id": request_id or request_id_ctx.get() or "",
            }
        }


class InvalidInputError(AppError):
    """Error untuk pesan kosong atau melebihi batas 1000 karakter."""

    def __init__(
        self,
        message_user: str = "Pesan tidak valid. Harap periksa kembali input Anda.",
        message_dev: str = "Pesan kosong atau melebihi batas 1000 karakter",
    ) -> None:
        super().__init__(
            code="invalid_input",
            message_user=message_user,
            message_dev=message_dev,
            status_code=400,
        )


class UnauthorizedError(AppError):
    """Error untuk autentikasi X-Service-Key yang salah atau tidak ada."""

    def __init__(
        self,
        message_user: str = "Akses ditolak. Layanan hanya dapat diakses oleh backend.",
        message_dev: str = "Header X-Service-Key tidak valid atau tidak disediakan",
    ) -> None:
        super().__init__(
            code="unauthorized",
            message_user=message_user,
            message_dev=message_dev,
            status_code=401,
        )


class ValidationError(AppError):
    """Error validasi payload permintaan."""

    def __init__(
        self,
        message_user: str = "Format data permintaan tidak sesuai skema.",
        message_dev: str = "Validasi skema gagal",
    ) -> None:
        super().__init__(
            code="validation_error",
            message_user=message_user,
            message_dev=message_dev,
            status_code=422,
        )


class RateLimitedError(AppError):
    """Error saat batas panggilan terlampaui."""

    def __init__(
        self,
        message_user: str = "Layanan sedang sibuk. Silakan coba sesaat lagi.",
        message_dev: str = "Rate limit terlampaui",
    ) -> None:
        super().__init__(
            code="rate_limited",
            message_user=message_user,
            message_dev=message_dev,
            status_code=429,
        )


class QuotaExceededError(AppError):
    """Error kuota penyedia AI habis."""

    def __init__(
        self,
        message_user: str = "Batas kuota asisten tercapai. Silakan coba kembali nanti.",
        message_dev: str = "LLM provider quota exceeded",
    ) -> None:
        super().__init__(
            code="quota_exceeded",
            message_user=message_user,
            message_dev=message_dev,
            status_code=429,
        )


class AIUnavailableError(AppError):
    """Error saat model AI atau vector store tidak dapat dihubungi."""

    def __init__(
        self,
        message_user: str = (
            "Layanan asisten AI sedang tidak dapat diakses. Silakan hubungi pegawai toko."
        ),
        message_dev: str = "Layanan LLM atau vector store mati",
    ) -> None:
        super().__init__(
            code="ai_unavailable",
            message_user=message_user,
            message_dev=message_dev,
            status_code=503,
        )


class AITimeoutError(AppError):
    """Error timeout LLM."""

    def __init__(
        self,
        message_user: str = "Asisten sedang sibuk. Silakan isi pesanan manual.",
        message_dev: str = "LLM request timeout",
    ) -> None:
        super().__init__(
            code="ai_timeout",
            message_user=message_user,
            message_dev=message_dev,
            status_code=504,
        )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handler FastAPI untuk AppError."""
    req_id = getattr(request.state, "request_id", None) or request_id_ctx.get()
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(request_id=req_id),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handler FastAPI untuk error validasi input Pydantic."""
    req_id = getattr(request.state, "request_id", None) or request_id_ctx.get()
    err = ValidationError(
        message_user="Data permintaan tidak valid atau tidak lengkap.",
        message_dev=str(exc.errors()),
    )
    return JSONResponse(
        status_code=422,
        content=err.to_dict(request_id=req_id),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler untuk exception tak terduga."""
    req_id = getattr(request.state, "request_id", None) or request_id_ctx.get()
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message_user": "Terjadi kesalahan internal pada layanan asisten.",
                "message_dev": str(exc),
                "request_id": req_id or "",
            }
        },
    )
