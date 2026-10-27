"""Aplikasi FastAPI Layanan Gen AI Asisten Chat Toko Sabana Adventure Jombor."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.routes_admin import router as admin_router
from app.api.routes_chat import router as chat_router
from app.api.routes_orders import router as orders_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    generic_error_handler,
    validation_error_handler,
)
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestIDMiddleware
from app.schemas.chat import HealthResponse
from app.services.intent import get_intent_classifier

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Siklus hidup aplikasi saat startup dan shutdown."""
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger.info("Layanan Gen AI Sabana Adventure Jombor berhasil dimulai.")
    yield
    logger.info("Layanan Gen AI dimatikan.")


def create_app() -> FastAPI:
    """Factory function untuk membuat instance aplikasi FastAPI."""
    app = FastAPI(
        title="Layanan Gen AI - Asisten Chat Toko Sabana Adventure",
        description=(
            "Layanan internal Gen AI (FastAPI) untuk asistensi chat persewaan "
            "alat camping Sabana Adventure Jombor.\n\n"
            "Fitur Utama:\n"
            "- Ekstraksi draf pesanan chat WhatsApp pelanggan (Hybrid X1 deterministik & LLM X3)\n"
            "- Tanya-Jawab RAG berbasis basis pengetahuan toko (KB-01 s/d KB-12)\n"
            "- Guardrails keamanan 3 lapis (Injeksi prompt, skor retrieval, & OOD)\n"
            "- Matriks perutean cerdas channel x intent (web_widget, telegram, staff_paste)\n\n"
            "Catatan Keamanan: Seluruh endpoint di bawah `/api/v1` memerlukan header "
            "`X-Service-Key`."
        ),
        version="2.0.0",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(RequestIDMiddleware)

    # Error Handlers Terpusat
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # Mendaftarkan router API v1
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    # Health check endpoint
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Sistem"],
        summary="Cek Status Layanan (Health Check)",
    )
    @app.get(
        "/api/v1/health",
        response_model=HealthResponse,
        tags=["Sistem"],
        summary="Cek Status Layanan v1",
        include_in_schema=False,
    )
    async def health_check() -> HealthResponse:
        """Mengecek status operasional layanan, versi model, dan prompt."""
        clf = get_intent_classifier()
        model_version = (
            str(clf.artifact.get("model_name", "intent-e1-v1"))
            if clf.artifact
            else "intent-e1-v1"
        )
        return HealthResponse(
            status="ok",
            model_version=model_version,
            prompt_version="extract_v1,rag_v1",
        )

    return app


app = create_app()
