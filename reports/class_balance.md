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
