"""Layanan pencocokan nama alat camping (Item Matcher) sesuai PRD Bagian 6.4 & 6.4a.

Menyediakan:
- Parsing kuantitas (qty) dan spesifikasi (kapasitas, ukuran, volume).
- Tiga metode pencocokan:
  - M1: RapidFuzz lexical matching (token_set_ratio & WRatio) terhadap nama dan alias.
  - M2: Cosine similarity embedding teks mentah terhadap embedding katalog alat.
  - M3: Gabungan berbobot w*M1 + (1-w)*M2 dengan bobot optimal.
- Aturan keputusan status: matched (>=0.85 & margin>=0.1), ambiguous (0.6-0.85), unmatched (<0.6).
- Peringatan ukuran untuk sepatu dan jaket jika ukuran belum disebut.
"""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field
from rapidfuzz import fuzz

from app.embeddings.base import get_embedder
from app.schemas.common import ItemStatusEnum
from app.schemas.order import OrderItem
from app.services.preprocessing import normalize

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = BASE_DIR / "data" / "catalog" / "katalog_alat.csv"

# Bobot default M3 (berdasarkan tuning pada validation split)
DEFAULT_M3_WEIGHT = 0.75


class Candidate(BaseModel):
    """Kandidat alat dari katalog hasil pencocokan."""

    item_id: str = Field(..., description="ID alat pada katalog")
    nama: str = Field(..., description="Nama resmi alat")
    score: float = Field(..., description="Skor kemiripan pencocokan (0.0 sampai 1.0)")
    matched_alias: str = Field(default="", description="Alias katalog yang paling cocok")


class CatalogItem:
    """Representasi satu entitas alat di dalam katalog toko."""

    def __init__(
        self,
        item_id: str,
        nama: str,
        kategori: str,
        alias_str: str,
        butuh_ukuran: bool,
        spec_kapasitas: int | None,
        tipe: str,
        harga_per_hari: int,
    ) -> None:
        self.item_id = item_id
        self.nama = nama
        self.kategori = kategori
        self.raw_aliases = [a.strip() for a in alias_str.split("|") if a.strip()]
        self.clean_aliases = [
            normalize(a, mode="for_intent") for a in self.raw_aliases
        ]
        self.clean_nama = normalize(nama, mode="for_intent")
        self.butuh_ukuran = butuh_ukuran
        self.spec_kapasitas = spec_kapasitas
        self.tipe = tipe
        self.harga_per_hari = harga_per_hari

        # Ekstrak volume dari nama/ID jika kategori tas carrier
        self.volume_l: int | None = None
        vol_match = re.search(r"(\d{2,3})l?\b", item_id.lower())
        if vol_match and "crr" in item_id.lower():
            self.volume_l = int(vol_match.group(1))


