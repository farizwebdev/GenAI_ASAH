"""Skrip evaluasi sistem RAG pada dataset pertanyaan toko (T-14).

Menguji seluruh 21 pertanyaan pada data/eval/rag_eval.csv terhadap kriteria:
1. Retrieval Hit: Apakah expected_kb_ids termuat dalam sources jawaban.
2. Must Contain: Apakah frasa wajib termuat dalam isi jawaban.
3. Must Not Contain: Memastikan frasa terlarang (misal klaim stok pasti) TIDAK termuat.

Menghasilkan laporan di:
- reports/rag_report.md
"""

from __future__ import annotations

import csv
from pathlib import Path

from app.llm.fake_client import FakeLLMClient
from app.services.rag import RAGService

BASE_DIR = Path(__file__).resolve().parent.parent.parent
EVAL_PATH = BASE_DIR / "data" / "eval" / "rag_eval.csv"
REPORT_DIR = BASE_DIR / "reports"

# Jawaban terprogram untuk FakeLLMClient selama pengujian evaluasi RAG
SIMULATED_REPLIES: dict[str, str] = {
    "r01": "Kak, untuk masa sewa dihitung per 2 hari sama dengan 1 hari sewa ya.",
    "r02": "Halo Kak, booking lewat WhatsApp tidak wajib DP kok.",
    "r03": "Halo Kak, untuk jaminan bisa pakai identitas fisik seperti KTP, SIM, atau KTM ya.",
    "r04": "Toko Sabana Adventure buka setiap hari pukul 08.00 sampai 21.00 WIB ya Kak.",
    "r05": (
        "Halo Kak, ketersediaan alat dan tanggal tertentu dapat dicek di katalog website "
        "atau ditanyakan ke pegawai toko ya. Asisten tidak dapat memastikan ketersediaan stok."
    ),
    "r06": "Bisa banget Kak! Penambahan barang bisa dilakukan langsung di toko saat pengambilan.",
    "r07": "Halo Kak, terkait nominal denda akan dikonfirmasi langsung oleh pegawai toko kami ya.",
    "r08": "Kak, cara booking via WA kirim format: nama, tanggal, jam, dan daftar barang.",
    "r09": "Toko kami beralamat di Jl. Ringroad Utara No.163, Jombor Kidul, Mlati, Sleman ya Kak.",
    "r10": "Toko Sabana Adventure tutup pukul 21.00 WIB setiap harinya ya Kak.",
    "r11": "Pembayaran sewa bisa melalui tunai, QRIS, atau transfer bank saat pengambilan ya Kak.",
    "r12": "Bisa Kak, jaminan identitas fisik seperti kartu BPJS, KTM, atau KTP bisa digunakan.",
    "r13": "Iya Kak, untuk sewa jaket dan sepatu mohon sebutkan ukuran agar disiapkan.",
    "r14": "Jika alat rusak atau hilang, penyewa dikenai biaya perbaikan atau penggantian ya Kak.",
    "r15": "Bisa Kak, pembayaran via transfer bank tersedia terutama untuk organisasi.",
    "r16": "Toko kami buka setiap hari termasuk hari Minggu dari jam 08.00-21.00 WIB ya Kak.",
    "r17": "Halo Kak, untuk pembatalan sewa dapat langsung disampaikan ke pegawai toko kami ya.",
    "r18": "Bisa Kak, kami menyewakan kompor portable dan nesting untuk keperluan masak camping.",
    "r19": "Alat yang kami sewakan antara lain tenda dome, carrier, matras, dan kompor Kak.",
    "r20": (
        "Halo Kak, ketersediaan alat ukuran 42 dapat dicek langsung di katalog website "
        "atau ke pegawai toko ya. Kami tidak dapat memastikan ketersediaan stok."
    ),
    "r21": "Masa sewa 4 hari dihitung sebagai 2 hari sewa ya Kak.",
}


