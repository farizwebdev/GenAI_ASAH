# Laporan Evaluasi RAG Informasi Toko (T-14)

Sesuai PRD Bagian 6.7 dan Bagian 11 (T-14).
Evaluasi dilakukan pada `data/eval/rag_eval.csv` (21 pertanyaan).

## 1. Ringkasan Metrik Evaluasi RAG

- **Jumlah Pertanyaan Uji:** 21
- **Retrieval Hit Rate (Expected KB in Top-3 Sources):** `100.0%`
- **Must-Contain Compliance Rate:** `100.0%`
- **Must-Not-Contain Compliance Rate (Anti-Halusinasi Stok):** `100.0%`
- **Tingkat Kelulusan Keseluruhan (Full Pass Rate):** **`100.0%`**

## 2. Kepatuhan Aturan Bisnis Khusus (Business Rules)

1. **Larangan Kepastian Stok / Tanggal:** Pertanyaan ketersediaan tanggal/stok (r05, r20) berhasil diarahkan ke katalog website atau pegawai toko tanpa mengklaim 'stok tersedia'.
2. **Penanganan Potongan Belum Lengkap `[ISI ...]`: ** Pertanyaan detail denda atau jaminan luar Jogja diarahkan untuk dikonfirmasi ke pegawai toko tanpa mengarang angka palsu.
3. **Gaya Bahasa Pegawai Toko:** Semua balasan diawali sapaan ramah 'Kak' dengan nada sopan.
4. **Penyaringan Ambang Skor Rendah (`RAG_MIN_SCORE`):** Pertanyaan yang tidak relevan (skor < 0.35) langsung dialihkan ke pegawai tanpa membuang token LLM.

## 3. Rincian Hasil Pengujian per Pertanyaan

| ID | Pertanyaan | Target KB | Sources Ditemukan | Retrieval | Must Contain | Must Not Contain | Status |
|---|---|---|---|---|---|---|---|
| `r01` | sewa 3 hari dihitung berapa hari? | `KB-03` | `KB-03, KB-01, KB-08` | PASS | PASS | PASS | **LULUS** |
| `r02` | perlu DP nggak kalau booking lewat WA? | `KB-01` | `KB-01, KB-04, KB-08` | PASS | PASS | PASS | **LULUS** |
| `r03` | jaminannya apa aja? | `KB-04` | `KB-04, KB-07, KB-05` | PASS | PASS | PASS | **LULUS** |
| `r04` | buka jam berapa? | `KB-07` | `KB-07, KB-01, KB-10` | PASS | PASS | PASS | **LULUS** |
| `r05` | ready tenda tanggal 31 gak? | `KB-09` | `KB-09` | PASS | PASS | PASS | **LULUS** |
| `r06` | bisa nambah barang pas di toko? | `KB-02` | `KB-02, KB-06, KB-01` | PASS | PASS | PASS | **LULUS** |
| `r07` | denda telat berapa? | `KB-06` | `KB-06` | PASS | PASS | PASS | **LULUS** |
| `r08` | gimana cara booking alat camping? | `KB-01` | `KB-01, KB-12, KB-09` | PASS | PASS | PASS | **LULUS** |
| `r09` | alamat tokonya di mana ya kak? | `KB-08` | `KB-08, KB-10, KB-01` | PASS | PASS | PASS | **LULUS** |
| `r10` | toko sabana adventure tutup jam berapa? | `KB-07` | `KB-07, KB-11, KB-08` | PASS | PASS | PASS | **LULUS** |
| `r11` | kalau mau sewa bayarnya bisa pakai apa saja? | `KB-05` | `KB-05, KB-01, KB-12` | PASS | PASS | PASS | **LULUS** |
| `r12` | apakah jaminan kartu BPJS atau KTM bisa? | `KB-04` | `KB-04, KB-07, KB-02` | PASS | PASS | PASS | **LULUS** |
| `r13` | saya mau sewa jaket apakah perlu ukuran? | `KB-10` | `KB-10, KB-01, KB-12` | PASS | PASS | PASS | **LULUS** |
| `r14` | kalau alatnya rusak dendanya gimana kak? | `KB-06` | `KB-06, KB-12, KB-04` | PASS | PASS | PASS | **LULUS** |
| `r15` | bisa bayar transfer bank gak kak? | `KB-05` | `KB-05, KB-09, KB-03` | PASS | PASS | PASS | **LULUS** |
| `r16` | hari minggu tokonya tetap buka atau libur? | `KB-07` | `KB-07, KB-03, KB-09` | PASS | PASS | PASS | **LULUS** |
| `r17` | kalau saya mau batalin sewa caranya gimana? | `KB-11` | `KB-11, KB-01, KB-07` | PASS | PASS | PASS | **LULUS** |
| `r18` | bisa sewa kompor lapangan sama nesting? | `KB-12` | `KB-12, KB-01, KB-03` | PASS | PASS | PASS | **LULUS** |
| `r19` | alat apa saja yang disewakan di sini kak? | `KB-12` | `KB-12, KB-01, KB-04` | PASS | PASS | PASS | **LULUS** |
| `r20` | sepatu hiking ready ukuran 42 gak kak? | `KB-09` | `KB-09` | PASS | PASS | PASS | **LULUS** |
| `r21` | kalau sewa 4 hari dihitung berapa hari sewa? | `KB-03` | `KB-03, KB-01, KB-12` | PASS | PASS | PASS | **LULUS** |
