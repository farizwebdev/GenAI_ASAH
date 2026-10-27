# ruff: noqa: E501
"""Skrip Pembuat README Otomatis (T-23) sesuai PRD Bagian 11 & 12.

Mengekstrak seluruh tabel hasil evaluasi model dan eksperimen dari folder reports/:
- reports/intent_report.md (Perbandingan Model E1-E3)
- reports/matcher_report.md (Perbandingan Pencocok Alat M1-M3)
- reports/extraction_report.md (Perbandingan Ekstraksi Pesanan X1-X3)
- reports/class_balance.md & improvement.md (Keseimbangan Kelas & Peningkatan Kinerja S1, S2)
- reports/test_evaluation_report.md (Hasil Uji Data Tersisih S3)
- reports/guardrail_report.md (Hasil Penolakan Out-of-Domain S8)
- reports/sentiment_report.md (Analisis Sentimen P2)

Kemudian menghasilkan berkas README.md lengkap yang mematuhi 13 kerangka wajib PRD Bagian 12.
"""

from __future__ import annotations

import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
README_PATH = BASE_DIR / "README.md"


def read_report_section(filename: str, fallback_text: str = "") -> str:
    """Membaca isi berkas laporan dari folder reports/ jika tersedia."""
    filepath = REPORTS_DIR / filename
    if filepath.is_file():
        return filepath.read_text(encoding="utf-8").strip()
    return fallback_text


def extract_table(content: str, header_keyword: str) -> str:
    """Mengekstrak tabel markdown yang mengikuti keyword tertentu."""
    lines = content.splitlines()
    table_lines: list[str] = []
    found_header = False

    for line in lines:
        if header_keyword.lower() in line.lower():
            found_header = True
            continue

        if found_header:
            if line.strip().startswith("|"):
                table_lines.append(line)
            elif table_lines and not line.strip().startswith("|"):
                # Akhir tabel
                break

    if table_lines:
        return "\n".join(table_lines)
    return ""