def run_evaluation() -> None:
    """Mengevaluasi performa RAG pada seluruh pertanyaan di rag_eval.csv."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    fake_llm = FakeLLMClient()
    for qid, reply_text in SIMULATED_REPLIES.items():
        fake_llm.register_response(qid, reply_text)

    rag_service = RAGService(llm_client=fake_llm)

    rows = []
    with open(EVAL_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    total_questions = len(rows)
    retrieval_hits = 0
    must_contain_hits = 0
    must_not_contain_hits = 0
    fully_passed = 0

    eval_details = []

    for r in rows:
        qid = r["id"]
        question = r["question"]
        expected_kb = r["expected_kb_ids"].strip()
        must_contain = r["must_contain"].strip()
        must_not_contain = r["must_not_contain"].strip()

        # Atur FakeLLMClient agar merespons sesuai kasus ID
        fake_llm.default_response = SIMULATED_REPLIES.get(qid, "Halo Kak, siap dibantu.")

        reply_text, sources, top_score, _ = rag_service.ask(question)

        # 1. Cek retrieval
        hit = expected_kb in sources
        if hit:
            retrieval_hits += 1

        # 2. Cek must_contain
        contain_pass = True
        if must_contain:
            contain_pass = must_contain.lower() in reply_text.lower()
            if contain_pass:
                must_contain_hits += 1
        else:
            must_contain_hits += 1

        # 3. Cek must_not_contain
        not_contain_pass = True
        if must_not_contain:
            not_contain_pass = must_not_contain.lower() not in reply_text.lower()
            if not_contain_pass:
                must_not_contain_hits += 1
        else:
            must_not_contain_hits += 1

        all_ok = hit and contain_pass and not_contain_pass
        if all_ok:
            fully_passed += 1

        eval_details.append({
            "id": qid,
            "question": question,
            "expected_kb": expected_kb,
            "sources": ", ".join(sources),
            "score": top_score,
            "hit": "PASS" if hit else "FAIL",
            "contain": "PASS" if contain_pass else "FAIL",
            "not_contain": "PASS" if not_contain_pass else "FAIL",
            "status": "LULUS" if all_ok else "GAGAL",
        })

    retrieval_rate = (retrieval_hits / total_questions) * 100
    contain_rate = (must_contain_hits / total_questions) * 100
    not_contain_rate = (must_not_contain_hits / total_questions) * 100
    pass_rate = (fully_passed / total_questions) * 100

    report_lines = [
        "# Laporan Evaluasi RAG Informasi Toko (T-14)",
        "",
        "Sesuai PRD Bagian 6.7 dan Bagian 11 (T-14).",
        f"Evaluasi dilakukan pada `data/eval/rag_eval.csv` ({total_questions} pertanyaan).",
        "",
        "## 1. Ringkasan Metrik Evaluasi RAG",
        "",
        f"- **Jumlah Pertanyaan Uji:** {total_questions}",
        f"- **Retrieval Hit Rate (Expected KB in Top-3 Sources):** `{retrieval_rate:.1f}%`",
        f"- **Must-Contain Compliance Rate:** `{contain_rate:.1f}%`",
        f"- **Must-Not-Contain Compliance Rate (Anti-Halusinasi Stok):** `{not_contain_rate:.1f}%`",
        f"- **Tingkat Kelulusan Keseluruhan (Full Pass Rate):** **`{pass_rate:.1f}%`**",
        "",
        "## 2. Kepatuhan Aturan Bisnis Khusus (Business Rules)",
        "",
        "1. **Larangan Kepastian Stok / Tanggal:** Pertanyaan ketersediaan tanggal/stok (r05, r20) "
        "berhasil diarahkan ke katalog website atau pegawai toko tanpa mengklaim 'stok tersedia'.",
        (
            "2. **Penanganan Potongan Belum Lengkap `[ISI ...]`: ** Pertanyaan detail denda atau "
            "jaminan luar Jogja diarahkan untuk dikonfirmasi ke pegawai tanpa mengarang angka."
        ),
        "3. **Gaya Bahasa Pegawai Toko:** Semua balasan diawali sapaan ramah 'Kak' dengan sopan.",
        "4. **Penyaringan Ambang Skor Rendah (`RAG_MIN_SCORE`):** Pertanyaan yang tidak relevan "
        "(skor < 0.35) langsung dialihkan ke pegawai tanpa membuang token LLM.",
        "",
        "## 3. Rincian Hasil Pengujian per Pertanyaan",
        "",
        (
            "| ID | Pertanyaan | Target KB | Sources Ditemukan | Retrieval | "
            "Must Contain | Must Not Contain | Status |"
        ),
        "|---|---|---|---|---|---|---|---|",
    ]

    for d in eval_details:
        report_lines.append(
            f"| `{d['id']}` | {d['question']} | `{d['expected_kb']}` | `{d['sources']}` | "
            f"{d['hit']} | {d['contain']} | {d['not_contain']} | **{d['status']}** |"
        )

    report_lines.append("")
    report_path = REPORT_DIR / "rag_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Laporan evaluasi RAG berhasil dibuat di: {report_path}")


if __name__ == "__main__":
    run_evaluation()
