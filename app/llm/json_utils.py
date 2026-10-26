"""Utilitas untuk pembersihan dan parsing output JSON dari LLM."""

import json
import re
from typing import Any

from app.core.errors import AppError

# Regex untuk mengekstrak blok JSON dari markdown code block (```json ... ``` atau ``` ... ```)
_MARKDOWN_JSON_PATTERN = re.compile(
    r"```(?:json)?\s*([\s\S]*?)\s*```",
    re.IGNORECASE,
)


def extract_json_str(text: str) -> str:
    """Mengekstrak string JSON mentah dari respons teks LLM.

    Mendukung respons teks langsung maupun yang dibungkus markdown code block.
    """
    text = text.strip()
    match = _MARKDOWN_JSON_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return text


def clean_and_parse_json(text: str) -> dict[str, Any]:
    """Membersihkan dan melakukan parse string menjadi dictionary JSON.

    Args:
        text: Teks keluaran LLM yang berisi JSON.

    Returns:
        dict: Hasil parsing JSON yang valid.

    Raises:
        AppError: Jika teks tidak dapat di-parse menjadi JSON valid.
    """
    clean_str = extract_json_str(text)
    try:
        data = json.loads(clean_str)
        if not isinstance(data, dict):
            raise AppError(
                code="invalid_ai_json",
                message_user="Hasil analisis asisten tidak sesuai format.",
                message_dev=f"Format JSON bukan objek/dict melainkan {type(data).__name__}",
                status_code=500,
            )
        return data
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AppError(
            code="invalid_ai_json",
            message_user="Asisten mengalami kendala memformat jawaban.",
            message_dev=f"Gagal parse JSON dari teks LLM: {exc}",
            status_code=500,
        ) from exc
