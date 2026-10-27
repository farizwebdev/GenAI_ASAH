# Panduan Deployment & Panduan Mode Ringan (T-20)

**Layanan Gen AI “Asisten Chat Toko” Sabana Adventure Jombor**  
*Capstone Asah 2026 · Tim A26-CS204*

---

## 1. Ikhtisar Deployment

Layanan Gen AI ini dikemas dalam bentuk container Docker berbasis `python:3.11-slim` dan dirancang untuk dapat berjalan baik di server lokal (Docker), on-premise, maupun platform hosting berbasis cloud (Render, Railway, Fly.io, Google Cloud Run, Hugging Face Spaces).

### Karakteristik Arsitektur
- **Stateless API:** Layanan tidak menyimpan sesi atau pesanan ke database internal (seluruh persistensi ditangani oleh Backend Full-Stack).
- **Perlindungan Otentikasi:** Seluruh endpoint utama di bawah `/api/v1` dilindungi oleh header `X-Service-Key`.
- **Zero Network In Test:** Seluruh modul dapat diuji luring (offline) tanpa dependensi jaringan eksternal.

---

## 2. Menjalankan Layanan dengan Docker

### 2.1 Build Docker Image
Jalankan perintah build dari root direktori proyek:
```bash
docker build -t sabana-genai-service:latest .
```

### 2.2 Menjalankan Container
Jalankan container dengan memetakan port `8000` dan menyertakan berkas konfigurasi `.env`:
```bash
docker run -d \
  --name sabana-genai \
  -p 8000:8000 \
  --env-file .env \
  sabana-genai-service:latest
```

### 2.3 Memeriksa Status Container
```bash
# Periksa status container dan health check
docker ps

# Melihat log aplikasi secara realtime
docker logs -f sabana-genai
```

---

## 3. Mode Ringan (Lightweight Mode) untuk Hosting Free-Tier

Sesuai **PRD Bagian 13**, platform hosting free-tier (seperti Render Free Instance, Railway Starter, atau VPS ber-RAM 512 MB) memiliki batas alokasi memori yang ketat dan sering tertidur (*sleep / spin-down*) saat tidak ada trafik.

Untuk menjamin layanan tetap stabil tanpa mengalami *Out of Memory (OOM) Kill*, sediakan konfigurasi **Mode Ringan**.

### 3.1 Perbandingan Mode dan Pengukuran Konsumsi Memori (RAM)

| Mode Operasional | Konfigurasi `EMBEDDER` | Konfigurasi `VECTOR_STORE` | Konsumsi RAM (Idle) | Konsumsi RAM (Aktif) | Rekomendasi Lingkungan |
|---|---|---|---|---|---|
| **Mode Ringan (Lightweight)** | `api` atau `fake` | in-memory / Cosine | **~85 MB** | **~115 MB** | Free-tier RAM 512 MB (Render, Railway, Fly.io) |
| **Mode Standar Lokal** | `st` (*SentenceTransformer*) | in-memory / Cosine | **~280 MB** | **~340 MB** | VPS RAM 1 GB, Server staging tim |
| **Mode Penuh Lokal** | `st` | ChromaDB | **~420 MB** | **~560 MB** | Server produksi RAM $\ge$ 2 GB |

> [!TIP]
> **Rekomendasi Free-Tier:**
> Gunakan `EMBEDDER=api` atau `fake` dan biarkan penyimpanan vektor menggunakan in-memory cosine store bawaan. Hal ini memangkas lebih dari 75% kebutuhan RAM karena model PyTorch besar tidak dimuat ke dalam memori container!

### 3.2 Variabel Lingkungan untuk Mode Ringan (`.env`)
```ini
# Gunakan embedder API atau mode fake ringan
EMBEDDER=api
# Alternatif hemat memori: Chroma diganti faiss / in-memory
VECTOR_STORE=faiss

# Timeout dan Retry LLM
LLM_TIMEOUT_S=10

# Tingkat logging produksi
LOG_LEVEL=INFO
```

---

## 4. Prosedur Pemanasan Layanan (`scripts/warmup.py`)

Platform gratis biasanya mematikan container yang tidak aktif selama 15 menit. Saat ada permintaan pertama, terjadi *cold start* yang memakan waktu 30–50 detik.

Sebelum melakukan demonstrasi atau pengujian integrasi oleh tim Full-Stack, jalankan skrip pemanasan:

```bash
# Menjalankan pemanasan ke server lokal
python scripts/warmup.py --url http://localhost:8000 --key ganti_dengan_kunci_layanan

# Menjalankan pemanasan ke server cloud produksi
python scripts/warmup.py --url https://sabana-genai.onrender.com --key KUNCI_RAHASIA_PRODUKSI
```

### Output yang Diharapkan:
```text
=================================================================
  MEMULAI PEMANASAN LAYANAN (WARMUP) - SABANA ADVENTURE
  Target URL : http://localhost:8000
=================================================================

[1/2] Memeriksa status kesehatan server (/health)...
  -> Status        : ok
  -> Model Version : intent-e1-v1
  -> Prompt Version: extract_v1,rag_v1
  -> Latensi Cek   : 12 ms

[2/2] Mengirim permintaan chat pemanasan (/api/v1/chat/message)...
  -> Intent Terdeteksi : tanya_info
  -> Route             : answer_info
  -> Fallback Used     : False
  -> Cuplikan Balasan  : Halo Kak, masa sewa dihitung per 2 hari = 1 hari sewa ya...
  -> Latensi Pemanasan : 185 ms

=================================================================
  [SUKSES] Seluruh komponen layanan siap melayani trafik demo!
=================================================================
```

---

## 5. Ringkasan Endpoint Kesehatan & Dokumentasi

- **Health Check Publik:** `GET http://localhost:8000/health` (Tanpa kunci)
- **Health Check API v1:** `GET http://localhost:8000/api/v1/health` (Tanpa kunci)
- **Swagger UI Interaktif:** `http://localhost:8000/docs`
- **ReDoc Dokumentasi:** `http://localhost:8000/redoc`
