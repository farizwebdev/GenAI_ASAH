# Laporan Evaluasi Data Uji Final (T-10)

Diproduksi otomatis oleh `app/training/evaluate.py` sesuai PRD Bagian 11 (T-10).
Evaluasi dilakukan murni pada data uji (*test split*) yang tidak pernah disentuh saat pelatihan.

## 1. Ringkasan Metrik Evaluasi Data Uji

- **Model Dievaluasi:** `E1_tuned_augmented`
- **Jumlah Sampel Uji:** 96
- **Test Macro-F1:** `0.9889`
- **Test Weighted-F1:** `0.9896`
- **Latensi Inferensi:** `0.179 ms/sampel`

## 2. Rincian Metrik per Kelas

| Kelas Intent | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| `booking_sewa` | 0.9444 | 1.0000 | 0.9714 | 17.0 |
| `keluhan` | 1.0000 | 1.0000 | 1.0000 | 23.0 |
| `lainnya` | 1.0000 | 1.0000 | 1.0000 | 20.0 |
| `tanya_info` | 1.0000 | 1.0000 | 1.0000 | 17.0 |
| `ubah_batal` | 1.0000 | 0.9474 | 0.9730 | 19.0 |

## 3. Matriks Kebingungan (Confusion Matrix) pada Data Uji

Kelas: `booking_sewa, keluhan, lainnya, tanya_info, ubah_batal`

```text
[[17,  0,  0,  0,  0],
 [ 0, 23,  0,  0,  0],
 [ 0,  0, 20,  0,  0],
 [ 0,  0,  0, 17,  0],
 [ 1,  0,  0,  0, 18]]
```