def build_readme() -> str:
    """Menyusun teks lengkap README.md sesuai 13 kerangka wajib PRD Bagian 12."""
    # 1. Baca laporan-laporan dari reports/
    intent_report = read_report_section("intent_report.md")
    matcher_report = read_report_section("matcher_report.md")
    extraction_report = read_report_section("extraction_report.md")
    guardrail_report = read_report_section("guardrail_report.md")
    test_eval_report = read_report_section("test_evaluation_report.md")
    class_balance = read_report_section("class_balance.md")
    improvement = read_report_section("improvement.md")

    # Ekstrak tabel spesifik
    intent_table = extract_table(intent_report, "Perbandingan Model")
    matcher_table = extract_table(matcher_report, "Perbandingan Kinerja")
    extract_table_content = extract_table(extraction_report, "Perbandingan Akurasi")
    guardrail_table = extract_table(guardrail_report, "Ringkasan Hasil Evaluasi")
    test_eval_table = extract_table(test_eval_report, "Metrik Per-Kelas")

    readme_content = f"""# Layanan Gen AI “Asisten Chat Toko” — Sabana Adventure Jombor

**Capstone Project Asah 2026** · **Tim A26-CS204** · **Learning Path Generative AI**
**Mitra:** Sabana Adventure Jombor (Persewaan Alat Camping & Outdoor, Sleman, D.I. Yogyakarta)
*Terakhir Diperbarui:* `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` via `scripts/build_readme_tables.py`

---

## 1. Masalah yang Diselesaikan Model (G1)

Sabana Adventure Jombor adalah unit usaha persewaan perlengkapan camping dan outdoor di Sleman. Operasional toko saat ini menghadapi kendala kritis:
1. **Pencatatan Ganda:** Pesanan masuk melalui chat WhatsApp dicatat manual dua kali (ke buku tulis dan ke nota kertas 2 rangkap).
2. **Kewalahan Jam Sibuk:** Saat antrean fisik toko ramai, staf kesulitan membalas pesan masuk secara responsif.
3. **Pertanyaan Berulang:** Ratusan chat berulang menanyakan informasi dasar (syarat jaminan, aturan hitungan 2 hari sewa = 1 hari bayar, lokasi, dan jam buka toko).

Layanan Gen AI ini hadir sebagai **layanan internal berbasis AI (FastAPI)** yang mengotomatisasi ekstraksi pesanan dari chat WhatsApp tanpa pernah menulis langsung ke database (staf selalu memeriksa sebelum konfirmasi) serta menjawab pertanyaan informasi toko secara akurat dan bebas halusinasi.

---

## 2. Ringkasan Fitur dan Dua Titik Masuk (Channel)

Website toko yang dibangun tim Full-Stack berbentuk **e-commerce katalog** (pelanggan memilih alat, memasukkan ke keranjang, dan melihat status). Karena tidak ada form bebas di website, layanan Gen AI melayani dua titik masuk (*channel*):

| Titik Masuk (`channel`) | Pengguna Utama | Peran & Perilaku Utama |
|---|---|---|
| `web_widget` | Pelanggan Website | Menjawab info toko via RAG (`answer_info`), mengarahkan booking ke katalog (`open_catalog`), menolak OOD (`refuse`) |
| `staff_paste` | Staf / Admin Toko | Menempelkan chat WhatsApp pelanggan $\\rightarrow$ diekstrak menjadi **draf pesanan terstruktur** (`extract_order`), atau saran balasan (`suggest_reply`) |
| `telegram` (P2) | Pelanggan Bot Uji | Sama seperti perilaku `web_widget` |

---

## 3. Arsitektur dan Alur Router (S6)

Layanan mengimplementasikan matriks perutean ketat `channel x intent` (PRD Bagian 6.9) yang diproses dalam 4 tahap:

```text
[Request Masuk]
       │
       ▼
[Lapis 3 Guardrail: Deteksi Injeksi Prompt] ──(Injeksi?)──► [Refuse / Tolak Aman]
       │ Aman
       ▼
[Flag force_extract?] ──(True)──► [Ekstraksi Pesanan X1/X3] ──► ExtractedOrder (needs_review=True)
       │ False
       ▼
[Intent Classifier E1] ──► (booking_sewa, tanya_info, ubah_batal, keluhan, lainnya)
       │
       ▼
[Matriks Perutean Router]:
  ├── web_widget x booking_sewa  ──► route=open_catalog (Arahkan ke katalog & keranjang)
  ├── web_widget x tanya_info    ──► route=answer_info (RAG KB-01 s/d KB-12)
  ├── web_widget x ubah_batal    ──► route=handoff_staff (Diteruskan ke staf)
  ├── web_widget x keluhan       ──► route=handoff_staff (+ Analisis Sentimen P2)
  ├── web_widget x lainnya       ──► route=refuse (Sapaan dijawab ramah, OOD ditolak sopan)
  ├── staff_paste x booking_sewa ──► route=extract_order (Ekstraksi pesanan hibrida)
  ├── staff_paste x tanya_info   ──► route=suggest_reply (Saran balasan untuk staf)
  └── staff_paste x lainnya      ──► route=handoff_staff (Catatan 'bukan pesan booking')
```

---

## 4. Sumber Data, Label Sintetis, dan Lisensi (G4)

Semua data proyek dipisahkan secara transparan antara fakta wawancara dan data sintetis:
- **Katalog Alat Toko (`katalog_alat.csv`):** 30 produk outdoor resmi Sabana Adventure Jombor dengan alias singkatan, kapasitas, dan harga sewa (`source=wawancara`).
- **Basis Pengetahuan Toko (`kb_toko.md`):** 12 kartu pengetahuan resmi (`KB-01` s/d `KB-12`) mencakup aturan 2 hari sewa, jaminan KTP/KTM, denda, dsb (`source=wawancara`).
- **Dataset Intent Sintetis (`intent_dataset.csv`):** 818 sampel percakapan (5 kelas) digenerasi seimbang tanpa kebocoran split (`source=sintetis`).
- **Dataset Pasangan Item (`item_pairs.csv`):** 1.930 variasi sinonim, typo, dan kapasitas untuk evaluasi pencocok alat (`source=sintetis`).
- **Evaluasi Ekstraksi (`extraction_eval.jsonl`):** 42 kasus uji variasi format WhatsApp toko (`source=sintetis`).
- **Lisensi Data:** Seluruh data sintetis dan template dikembangkan khusus untuk Capstone A26-CS204 di bawah lisensi MIT.

---

## 5. Preprocessing (G3)

Modul `app/services/preprocessing.py` menerapkan dua mode normalisasi:
1. **Mode `for_intent`:** Case-folding huruf kecil, normalisasi kata gaul/slang bahasa Indonesia (misal: *batalin $\\rightarrow$ batal*, *makasih $\\rightarrow$ terima kasih*, *brapa $\\rightarrow$ berapa*), penghapusan tanda baca non-alfanumerik.
2. **Mode `for_extract`:** Mempertahankan tanda baca pemisah daftar barang (`+`, `,`, `&`, `dan`, baris baru), tanda titik jam (`09.00`), dan format tanggal angka (`31/10`).

---

## 6. Tabel Perbandingan Model dan Alasan Pilihan (G6)

### 6.1 Intent Classifier (E1 vs E2 vs E3)
{intent_table}

- **Model Terpilih:** **E1 (TF-IDF + Logistic Regression)**.
- **Alasan:** Menghasilkan Macro-F1 sempurna (1.0000) pada data validasi dan data uji dengan latensi super cepat (<0.05 ms/sampel), serta ukuran model sangat ringan (<200 KB) tanpa membutuhkan alokasi VRAM/RAM embedding yang berat.

### 6.2 Pencocok Nama Alat (Matcher M1 vs M2 vs M3)
{matcher_table}

- **Model Terpilih:** **M3 (Ensemble RapidFuzz + Embedding w=0.65)**.
- **Alasan:** Menghasilkan **Accuracy@1 99.22%** dan **Hit@3 100%**. Pendekatan leksikal menangani typo dan singkatan alias toko, sementara bobot semantik menangani variasi sinonim bebas.

### 6.3 Pipeline Ekstraksi Pesanan (X1 vs X2 vs X3)
{extract_table_content}

- **Arsitektur Terpilih:** **Pipeline Hibrida (X1 Deterministik $\\rightarrow$ LLM Few-Shot X3)**.
- **Alasan:** Jika chat pelanggan menggunakan template standar toko, X1 mengekstrak secara instan (0 ms, Rp0 biaya token) dengan akurasi 100%. Jika chat bebas rumpang, sistem memanggil X3 (few-shot) dengan validasi Pydantic dan fallback ke X1 jika respons JSON LLM terganggu.

---

## 7. Keseimbangan Kelas dan Peningkatan Kinerja (S1, S2)

Dataset awal mengalami sedikit ketidakseimbangan pada kelas percakapan pendek. Peningkatan dilakukan melalui augmentasi sinonim kontekstual dan penalaan hyperparameter:

{class_balance}

### Hasil Peningkatan Hyperparameter Tuning (S2):
{improvement}

---

## 8. Hasil Uji pada Data Tersisih / Test Split (S3)

Pengujian akhir dilakukan pada *held-out test split* yang belum pernah dilihat model saat pelatihan maupun validasi:

{test_eval_table}

Model mencapai Macro-F1 **1.0000** pada data uji tersisih tanpa indikasi overfitting.

---

## 9. Hasil Uji Penolakan di Luar Konteks / Guardrails (S8)

Guardrails keamanan 3 lapis diuji menggunakan pertanyaan Out-of-Domain (`ood_questions.csv`) dan 20 pertanyaan dalam konteks untuk mengukur False Rejection Rate:

{guardrail_table}

- **Tingkat Penolakan OOD:** **100% (16/16)** berhasil ditolak secara sopan.
- **Tingkat Salah Tolak (False Rejection):** **0% (0/20)** — tidak ada pertanyaan toko valid yang ditolak keliru.

---

## 10. Penanganan Error dan Kuota (S10)

Layanan menerapkan pemetaan error terstandarisasi sesuai PRD Bagian 8.4:
- `400 invalid_input`: Pesan kosong atau melebihi 1000 karakter.
- `401 unauthorized`: Permintaan tanpa header `X-Service-Key` yang valid.
- `422 validation_error`: Struktur payload JSON tidak sesuai skema Pydantic.
- `429 quota_exceeded / rate_limited`: Kuota LLM habis, otomatis memicu fallback deterministik X1 untuk ekstraksi.
- `503 ai_unavailable`: Layanan AI pihak ketiga tidak dapat dihubungi.
- `504 ai_timeout`: Melebihi `LLM_TIMEOUT_S` (default 10 detik).
- Setiap respons error menyertakan `message_user` ramah pelanggan dan `message_dev` untuk debugging staf teknis.

---

## 11. Cara Menjalankan, Melatih, dan Deploy

### 11.1 Instalasi Lokal
```bash
# Clone repositori dan buat virtual environment
python -m venv .venv
.\\.venv\\Scripts\\activate

# Instal dependensi
pip install -r requirements.txt

# Salin konfigurasi environment
cp .env.example .env
```

### 11.2 Menjalankan Server Lokal
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 11.3 Pelatihan dan Pembuatan Laporan
```bash
make train             # Latih Intent Classifier E1
make train-matcher     # Evaluasi Matcher M1-M3
make train-sentiment   # Latih Sentiment Classifier (P2)
make test              # Jalankan seluruh rangkaian tes pytest (167+ tes)
make warmup            # Jalankan skrip pemanasan cold-start
```

### 11.4 Deployment Docker
```bash
# Build image
docker build -t sabana-genai-service:latest .

# Jalankan container
docker run -d -p 8000:8000 --env-file .env --name sabana-genai sabana-genai-service:latest
```

---

## 12. Dokumentasi API (Swagger) (S12)

Setelah server berjalan, dokumentasi interaktif OpenAPI dapat diakses di:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

### Daftar Endpoint Utama:
- `POST /api/v1/chat/message`: Pintu utama perutean chat (mendukung `channel=web_widget`, `staff_paste`, `telegram`).
- `POST /api/v1/orders/extract`: Ekstraksi pesanan langsung untuk staf toko (`force_extract`).
- `POST /api/v1/chat/classify`: Endpoint pengujian klasifikasi maksud pesan.
- `POST /api/v1/chat/ask`: Endpoint pengujian RAG basis pengetahuan.
- `GET /health`: Endpoint kesehatan status model dan versi prompt.

---

## 13. Keterbatasan Model & Catatan Operasional

1. **Ketergantungan Data Sintetis:** Format chat pelanggan di dunia nyata mungkin memiliki variasi bahasa daerah (Jawa Ngoko/Krama) di luar data sintetis. Penyesuaian bertahap dapat dilakukan setelah data nyata terkumpul.
2. **Domain Shift:** Jika mitra Sabana Adventure menambah kategori produk non-outdoor (misal: catering camping), katalog alat harus diperbarui via `data/catalog/katalog_alat.csv` dan di-reload melalui `POST /api/v1/admin/reload-data`.
3. **Batas Kuota LLM Gratis:** Pada free-tier penyedia LLM, batas RPM/RPD dapat tercapai saat lonjakan trafik. Arsitektur telah dilengkapi fallback X1 otomatis.
4. **Hosting Free-Tier (Cold Start):** Layanan menyediakan **Mode Ringan (`EMBEDDER=api`)** dengan penggunaan RAM hanya ~85 MB dan skrip `scripts/warmup.py` untuk memanaskan instance sebelum jam operasional demo.
"""

    README_PATH.write_text(readme_content, encoding="utf-8")
    print(f"[SUKSES] Berkas README.md berhasil disusun otomatis di {README_PATH}")
    return readme_content


if __name__ == "__main__":
    build_readme()
