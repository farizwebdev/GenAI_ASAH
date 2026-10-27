"""Layanan ekstraksi draf pesanan sewa alat camping (Extractor) sesuai PRD Bagian 6.6.

Pipeline ekstraksi:
1. Normalisasi teks dengan mode 'for_extract' (pertahankan baris baru dan label).
2. Pra-parse deterministik (X1) untuk templat toko (Nama, Tanggal ambil, Jam, List barang).
3. Jika templat tidak terdeteksi atau field kosong, panggil LLM (X2 zero-shot / X3 few-shot).
4. Validasi output JSON dengan Pydantic. Jika rusak: coba ulang 1x, lalu fallback ke X1.
5. Normalisasi tanggal dan jam dengan utilitas dates.py & times.py.
6. Pencocokan katalog alat untuk setiap item menggunakan ItemMatcher.
7. Penghitungan missing_fields (wajib: tanggal, jam, minimal 1 item; nama & kembali opsional).
8. Deteksi catatan khusus (misal penambahan barang saat di toko).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.llm.base import BaseLLMClient, get_llm_client
from app.llm.json_utils import clean_and_parse_json
from app.schemas.order import ExtractedOrder, OrderItem
from app.services.matcher import ItemMatcher, get_item_matcher
from app.services.preprocessing import normalize
from app.utils.dates import parse_date
from app.utils.times import parse_time

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROMPT_FILE = BASE_DIR / "prompts" / "extract_v1.txt"

# Pola frasa catatan penambahan barang di toko
EXTRA_NOTE_PATTERNS = [
    r"nanti\s+nambah\s+barang\s+di\s+toko.*",
    r"tambahan\s+.*pas\s+nyampe\s+toko.*",
    r"nambah\s+(?:di\s+)?toko.*",
    r"ambil\s+langsung\s+nambah\s+di\s+toko.*",
]


class OrderExtractor:
    """Ekstraktor pesan booking sewa menjadi draf pesanan ExtractedOrder."""

    def __init__(
        self,
        llm_client: BaseLLMClient | None = None,
        matcher: ItemMatcher | None = None,
        prompt_path: Path | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.matcher = matcher or get_item_matcher()
        self.prompt_path = prompt_path or PROMPT_FILE
        self._system_prompt_raw = ""
        self._load_prompt()

    def _load_prompt(self) -> None:
        """Memuat teks instruksi sistem dari berkas prompt."""
        if self.prompt_path.is_file():
            self._system_prompt_raw = self.prompt_path.read_text(encoding="utf-8")

    def _get_llm(self) -> BaseLLMClient:
        """Mengambil instance LLM Client secara lazy."""
        if self.llm_client is None:
            self.llm_client = get_llm_client()
        return self.llm_client

    def parse_deterministic_x1(
        self,
        text: str,
        reference_date: str | None = None,
    ) -> tuple[ExtractedOrder, bool]:
        """Pra-parse deterministik (X1) untuk format templat toko Sabana Adventure.

        Membaca pola baris berlabel:
        Nama: ...
        Tanggal ambil: ...
        Kisaran jam ambil / Jam: ...
        List barang / List: ...

        Returns:
            tuple: (ExtractedOrder, template_detected_flag)
        """
        orig_lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean_text = normalize(text, mode="for_extract")

        customer_name: str | None = None
        raw_date: str | None = None
        raw_time: str | None = None
        raw_items: list[str] = []
        extra_note: str | None = None
        warnings: list[str] = []

        template_detected = False

        # 1. Ekstrak baris berdasarkan label
        for line in orig_lines:
            lower_line = line.lower()

            # Deteksi Nama
            name_match = re.search(r"^(?:nama|customer)\s*:\s*(.+)$", lower_line)
            if name_match:
                customer_name = line[name_match.start(1):].strip()
                template_detected = True
                continue

            # Deteksi Tanggal Ambil
            date_match = re.search(
                r"^(?:tanggal(?:\s+ambil)?|tgl(?:\s+ambil)?)\s*:\s*(.+)$",
                lower_line,
            )
            if date_match:
                raw_date = line[date_match.start(1):].strip()
                template_detected = True
                continue

            # Deteksi Jam Ambil
            time_match = re.search(
                r"^(?:kisaran\s+jam(?:\s+ambil)?|jam(?:\s+ambil)?|waktu)\s*:\s*(.+)$",
                lower_line,
            )
            if time_match:
                raw_time = line[time_match.start(1):].strip()
                template_detected = True
                continue

            # Deteksi List Barang
            items_match = re.search(
                r"^(?:list(?:\s+barang)?|barang|pesanan)\s*:\s*(.+)$",
                lower_line,
            )
            if items_match:
                items_str = line[items_match.start(1):].strip()
                template_detected = True
                # Pisahkan daftar barang dengan koma, +, sama, dan, &
                parts = re.split(r",|\+|\bsama\b|\bdan\b|&", items_str)
                for p in parts:
                    clean_p = p.strip()
                    if clean_p:
                        raw_items.append(clean_p)
                continue

            # Deteksi Catatan Ekstra (misal: "Nanti nambah barang di toko")
            for pat in EXTRA_NOTE_PATTERNS:
                if re.search(pat, lower_line):
                    extra_note = line.strip()
                    break

        # 2. Jika bukan format templat berlabel, coba tangkap teks bebas
        if not template_detected:
            # Cari extra note di teks bebas
            for pat in EXTRA_NOTE_PATTERNS:
                note_m = re.search(pat, clean_text, re.IGNORECASE)
                if note_m:
                    extra_note = note_m.group(0).strip()
                    break

            # Cari tanggal & jam langsung dari teks bebas
            iso_d, d_warns = parse_date(clean_text, reference_date=reference_date)
            if iso_d:
                raw_date = clean_text
            start_t, end_t, t_warns = parse_time(clean_text)
            if start_t:
                raw_time = clean_text

            # Coba deteksi item jika ada kata sewa / booking / ambil
            item_split_parts = re.split(
                r",|\+|\bsama\b|\bdan\b|&|\bambil\b|\bsewa\b|\bbooking\b",
                clean_text,
            )
            for part in item_split_parts:
                cand_item = part.strip()
                # Jika kandidat mengandung kata kunci alat camping
                if len(cand_item) > 2 and any(
                    k in cand_item.lower()
                    for k in [
                        "tenda", "carrier", "keril", "matras", "sleeping",
                        "sb", "kompor", "nesting", "gas", "headlamp",
                        "sepatu", "jaket", "ponco", "kursi", "meja",
                        "hammock", "flysheet", "flyseat", "pole",
                    ]
                ):
                    raw_items.append(cand_item)

        # 3. Normalisasi Tanggal & Jam
        pickup_date = None
        if raw_date:
            parsed_d, d_warns = parse_date(raw_date, reference_date=reference_date)
            pickup_date = parsed_d
            warnings.extend(d_warns)

        pickup_start = None
        pickup_end = None
        if raw_time:
            parsed_s, parsed_e, t_warns = parse_time(raw_time)
            pickup_start = parsed_s
            pickup_end = parsed_e
            warnings.extend(t_warns)

        # 4. Pencocokan Item ke Katalog
        order_items: list[OrderItem] = []
        for raw_item in raw_items:
            matched_item = self.matcher.match_item(raw_item)
            order_items.append(matched_item)
            if matched_item.notes:
                for note in matched_item.notes.split("; "):
                    if note not in warnings:
                        warnings.append(note)

        # 5. Hitung Missing Fields
        missing_fields: list[str] = []
        if not pickup_date:
            missing_fields.append("pickup_date")
        if not pickup_start and not raw_time:
            missing_fields.append("pickup_time")
        if not order_items:
            missing_fields.append("items")

        order = ExtractedOrder(
            customer_name=customer_name,
            pickup_date=pickup_date,
            pickup_time_start=pickup_start,
            pickup_time_end=pickup_end,
            pickup_time_raw=raw_time,
            return_date=None,
            items=order_items,
            extra_note=extra_note,
            missing_fields=missing_fields,
            warnings=warnings,
            needs_review=True,
        )

        return order, template_detected

    def _build_prompt(
        self,
        message: str,
        reference_date: str | None = None,
        few_shot: bool = True,
    ) -> tuple[str, str]:
        """Menyiapkan system prompt dan user message untuk LLM."""
        ref_d = reference_date or "2026-10-28"

        if few_shot or not self._system_prompt_raw:
            sys_prompt = self._system_prompt_raw
        else:
            # Mode X2: Ambil bagian sebelum FEW-SHOT EXAMPLES
            parts = self._system_prompt_raw.split("--- FEW-SHOT EXAMPLES ---")
            sys_prompt = parts[0].strip()

        user_content = (
            f"reference_date: {ref_d}\n\n"
            f"Pesan pelanggan:\n{message}"
        )
        return sys_prompt, user_content

    def _call_llm_json(
        self,
        sys_prompt: str,
        user_content: str,
    ) -> dict[str, Any]:
        """Memanggil LLM dengan mekanisme retry 1x jika JSON rusak."""
        llm = self._get_llm()
        try:
            resp_text = llm.generate(user_content, system_instruction=sys_prompt)
            return clean_and_parse_json(resp_text)
        except Exception as exc:
            logger.warning(f"Percobaan 1 parsing JSON LLM gagal ({exc}), mencoba ulang...")
            # Retry 1x sesuai PRD 6.6
            retry_prompt = (
                f"{user_content}\n\n"
                "PENTING: Keluaran harus HANYA SATU OBJEK JSON VALID murni, tanpa teks lain."
            )
            resp_text_retry = llm.generate(retry_prompt, system_instruction=sys_prompt)
            return clean_and_parse_json(resp_text_retry)

    def extract(
        self,
        message: str,
        reference_date: str | None = None,
        method: str = "hybrid",
    ) -> tuple[ExtractedOrder, bool]:
        """Mengekstrak draf pesanan sewa dari pesan pelanggan.

        Args:
            message: Teks mentah pesan booking dari pelanggan toko.
            reference_date: Tanggal acuan YYYY-MM-DD.
            method: 'hybrid' (X1 jika templat lengkap, LLM jika tidak),
                    'x1' (deterministik murni),
                    'x2' (zero-shot LLM),
                    'x3' (few-shot LLM).

        Returns:
            tuple[ExtractedOrder, bool]: (hasil_ekstraksi, fallback_used_flag)
        """
        ref_d = reference_date or "2026-10-28"
        x1_order, template_detected = self.parse_deterministic_x1(
            message, reference_date=ref_d
        )

        # Jika metode X1 diminta, kembalikan hasil deterministik
        if method == "x1":
            return x1_order, False

        # Jika metode hybrid dan templat berlabel terdeteksi lengkap
        if method == "hybrid" and template_detected and len(x1_order.missing_fields) == 0:
            return x1_order, False

        # Gunakan LLM (X2 atau X3)
        few_shot = (method != "x2")
        sys_prompt, user_content = self._build_prompt(
            message, reference_date=ref_d, few_shot=few_shot
        )

        try:
            json_dict = self._call_llm_json(sys_prompt, user_content)

            # Validasi dan konversi tanggal & jam dengan utilitas
            raw_d = json_dict.get("pickup_date")
            parsed_d, d_warns = (
                parse_date(str(raw_d), reference_date=ref_d) if raw_d else (None, [])
            )

            raw_time_str = json_dict.get("pickup_time_raw") or json_dict.get("pickup_time_start")
            start_t = None
            end_t = None
            t_warns = []
            if raw_time_str:
                start_t, end_t, t_warns = parse_time(str(raw_time_str))
            elif json_dict.get("pickup_time_start"):
                start_t, end_t, t_warns = parse_time(str(json_dict.get("pickup_time_start")))

            # Pencocokan katalog alat untuk setiap item yang diekstrak LLM
            llm_items = json_dict.get("items", [])
            order_items: list[OrderItem] = []
            warnings: list[str] = list(json_dict.get("warnings", []))
            warnings.extend(d_warns)
            warnings.extend(t_warns)

            for item_raw in llm_items:
                if isinstance(item_raw, dict):
                    raw_text = str(item_raw.get("raw_text", ""))
                    matched = self.matcher.match_item(raw_text)
                    # Jika LLM memiliki qty lebih spesifik
                    if "qty" in item_raw and int(item_raw["qty"]) > 1:
                        matched.qty = int(item_raw["qty"])
                    order_items.append(matched)
                    if matched.notes:
                        for n in matched.notes.split("; "):
                            if n not in warnings:
                                warnings.append(n)
                elif isinstance(item_raw, str):
                    matched = self.matcher.match_item(item_raw)
                    order_items.append(matched)

            # Hitung missing_fields
            missing_fields: list[str] = []
            if not parsed_d:
                missing_fields.append("pickup_date")
            if not start_t and not raw_time_str:
                missing_fields.append("pickup_time")
            if not order_items:
                missing_fields.append("items")

            extracted = ExtractedOrder(
                customer_name=json_dict.get("customer_name"),
                pickup_date=parsed_d,
                pickup_time_start=start_t or json_dict.get("pickup_time_start"),
                pickup_time_end=end_t or json_dict.get("pickup_time_end"),
                pickup_time_raw=raw_time_str,
                return_date=json_dict.get("return_date"),
                items=order_items,
                extra_note=json_dict.get("extra_note"),
                missing_fields=missing_fields,
                warnings=sorted(set(warnings)),
                needs_review=True,
            )
            return extracted, False

        except Exception as exc:
            logger.warning(
                f"Ekstraksi LLM gagal ({exc}), menggunakan fallback X1 deterministik."
            )
            # Fallback ke X1 sesuai PRD 6.6
            return x1_order, True


_extractor_instance: OrderExtractor | None = None


def get_order_extractor() -> OrderExtractor:
    """Mengambil instance singleton OrderExtractor."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = OrderExtractor()
    return _extractor_instance