def parse_item_text(raw_text: str) -> tuple[str, int, dict[str, Any], list[str]]:
    """Mengekstrak nama bersih, jumlah (qty), spesifikasi, dan peringatan dari teks item.

    Sesuai PRD Bagian 6.4 & 6.4a:
    - Pola 'N unit': x3, 3x, 3 buah, 3 pcs, atau angka sebelum/sesudah nama.
    - Angka setelah kap/kapasitas atau sebelum orang/org/p adalah kapasitas (spesifikasi).
    - 'tenda dome 2': ambigu (kapasitas 2 atau 2 buah). Pilih kapasitas 2, qty=1,
      dan tambah peringatan 'angka 2 dapat berarti jumlah'.
    - Ukuran (sepatu/jaket) dan volume carrier dideteksi sebagai spec.
    """
    text = raw_text.strip()
    norm = normalize(text, mode="for_intent")
    warnings: list[str] = []
    spec: dict[str, Any] = {}
    qty = 1

    # Kasus khusus PRD 6.4a: "tenda dome 2"
    if re.search(r"\btenda\s+dome\s+2\b", norm):
        spec["kapasitas"] = 2
        warnings.append("angka 2 dapat berarti jumlah")
        # Hapus "tenda dome 2" dari pencarian qty agar tidak dobel hitung
        norm = re.sub(r"\btenda\s+dome\s+2\b", "tenda dome", norm).strip()

    # 1. Ekstrak Kapasitas Tenda (contoh: 'kap 4', 'kapasitas 4', '4 orang', '4p', 'dome 4')
    kap_match = re.search(r"(?:kap(?:asitas)?\s*(\d{1,2})|(\d{1,2})\s*(?:orang|org|p\b))", norm)
    if kap_match:
        val = kap_match.group(1) or kap_match.group(2)
        spec["kapasitas"] = int(val)
        norm = re.sub(
            r"(?:kap(?:asitas)?\s*\d{1,2}|\d{1,2}\s*(?:orang|org|p\b))",
            "",
            norm,
        ).strip()
    elif "kapasitas" not in spec:
        # Cek angka setelah tenda atau dome: misal "tenda 4", "dome 6"
        tent_spec = re.search(r"\b(?:tenda|dome)\s+(\d)\b", norm)
        if tent_spec:
            spec["kapasitas"] = int(tent_spec.group(1))
            norm = re.sub(r"\b((?:tenda|dome)\s+)\d\b", r"\1", norm).strip()

    # 2. Ekstrak Volume Carrier (contoh: '60l', '60 liter', 'carrier 60')
    vol_match = re.search(r"\b(\d{2,3})\s*(?:l\b|liter)", norm)
    if vol_match:
        spec["volume_l"] = int(vol_match.group(1))
        norm = re.sub(r"\b\d{2,3}\s*(?:l\b|liter)", "", norm).strip()
    else:
        crr_vol_match = re.search(r"\b(?:carrier|keril|ransel(?:\s+gunung)?)\s+(\d{2})\b", norm)
        if crr_vol_match:
            spec["volume_l"] = int(crr_vol_match.group(1))
            norm = re.sub(
                r"\b((?:carrier|keril|ransel(?:\s+gunung)?)\s+)\d{2}\b",
                r"\1",
                norm,
            ).strip()

    # 3. Ekstrak Ukuran Sepatu / Jaket (contoh: 'ukuran 42', 'size 42', 'uk 42')
    size_match = re.search(r"\b(?:ukuran|size|uk)\s*([0-9]{2}|[smlx]+)\b", norm)
    if size_match:
        spec["ukuran"] = size_match.group(1)
        norm = re.sub(r"\b(?:ukuran|size|uk)\s*([0-9]{2}|[smlx]+)\b", "", norm).strip()

    # 4. Ekstrak Jumlah (Qty)
    # Pola: x3, 3x, 3 pcs, 3 buah, 3 unit
    explicit_qty = re.search(r"\b(?:x(\d+)|(\d+)x|(\d+)\s*(?:buah|pcs|unit|biji|pasang))\b", norm)
    if explicit_qty:
        val = explicit_qty.group(1) or explicit_qty.group(2) or explicit_qty.group(3)
        qty = int(val)
        norm = re.sub(
            r"\b(?:x\d+|\d+x|\d+\s*(?:buah|pcs|unit|biji|pasang))\b",
            "",
            norm,
        ).strip()
    else:
        # Pola angka di awal atau di akhir teks (misal: "2 matras", "matras 2")
        lead_num = re.search(r"^(\d+)\s+(.*)$", norm)
        trail_num = re.search(r"^(.*?)\s+(\d+)$", norm)
        if lead_num:
            qty = int(lead_num.group(1))
            norm = lead_num.group(2).strip()
        elif trail_num:
            # Pastikan bukan bagian dari nama model yang tidak terdeteksi
            qty = int(trail_num.group(2))
            norm = trail_num.group(1).strip()

    # Bersihkan sisa spasi
    clean_name = re.sub(r"\s+", " ", norm).strip()
    if not clean_name:
        clean_name = text.lower()

    return clean_name, max(1, qty), spec, warnings


