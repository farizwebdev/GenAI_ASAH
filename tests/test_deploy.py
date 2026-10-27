"""Pengujian Unit dan Verifikasi Konfigurasi Docker & Deploy (T-20).

Memastikan:
1. Berkas Dockerfile ada, valid, dan memuat instruksi standar (Python 3.11, non-root user, dsb).
2. Berkas .dockerignore mengabaikan kredensial (.env) dan folder cache.
3. Endpoint /health dan /api/v1/health berfungsi dengan status 'ok'.
4. Skrip scripts/warmup.py dapat melakukan pemanasan server dengan sukses.
5. Panduan Mode Ringan terdokumentasi di docs/deployment.md.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from scripts.warmup import ping_health, run_warmup, send_warmup_query

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def client() -> TestClient:
    """Fixture FastAPI TestClient."""
    return TestClient(app)


def test_dockerfile_exists_and_contains_standard_directives() -> None:
    """Memastikan berkas Dockerfile ada dan memuat instruksi standar industri."""
    dockerfile_path = BASE_DIR / "Dockerfile"
    assert dockerfile_path.is_file(), "Dockerfile harus ada di root repository"

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "FROM python:3.11-slim" in content, "Harus menggunakan base image python:3.11-slim"
    assert "WORKDIR /app" in content, "Harus menyetel direktori kerja /app"
    assert "COPY requirements.txt" in content, "Harus menyalin requirements.txt"
    assert "RUN pip install" in content, "Harus menjalankan instalasi dependensi"
    assert "EXPOSE 8000" in content, "Harus mengekspos port 8000"
    assert "HEALTHCHECK" in content, "Harus mendefinisikan instruksi HEALTHCHECK"
    assert "uvicorn" in content, "Harus menjalankan server ASGI uvicorn"
    assert "appuser" in content, "Harus menggunakan non-root user untuk keamanan"


def test_dockerignore_excludes_sensitive_and_temporary_files() -> None:
    """Memastikan berkas .dockerignore mengabaikan secret (.env) dan folder cache."""
    dockerignore_path = BASE_DIR / ".dockerignore"
    assert dockerignore_path.is_file(), ".dockerignore harus ada di root repository"

    content = dockerignore_path.read_text(encoding="utf-8")
    assert ".env" in content, ".dockerignore harus mengabaikan berkas .env"
    assert ".venv" in content, ".dockerignore harus mengabaikan folder virtualenv"
    assert "__pycache__" in content, ".dockerignore harus mengabaikan cache Python"
    assert ".pytest_cache" in content, ".dockerignore harus mengabaikan cache pytest"


def test_health_endpoints_status_and_schema(client: TestClient) -> None:
    """Memastikan endpoint /health dan /api/v1/health mengembalikan status ok dan versi model."""
    for path in ["/health", "/api/v1/health"]:
        resp = client.get(path)
        assert resp.status_code == 200, f"Endpoint {path} harus merespons 200 OK"
        data = resp.json()
        assert data.get("status") == "ok"
        assert "model_version" in data
        assert isinstance(data["model_version"], str)
        assert "prompt_version" in data
        assert isinstance(data["prompt_version"], str)


def test_warmup_script_ping_health(client: TestClient) -> None:
    """Memvalidasi fungsi ping_health pada scripts/warmup.py."""
    data = ping_health(base_url="http://testserver", client=client)
    assert data.get("status") == "ok"
    assert "_latency_ms" in data
    assert data["_latency_ms"] >= 0


def test_warmup_script_send_warmup_query(client: TestClient) -> None:
    """Memvalidasi fungsi send_warmup_query pada scripts/warmup.py."""
    settings = get_settings()
    data = send_warmup_query(
        base_url="http://testserver",
        service_key=settings.SERVICE_API_KEY,
        message="sewa 3 hari dihitung berapa hari ya kak?",
        client=client,
    )
    assert "intent" in data
    assert "route" in data
    assert "reply_text" in data
    assert "_latency_ms" in data
    assert data["_latency_ms"] >= 0


def test_warmup_script_run_warmup_success(client: TestClient) -> None:
    """Memastikan run_warmup berhasil mengeksekusi kedua langkah pemanasan."""
    settings = get_settings()
    success = run_warmup(
        base_url="http://testserver",
        service_key=settings.SERVICE_API_KEY,
        client=client,
    )
    assert success is True


def test_warmup_script_error_handling() -> None:
    """Memastikan skrip warmup menangani error koneksi secara elegan."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.text = "Service Unavailable"
    mock_client.get.return_value = mock_resp

    with pytest.raises(RuntimeError, match="Health check gagal"):
        ping_health(base_url="http://mockserver", client=mock_client)


def test_mode_ringan_documentation_exists() -> None:
    """Memastikan dokumentasi deployment dan mode ringan tersedia di docs/deployment.md."""
    doc_path = BASE_DIR / "docs" / "deployment.md"
    assert doc_path.is_file(), "Berkas docs/deployment.md harus tersedia"

    content = doc_path.read_text(encoding="utf-8")
    assert "Mode Ringan" in content, "Harus mendokumentasikan Mode Ringan"
    assert "EMBEDDER=api" in content, "Harus menyebutkan konfigurasi EMBEDDER=api"
    assert "docker build" in content, "Harus menyertakan panduan docker build"
    assert "docker run" in content, "Harus menyertakan panduan docker run"
    assert "warmup.py" in content, "Harus menyertakan panduan pemanasan server"
