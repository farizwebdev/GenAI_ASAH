# ==============================================================================
# Dockerfile Layanan Gen AI “Asisten Chat Toko” Sabana Adventure Jombor (T-20)
# Multi-stage / Lightweight Production Image berbasis Python 3.11-slim
# ==============================================================================

FROM python:3.11-slim

# Menyetel environment variable standar container Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Direktori kerja aplikasi
WORKDIR /app

# Menginstal dependensi sistem minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Menginstal dependensi Python terlebih dahulu untuk memanfaatkan cache layer Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh kode aplikasi, konfigurasi, data, dan model
COPY app/ ./app/
COPY configs/ ./configs/
COPY data/ ./data/
COPY models/ ./models/
COPY prompts/ ./prompts/
COPY scripts/ ./scripts/

# Membuat non-root user untuk keamanan operasional container
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Mengekspos port layanan
EXPOSE 8000

# Healthcheck otomatis untuk orkestrator (Docker Compose / Kubernetes / Cloud Run)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Menjalankan server ASGI Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
