"""Skrip Pemanasan Layanan (Warmup Script) Sabana Adventure sesuai PRD Bagian 11 (T-20) & 13.

Tujuan:
1. Memanggil endpoint `/health` untuk memastikan server aktif dan model intent/prompt termuat.
2. Mengirimkan satu permintaan chat representatif ke `/api/v1/chat/message` untuk
   mengantisipasi cold start pada hosting free-tier (Render, Railway, Fly.io, dsb).
3. Mengukur dan melaporkan latensi round-trip sebelum demonstrasi atau evaluasi.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any

import httpx

DEFAULT_BASE_URL = os.getenv("SERVICE_URL", "http://localhost:8000")
DEFAULT_SERVICE_KEY = os.getenv("SERVICE_API_KEY", "ganti_dengan_kunci_layanan")


def ping_health(
    base_url: str,
    timeout: float = 10.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Memanggil endpoint health check /health dan mengembalikan respon JSON."""
    url = f"{base_url.rstrip('/')}/health"
    start = time.perf_counter()

    if client is not None:
        resp = client.get(url, timeout=timeout)
    else:
        with httpx.Client() as http_client:
            resp = http_client.get(url, timeout=timeout)

    latency_ms = int((time.perf_counter() - start) * 1000)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Health check gagal dengan HTTP {resp.status_code}: {resp.text}"
        )

    data = resp.json()
    data["_latency_ms"] = latency_ms
    return data


def send_warmup_query(
    base_url: str,
    service_key: str,
    message: str = "sewa 3 hari dihitung berapa hari ya kak?",
    timeout: float = 15.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Mengirim satu pesan chat pemanasan ke /api/v1/chat/message."""
    url = f"{base_url.rstrip('/')}/api/v1/chat/message"
    headers = {
        "X-Service-Key": service_key,
        "Content-Type": "application/json",
    }
    payload = {
        "channel": "web_widget",
        "message": message,
    }

    start = time.perf_counter()
    if client is not None:
        resp = client.post(url, json=payload, headers=headers, timeout=timeout)
    else:
        with httpx.Client() as http_client:
            resp = http_client.post(url, json=payload, headers=headers, timeout=timeout)

    latency_ms = int((time.perf_counter() - start) * 1000)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Permintaan pemanasan chat gagal dengan HTTP {resp.status_code}: {resp.text}"
        )

    data = resp.json()
    data["_latency_ms"] = latency_ms
    return data


def run_warmup(
    base_url: str = DEFAULT_BASE_URL,
    service_key: str = DEFAULT_SERVICE_KEY,
    timeout: float = 15.0,
    client: httpx.Client | None = None,
) -> bool:
    """Menjalankan seluruh alur pemanasan dan menampilkan ringkasan diagnostik."""
    print("=" * 65)
    print("  MEMULAI PEMANASAN LAYANAN (WARMUP) - SABANA ADVENTURE")
    print(f"  Target URL : {base_url}")
    print("=" * 65)

    # Langkah 1: Healthcheck
    print("\n[1/2] Memeriksa status kesehatan server (/health)...")
    try:
        health_data = ping_health(base_url=base_url, timeout=timeout, client=client)
        print(f"  -> Status        : {health_data.get('status')}")
        print(f"  -> Model Version : {health_data.get('model_version')}")
        print(f"  -> Prompt Version: {health_data.get('prompt_version')}")
        print(f"  -> Latensi Cek   : {health_data.get('_latency_ms')} ms")
    except Exception as exc:
        print(f"  [GAGAL] Tidak dapat menghubungi /health: {exc}")
        return False

    # Langkah 2: Permintaan Chat Contoh
    print("\n[2/2] Mengirim permintaan chat pemanasan (/api/v1/chat/message)...")
    try:
        chat_data = send_warmup_query(
            base_url=base_url,
            service_key=service_key,
            timeout=timeout,
            client=client,
        )
        print(f"  -> Intent Terdeteksi : {chat_data.get('intent')}")
        print(f"  -> Route             : {chat_data.get('route')}")
        print(f"  -> Fallback Used     : {chat_data.get('meta', {}).get('fallback_used')}")
        print(f"  -> Cuplikan Balasan  : {str(chat_data.get('reply_text'))[:60]}...")
        print(f"  -> Latensi Pemanasan : {chat_data.get('_latency_ms')} ms")
    except Exception as exc:
        print(f"  [GAGAL] Permintaan chat pemanasan gagal: {exc}")
        return False

    print("\n" + "=" * 65)
    print("  [SUKSES] Seluruh komponen layanan siap melayani trafik demo!")
    print("=" * 65)
    return True


def main() -> None:
    """Entry point CLI untuk eksekusi skrip pemanasan."""
    parser = argparse.ArgumentParser(
        description="Skrip pemanasan layanan Gen AI Sabana Adventure Jombor"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help="Base URL layanan (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--key",
        default=DEFAULT_SERVICE_KEY,
        help="Kunci otentikasi X-Service-Key",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Batas waktu permintaan dalam detik (default: 15.0)",
    )

    args = parser.parse_args()
    success = run_warmup(
        base_url=args.url,
        service_key=args.key,
        timeout=args.timeout,
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
