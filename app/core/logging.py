"""Konfigurasi logging aman tanpa memuat data pribadi (PII) dan menyertakan request_id."""

import logging
import sys
from contextvars import ContextVar
from typing import Any

from app.utils.pii import mask_pii

# Context variable untuk menyimpan request_id aktif pada async request
request_id_ctx: ContextVar[str | None] = ContextVar("request_id_ctx", default=None)


class PIIMaskingFilter(logging.Filter):
    """Filter logging yang menyensor data pribadi dari pesan log."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_pii(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (mask_pii(v) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    mask_pii(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


class RequestIDFormatter(logging.Formatter):
    """Formatter logging yang menyertakan request_id dari context aktif."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        record.request_id = req_id if req_id else "-"
        return super().format(record)


def setup_logging(log_level: str = "INFO") -> None:
    """Menginisialisasi konfigurasi logging terpusat."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = RequestIDFormatter(
        fmt="%(asctime)s [%(levelname)s] [req_id:%(request_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(PIIMaskingFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """Mendapatkan logger dengan nama modul tertentu."""
    return logging.getLogger(name)
