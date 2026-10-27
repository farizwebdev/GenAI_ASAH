# Laporan Evaluasi Pencocok Nama Alat (Matcher M1–M3) (T-11)

Sesuai PRD Bagian 6.4 dan Bagian 11 (T-11).
Evaluasi dilakukan pada dataset pasangan item (`data/synthetic/item_pairs.csv`)
khususnya pada split data uji (*test split*) dengan total **386 sampel**.

## 1. Deskripsi Metode Pencocokan

- **M1 (Lexical Fuzzy):** Menggunakan library RapidFuzz (`token_set_ratio` & `WRatio`) yang dicocokkan ke nama resmi dan seluruh alias katalog alat.
- **M2 (Semantic Embedding):** Menggunakan representasi vektor embedding kosinus antara teks masukan pelanggan dengan gabungan deskripsi alat di katalog.
- **M3 (Ensemble Berbobot):** Kombinasi linier `w * M1 + (1 - w) * M2` dengan bobot optimal `w = 0.65` hasil tuning.

## 2. Tabel Perbandingan Kinerja pada Data Uji (Test Split)

| Metode | Accuracy@1 | Hit@3 | MRR | Latensi (ms/sampel) |
|---|---|---|---|---|
| **M1** (RapidFuzz) | 0.9948 | 1.0000 | 0.9974 | 0.645 ms |
| **M2** (Embedding) | 0.3212 | 0.4326 | 0.3718 | 8.560 ms |
| **M3** (Ensemble w=0.65) | **0.9922** | **1.0000** | **0.9961** | 8.483 ms |

## 3. Analisis dan Pilihan Model Final

- **Model Terpilih:** **M3** (bobot `w=0.65`).
- **Alasan:** M3 memberikan keseimbangan optimal antara kecepatan leksikal (M1) dan ketahanan semantik (M2). M1 sangat unggul pada singkatan dan typo persis, sementara M2 memperkuat pencarian ketika ada variasi kata bebas.
- **Aturan Keputusan Status:**
  - `matched`: Skor $\ge 0.85$ dan selisih (margin) ke kandidat kedua $\ge 0.10$.
  - `ambiguous`: Skor antara $0.60$ hingga $0.85$ atau margin kecil.
  - `unmatched`: Skor di bawah $0.60$.

## 4. Contoh Penanganan Kasus Nyata

| Input Mentah | Item Terpilih | Qty | Spec Terdeteksi | Status | Peringatan |
|---|---|---|---|---|---|
| `tenda kap 4` | `TND-DOME-4` | 1 | `kapasitas: 4` | `matched` | - |
| `sleeping back` | `SLB-STD` | 1 | - | `matched` | - |
| `matras 2` | `MTR-SPONS` | 2 | - | `matched` | - |
| `sepatu` | `SPT-HIK` | 1 | - | `ambiguous` | `ukuran sepatu belum disebut` |
| `tenda dome 2` | `TND-DOME-2` | 1 | `kapasitas: 2` | `matched` | `angka 2 dapat berarti jumlah` |
| `playstation 5` | `None` | 1 | - | `unmatched` | - |
