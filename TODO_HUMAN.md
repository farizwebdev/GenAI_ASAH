# TODO_HUMAN: Daftar Tindakan dan Keputusan Manusia

Dokumen ini mencatat hal-hal yang membutuhkan data asli, keputusan bisnis, atau kredensial dari pihak pengelola toko Sabana Adventure Jombor atau tim pengembang. AI Agent tidak boleh mengarang data fakta di bawah ini.

| ID | Item | Status | Catatan / Bagian PRD |
|---|---|---|---|
| H-01 | Pengisian API Key Layanan (`SERVICE_API_KEY`) | Menunggu | Bagian 7 & 8: Kunci autentikasi bersama antara Full-Stack Backend dan Gen AI Service. |
| H-02 | Kredensial LLM (`LLM_API_KEY` & `LLM_MODEL`) | Menunggu | Bagian 7: Kunci API Google Gemini (atau provider lain) dan nama model yang aktif di akun. |
| H-03 | Model Embedding (`EMBED_MODEL`) | Menunggu | Bagian 7: Penentuan model embedding lokal (Sentence Transformers) atau API. |
| H-04 | Informasi Denda & Keterlambatan (`KB-06`) | Menunggu | Bagian 5.6: Nilai denda nominal per hari/jam keterlambatan belum tersedia dari mitra. |
| H-05 | Ketentuan Jaminan Pelanggan Luar Jogja (`KB-04`) | Menunggu | Bagian 5.6: Aturan identitas jaminan untuk pelanggan ber-KTP luar DIY belum dikonfirmasi. |
| H-06 | Ketentuan Detail Ubah/Batal Sewa (`KB-11`) | Menunggu | Bagian 5.6: Batas waktu maksimal pembatalan dan refund uang muka (jika ada). |
| H-07 | Dataset Sentimen Bahasa Indonesia (P2) | Menunggu | Bagian 6.12 & T-22: File `data/external/sentiment_id.csv` harus disediakan manual dengan lisensi jelas. |
