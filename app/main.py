"""Aplikasi FastAPI Layanan Gen AI Asisten Chat Toko Sabana Adventure Jombor."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

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
    settings = get_settings()

    app = FastAPI(
        title="Layanan Gen AI - Asisten Chat Toko",
        description="Layanan AI untuk ekstraksi booking, RAG info toko, dan guardrails chat Sabana Adventure Jombor.",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(RequestIDMiddleware)

    # Error Handlers Terpusat
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # Health check endpoint
    @app.get("/health", response_model=HealthResponse, tags=["Sistem"])
    async def health_check() -> HealthResponse:
        """Mengecek status operasional layanan."""
        return HealthResponse(
            status="ok",
            model_version="intent-baseline-v1",
            prompt_version="extract_v1,rag_v1",
        )

    return app


app = create_app()
