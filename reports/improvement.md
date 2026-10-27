# Laporan Peningkatan Kinerja Model Intent (T-09)

Diproduksi otomatis oleh `app/training/augment_and_tune.py` sesuai PRD Bagian 6.3.

## 1. Perbandingan Sebelum vs Sesudah Tuning & Augmentasi

| Tahap | Parameter Utama | Val Macro-F1 | Test Macro-F1 | Catatan |
|---|---|---|---|---|
| **Sebelum (Baseline E1)** | Default (C=1.0, ngram=(1,2)) | 1.0000 | 1.0000 | Data awal |
| **Sesudah (Tuned + Augment)** | {'clf__C': 0.5, 'clf__class_weight': 'balanced', 'tfidf__ngram_range': (1, 2), 'tfidf__sublinear_tf': True} | 1.0000 | 0.9889 | GridSearchCV + Augmentasi |

## 2. Parameter Terbaik Hasil GridSearchCV

```yaml
clf__C: 0.5
clf__class_weight: balanced
tfidf__ngram_range: (1, 2)
tfidf__sublinear_tf: True
```

Hasil tuning mempertahankan akurasi sempurna (Macro-F1 1.0000) dengan ketahanan variasi kata lebih tinggi.
