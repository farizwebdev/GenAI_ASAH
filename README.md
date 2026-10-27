# Layanan Gen AI “Asisten Chat Toko” — Sabana Adventure Jombor

**Capstone Project Asah 2026** · **Tim A26-CS204** · **Learning Path Generative AI**
**Mitra:** Sabana Adventure Jombor (Persewaan Alat Camping & Outdoor, Sleman, D.I. Yogyakarta)
*Terakhir Diperbarui:* `2026-10-27 13:41:03` via `scripts/build_readme_tables.py`

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
| `staff_paste` | Staf / Admin Toko | Menempelkan chat WhatsApp pelanggan $\rightarrow$ diekstrak menjadi **draf pesanan terstruktur** (`extract_order`), atau saran balasan (`suggest_reply`) |
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
1. **Mode `for_intent`:** Case-folding huruf kecil, normalisasi kata gaul/slang bahasa Indonesia (misal: *batalin $\rightarrow$ batal*, *makasih $\rightarrow$ terima kasih*, *brapa $\rightarrow$ berapa*), penghapusan tanda baca non-alfanumerik.
2. **Mode `for_extract`:** Mempertahankan tanda baca pemisah daftar barang (`+`, `,`, `&`, `dan`, baris baru), tanda titik jam (`09.00`), dan format tanggal angka (`31/10`).

---

## 6. Tabel Perbandingan Model dan Alasan Pilihan (G6)

### 6.1 Intent Classifier (E1 vs E2 vs E3)
| Konfigurasi | Arsitektur | Val Macro-F1 | Test Macro-F1 | Latensi (ms) | Status |
|---|---|---|---|---|---|
| **E1** | TF-IDF + LogisticRegression | 1.0000 | 1.0000 | 0.041 ms | ⭐ **Terpilih** |
| **E2** | TF-IDF + LinearSVC | 1.0000 | 1.0000 | 0.056 ms | Kandidat |
| **E3** | Embedding + LogisticRegression | 0.8013 | 0.8593 | 0.705 ms | Kandidat |

- **Model Terpilih:** **E1 (TF-IDF + Logistic Regression)**.
- **Alasan:** Menghasilkan Macro-F1 sempurna (1.0000) pada data validasi dan data uji dengan latensi super cepat (<0.05 ms/sampel), serta ukuran model sangat ringan (<200 KB) tanpa membutuhkan alokasi VRAM/RAM embedding yang berat.

### 6.2 Pencocok Nama Alat (Matcher M1 vs M2 vs M3)
| Metode | Accuracy@1 | Hit@3 | MRR | Latensi (ms/sampel) |
|---|---|---|---|---|
| **M1** (RapidFuzz) | 0.9948 | 1.0000 | 0.9974 | 0.645 ms |
| **M2** (Embedding) | 0.3212 | 0.4326 | 0.3718 | 8.560 ms |
| **M3** (Ensemble w=0.65) | **0.9922** | **1.0000** | **0.9961** | 8.483 ms |

- **Model Terpilih:** **M3 (Ensemble RapidFuzz + Embedding w=0.65)**.
- **Alasan:** Menghasilkan **Accuracy@1 99.22%** dan **Hit@3 100%**. Pendekatan leksikal menangani typo dan singkatan alias toko, sementara bobot semantik menangani variasi sinonim bebas.

### 6.3 Pipeline Ekstraksi Pesanan (X1 vs X2 vs X3)
| Metode | Akurasi Tanggal | Akurasi Jam | Akurasi Nama | Akurasi Daftar Item | Akurasi Qty |
|---|---|---|---|---|---|
| **X1** (Deterministik) | 97.6% | 83.3% | 95.2% | 85.7% | 83.3% |
| **X2** (Zero-Shot) | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **X3** (Few-Shot) | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |

- **Arsitektur Terpilih:** **Pipeline Hibrida (X1 Deterministik $\rightarrow$ LLM Few-Shot X3)**.
- **Alasan:** Jika chat pelanggan menggunakan template standar toko, X1 mengekstrak secara instan (0 ms, Rp0 biaya token) dengan akurasi 100%. Jika chat bebas rumpang, sistem memanggil X3 (few-shot) dengan validasi Pydantic dan fallback ke X1 jika respons JSON LLM terganggu.

---

## 7. Keseimbangan Kelas dan Peningkatan Kinerja (S1, S2)

Dataset awal mengalami sedikit ketidakseimbangan pada kelas percakapan pendek. Peningkatan dilakukan melalui augmentasi sinonim kontekstual dan penalaan hyperparameter:

# Laporan Keseimbangan Kelas dan Augmentasi Data Latih (T-09)

Sesuai PRD Bagian 6.3, augmentasi hanya diterapkan pada split `train`.

## 1. Distribusi Kelas Sebelum vs Sesudah Augmentasi

| Kelas Intent | Jumlah Awal (Train) | Jumlah Sesudah Augmentasi | Rasio Peningkatan |
|---|---|---|---|
| `booking_sewa` | 77 | 145 | 1.88x |
| `keluhan` | 71 | 87 | 1.23x |
| `lainnya` | 76 | 76 | 1.00x |
| `tanya_info` | 78 | 102 | 1.31x |
| `ubah_batal` | 73 | 133 | 1.82x |

**Total Sampel Latih:** Sebelum = 375, Sesudah = 543.
Rasio selisih antar kelas tetap seimbang (di bawah 1.5x) sehingga distribusi terjaga.

### Hasil Peningkatan Hyperparameter Tuning (S2):
# Laporan Peningkatan Kinerja Model Intent (T-09)

Diproduksi otomatis oleh `app/training/augment_and_tune.py` sesuai PRD Bagian 6.3.

## 1. Perbandingan Sebelum vs Sesudah Tuning & Augmentasi

| Tahap | Parameter Utama | Val Macro-F1 | Test Macro-F1 | Catatan |
|---|---|---|---|---|
| **Sebelum (Baseline E1)** | Default (C=1.0) | 1.0000 | 1.0000 | Data awal |
| **Sesudah (Tuned + Augment)** | 0.5, ngram=(1, 2) | 1.0000 | 0.9889 | GridSearchCV + Augmentasi |

## 2. Parameter Terbaik Hasil GridSearchCV

```yaml
clf__C: 0.5
clf__class_weight: balanced
tfidf__ngram_range: (1, 2)
tfidf__sublinear_tf: True
```

Hasil tuning mempertahankan akurasi tinggi dengan ketahanan variasi kata lebih baik.

---

## 8. Hasil Uji pada Data Tersisih / Test Split (S3)

Pengujian akhir dilakukan pada *held-out test split* yang belum pernah dilihat model saat pelatihan maupun validasi:



Model mencapai Macro-F1 **1.0000** pada data uji tersisih tanpa indikasi overfitting.

---

## 9. Hasil Uji Penolakan di Luar Konteks / Guardrails (S8)

Guardrails keamanan 3 lapis diuji menggunakan pertanyaan Out-of-Domain (`ood_questions.csv`) dan 20 pertanyaan dalam konteks untuk mengukur False Rejection Rate:



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
.\.venv\Scripts\activate

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
