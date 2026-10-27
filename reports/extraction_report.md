# Laporan Evaluasi Pipeline Ekstraksi Pesanan (X1–X3) (T-13)

Sesuai PRD Bagian 6.6 dan Bagian 11 (T-13).
Evaluasi dilakukan pada `data/eval/extraction_eval.jsonl` (42 kasus uji).

## 1. Deskripsi Metode Ekstraksi

- **X1 (Pra-parse Deterministik):** Mengekstrak data berdasarkan pola templat toko (`Nama:`, `Tanggal ambil:`, `Jam:`, `List:`) dengan regex murni tanpa LLM. Kecepatan seketika (0 ms) dan biaya Rp0.
- **X2 (Zero-Shot LLM):** Menggunakan instruksi sistem `prompts/extract_v1.txt` tanpa contoh few-shot.
- **X3 (Few-Shot LLM):** Menggunakan instruksi sistem `prompts/extract_v1.txt` dengan 3 contoh few-shot lengkap (templat terisi, tanggal relatif, dan penambahan di toko).

## 2. Tabel Perbandingan Akurasi per Kolom

| Metode | Akurasi Tanggal | Akurasi Jam | Akurasi Nama | Akurasi Daftar Item | Akurasi Qty |
|---|---|---|---|---|---|
| **X1** (Deterministik) | 97.6% | 83.3% | 95.2% | 85.7% | 83.3% |
| **X2** (Zero-Shot) | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **X3** (Few-Shot) | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |

## 3. Analisis dan Desain Pipeline Hibrida

1. **Keunggulan X1:** Bekerja sempurna pada format WhatsApp resmi toko yang rapi. Pada format berlabel, X1 menghasilkan akurasi 100% tanpa memakan token atau latensi LLM.
2. **Kelemahan X1:** Pada pesan percakapan bebas (contoh: *'sabtu ini jam 9 pagi ambil keril 60 sama matras 2'*), X1 tidak dapat menangkap nama atau batas item yang ambigu.
3. **Peran X3 (Few-Shot):** Mampu menangkap konteks kompleks seperti tanggal relatif terhadap `reference_date`, frasa penambahan barang di toko ke `extra_note`, dan membedakan kapasitas dari jumlah unit.
4. **Strategi Hibrida Final:** Pipeline `OrderExtractor` pertama-tama menjalankan X1. Bila format templat terdeteksi lengkap tanpa ada field wajib yang kosong, sistem langsung menggunakan hasil X1. Bila pesan tidak berformat atau ada data yang rumpang, sistem memanggil LLM X3 dengan fallback aman ke X1 bila respons LLM rusak.

## 4. Mekanisme Keamanan & Penanganan Kesalahan

- **Validasi Skema:** Output LLM divalidasi dengan skema Pydantic `ExtractedOrder`.
- **Normalisasi Tanggal/Jam:** Output tanggal/jam dari LLM tidak langsung dipercaya, melainkan diverifikasi ulang dengan `app/utils/dates.py` dan `app/utils/times.py`.
- **Pencocokan Katalog:** Setiap nama alat selalu divalidasi ke katalog resmi via `ItemMatcher` untuk mencegah halusinasi nama produk.
- **Status Review:** Seluruh draf pesanan selalu ditandai `needs_review=True` agar staf toko dapat meninjau sebelum draf difinalisasi.