class ItemMatcher:
    """Pencocok alat camping ke katalog toko dengan metode M1, M2, dan M3."""

    def __init__(
        self,
        catalog_path: Path | None = None,
        m3_weight: float = DEFAULT_M3_WEIGHT,
    ) -> None:
        self.catalog_path = catalog_path or CATALOG_PATH
        self.m3_weight = m3_weight
        self.catalog: list[CatalogItem] = []
        self._load_catalog()
        self._embedder = None
        self._catalog_embeddings: dict[str, np.ndarray] = {}

    def _load_catalog(self) -> None:
        """Memuat katalog alat dari berkas CSV."""
        if not self.catalog_path.is_file():
            raise FileNotFoundError(f"Berkas katalog {self.catalog_path} tidak ditemukan.")

        with open(self.catalog_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kap = int(row["spec_kapasitas"]) if row.get("spec_kapasitas") else None
                item = CatalogItem(
                    item_id=row["item_id"],
                    nama=row["nama"],
                    kategori=row["kategori"],
                    alias_str=row.get("alias", ""),
                    butuh_ukuran=row.get("butuh_ukuran", "false").lower() == "true",
                    spec_kapasitas=kap,
                    tipe=row.get("tipe", "sewa"),
                    harga_per_hari=int(row.get("harga_per_hari_contoh", 10000)),
                )
                self.catalog.append(item)

    def _get_embedder(self):
        """Memuat embedder secara lazy."""
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    def _ensure_catalog_embeddings(self) -> None:
        """Menghitung dan meng-cache embedding semua item katalog."""
        if self._catalog_embeddings:
            return

        embedder = self._get_embedder()
        for item in self.catalog:
            # Gabungkan nama resmi dan semua alias untuk representasi semantik alat
            texts = [item.nama] + item.raw_aliases
            combined_desc = " ".join(texts)
            vec = np.array(embedder.embed_text(combined_desc))
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            self._catalog_embeddings[item.item_id] = vec

    def _score_m1(
        self,
        clean_text: str,
        spec: dict[str, Any],
        item: CatalogItem,
    ) -> tuple[float, str]:
        """Menghitung skor M1 (RapidFuzz WRatio lexical matching)."""
        best_sim = 0.0
        best_alias = item.nama

        candidates_to_match = [item.clean_nama] + item.clean_aliases
        for cand in candidates_to_match:
            if clean_text == cand:
                score = 1.0
            else:
                score = fuzz.WRatio(clean_text, cand) / 100.0

            if score > best_sim:
                best_sim = score
                best_alias = cand

        # Penyesuaian spesifikasi kapasitas
        query_kap = spec.get("kapasitas")
        if query_kap is not None and item.spec_kapasitas is not None:
            if query_kap == item.spec_kapasitas:
                best_sim = min(1.0, best_sim + 0.15)
            else:
                best_sim = max(0.0, best_sim - 0.40)
        elif query_kap is not None and "tenda" in item.kategori and item.spec_kapasitas is None:
            best_sim = max(0.0, best_sim - 0.20)

        # Penyesuaian spesifikasi volume carrier
        query_vol = spec.get("volume_l")
        if query_vol is not None and item.volume_l is not None:
            if query_vol == item.volume_l:
                best_sim = min(1.0, best_sim + 0.15)
            else:
                best_sim = max(0.0, best_sim - 0.40)

        return float(best_sim), best_alias

    def _score_m2(
        self,
        clean_text: str,
        spec: dict[str, Any],
        item: CatalogItem,
    ) -> float:
        """Menghitung skor M2 (Semantic Cosine Similarity embedding)."""
        self._ensure_catalog_embeddings()
        embedder = self._get_embedder()
        q_vec = np.array(embedder.embed_text(clean_text))
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        target_vec = self._catalog_embeddings.get(item.item_id)
        if target_vec is None:
            return 0.0

        cos_sim = float(np.dot(q_vec, target_vec))
        # Skalakan cos_sim non-negatif
        sim = max(0.0, min(1.0, cos_sim))

        # Penyesuaian spesifikasi kapasitas & volume
        query_kap = spec.get("kapasitas")
        if query_kap is not None and item.spec_kapasitas is not None:
            if query_kap == item.spec_kapasitas:
                sim = min(1.0, sim + 0.1)
            else:
                sim = max(0.0, sim - 0.3)

        query_vol = spec.get("volume_l")
        if query_vol is not None and item.volume_l is not None:
            if query_vol == item.volume_l:
                sim = min(1.0, sim + 0.1)
            else:
                sim = max(0.0, sim - 0.3)

        return float(sim)

    def match(
        self,
        raw_text: str,
        top_k: int = 3,
        method: str = "m3",
    ) -> list[Candidate]:
        """Mencocokkan nama alat mentah ke katalog dan mengembalikan top-k kandidat.

        Args:
            raw_text: Teks mentah nama alat (misal: 'tenda kap 4', 'sleeping back').
            top_k: Jumlah kandidat teratas yang dikembalikan (default 3).
            method: Metode pencocokan: 'm1' (lexical), 'm2' (semantic), atau 'm3' (gabungan).

        Returns:
            list[Candidate]: Daftar kandidat terurut dari skor tertinggi.
        """
        clean_text, _, spec, _ = parse_item_text(raw_text)
        candidates: list[Candidate] = []

        for item in self.catalog:
            m1_score, alias = self._score_m1(clean_text, spec, item)

            if method == "m1":
                final_score = m1_score
            elif method == "m2":
                final_score = self._score_m2(clean_text, spec, item)
            else:
                # Default: M3 (w*M1 + (1-w)*M2)
                m2_score = self._score_m2(clean_text, spec, item)
                final_score = (self.m3_weight * m1_score) + ((1.0 - self.m3_weight) * m2_score)

            candidates.append(
                Candidate(
                    item_id=item.item_id,
                    nama=item.nama,
                    score=round(float(final_score), 4),
                    matched_alias=alias,
                )
            )

        # Urutkan berdasarkan skor menurun
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:top_k]

    def match_item(
        self,
        raw_text: str,
        method: str = "m3",
    ) -> OrderItem:
        """Mem-parsing teks dan mencocokkannya ke format OrderItem lengkap.

        Sesuai PRD Bagian 6.4:
        - Skor >= 0.85 dan margin ke kandidat ke-2 >= 0.1 -> matched
        - Skor 0.60 s/d 0.85 atau margin kecil -> ambiguous
        - Skor < 0.60 -> unmatched
        - Cek butuh_ukuran -> tambahkan ke warnings jika ukuran belum disebut.
        """
        clean_text, qty, spec, warnings = parse_item_text(raw_text)
        candidates = self.match(raw_text, top_k=3, method=method)

        if not candidates:
            return OrderItem(
                raw_text=raw_text,
                qty=qty,
                spec=spec,
                matched_item_id=None,
                matched_name=None,
                match_score=0.0,
                status=ItemStatusEnum.unmatched,
                notes=None,
            )

        top1 = candidates[0]
        top2_score = candidates[1].score if len(candidates) > 1 else 0.0
        margin = top1.score - top2_score

        # Tentukan status keputusan
        if top1.score >= 0.85 and (margin >= 0.10 or math.isclose(top1.score, 1.0)):
            status = ItemStatusEnum.matched
            matched_id = top1.item_id
            matched_name = top1.nama
        elif top1.score >= 0.60:
            status = ItemStatusEnum.ambiguous
            matched_id = top1.item_id
            matched_name = top1.nama
        else:
            status = ItemStatusEnum.unmatched
            matched_id = None
            matched_name = None

        # Periksa validasi ukuran untuk sepatu dan jaket
        catalog_map = {item.item_id: item for item in self.catalog}
        if matched_id and matched_id in catalog_map:
            cat_item = catalog_map[matched_id]
            if cat_item.butuh_ukuran and "ukuran" not in spec:
                kategori_name = "sepatu" if "spt" in cat_item.item_id.lower() else "jaket"
                warnings.append(f"ukuran {kategori_name} belum disebut")

        notes_val = "; ".join(warnings) if warnings else None

        return OrderItem(
            raw_text=raw_text,
            qty=qty,
            spec=spec,
            matched_item_id=matched_id,
            matched_name=matched_name,
            match_score=top1.score,
            status=status,
            notes=notes_val,
        )


_matcher_instance: ItemMatcher | None = None


def get_item_matcher() -> ItemMatcher:
    """Mengambil instance singleton ItemMatcher."""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = ItemMatcher()
    return _matcher_instance
