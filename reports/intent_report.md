# Laporan Pelatihan Model Intent Klasifikasi (E1 - E3)

Diproduksi secara otomatis oleh `app/training/train_intent.py` sesuai PRD Bagian 6.2.

## 1. Tabel Perbandingan Model

| Konfigurasi | Arsitektur | Val Macro-F1 | Test Macro-F1 | Latensi (ms) | Status |
|---|---|---|---|---|---|
| **E1** | TF-IDF + LogisticRegression | 1.0000 | 1.0000 | 0.070 ms | ⭐ **Terpilih** |
| **E2** | TF-IDF + LinearSVC | 1.0000 | 1.0000 | 0.265 ms | Kandidat |
| **E3** | Embedding + LogisticRegression | 0.8013 | 0.8593 | 0.417 ms | Kandidat |

*Model terbaik dipilih berdasarkan skor tertinggi pada dataset **Validation (Val)**.*

## 2. Kinerja per Kelas Model Terbaik (E1)

| Kelas Intent | F1-Score pada Test |
|---|---|
| `booking_sewa` | 1.0000 |
| `keluhan` | 1.0000 |
| `lainnya` | 1.0000 |
| `tanya_info` | 1.0000 |
| `ubah_batal` | 1.0000 |

## 3. Matriks Kebingungan (Confusion Matrix) Model Terbaik (E1)

Kelas: `booking_sewa, keluhan, lainnya, tanya_info, ubah_batal`

```text
[[17,  0,  0,  0,  0],
 [ 0, 23,  0,  0,  0],
 [ 0,  0, 20,  0,  0],
 [ 0,  0,  0, 17,  0],
 [ 0,  0,  0,  0, 19]]
```
