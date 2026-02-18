#!/usr/bin/env python3
"""
Daggerheart Card Extractor
==========================
Splits the Italian printable PDF (sources/carte_stampabili.pdf) into individual
card images organised by category:

  cards/
  ├── origine/            ← Origin race cards
  ├── comunità/           ← Community cards
  ├── domini/
  │   ├── arcano/         ← Arcana domain  (eye icon, muted purple badge)
  │   │   ├── classi/     ← Class feature cards (pages 1-6)
  │   │   └── abilita/    ← Ability/spell cards (pages 10-30)
  │   ├── lama/           ← Blade domain   (sword+wings, red-orange)
  │   ├── osso/           ← Bone domain    (skull, light gold)
  │   ├── codice/         ← Codex domain   (book, steel blue)
  │   ├── grazia/         ← Grace domain   (swan, hot pink)
  │   ├── mezzanotte/     ← Midnight domain(crescent, muted amber)
  │   ├── saggio/         ← Sage domain    (leaf, forest green)
  │   ├── splendore/      ← Splendor domain(sun, bright gold)
  │   └── valore/         ← Valor domain   (shield, orange)
  └── index.json          ← Full card manifest for the frontend

Usage:
  uv run python main.py
  uv run python main.py --dpi 250 --debug
"""

from __future__ import annotations

import sys

# Force UTF-8 output on Windows consoles (avoids cp1252 UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import json
import re
import shutil
import unicodedata
from math import sqrt
from pathlib import Path
from typing import Optional

import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

# ── Configuration ─────────────────────────────────────────────────────────────
PDF_PATH   = Path("sources/carte_stampabili.pdf")
OUTPUT_DIR = Path("cards")
DPI        = 200

ART_W, ART_H, ART_TOL = 201.9, 110.4, 0.12   # art-box dimensions ± 12 %

CAT_ORIGIN    = "origine"
CAT_COMMUNITY = "comunità"
CAT_DOMAIN    = "domini"

# PDF pages 1-6 (0-indexed: 0-5) contain class feature cards.
# All others are either origin/community (7-9) or ability cards (10-30).
CLASS_PAGES: frozenset[int] = frozenset(range(6))

_TIPO_WORDS: set[str] = {
    "azione", "reazione", "passivo", "abilità", "incantesimo",
    "rituale", "privilegio", "specializzazione", "maestria",
    "tratto", "caratteristica",
}

# ── Hard-coded class → domain (18 classes, 2 per domain) ─────────────────────
# Determined by badge colour analysis + Daggerheart game knowledge.
CLASS_DOMAIN: dict[str, str] = {
    # grazia (Grace) — swan badge, pink/rose
    "TROVATORE":                    "grazia",
    "ORATORE":                      "grazia",
    # saggio (Sage) — leaf badge, forest green
    "CUSTODE DEGLI ELEMENTI":       "saggio",
    "CUSTODE DEL RINNOVAMENTO":     "saggio",
    # valore (Valor) — shield badge, orange
    "VALOROSO":                     "valore",
    "VENDICATORE":                  "valore",
    # osso (Bone) — skull badge, olive/earth
    "FERALE":                       "osso",
    "APRIPISTA":                    "osso",
    # mezzanotte (Midnight) — crescent badge, dark
    "OMBRA NOTTURNA":               "mezzanotte",
    "LADRO":                        "mezzanotte",
    # splendore (Splendor) — sun badge, bright gold
    "EMISSARIO DIVINO":             "splendore",
    "SENTINELLA ALATA":             "splendore",
    # arcano (Arcana) — eye badge, muted purple
    "POTERE ELEMENTALE":            "arcano",
    "POTERE PRIMORDIALE":           "arcano",
    # lama (Blade) — sword badge, red-orange
    "CHIAMATA DEL CORAGGIO":        "lama",
    "CHIAMATA DELLO STERMINATORE":  "lama",
    # codice (Codex) — book badge, steel blue
    "SCUOLA DELLA CONOSCENZA":      "codice",
    "SCUOLA DELLA GUERRA":          "codice",
}

# ── Reference badge colours for ability card domain detection ─────────────────
# Empirically sampled from the top-left badge region of known-domain ability cards.
DOMAIN_REF_COLORS: dict[str, tuple[int, int, int]] = {
    "arcano":     (141,  94, 133),   # muted purple-rose  – pages 10-12
    "lama":       (172,  67,  47),   # red-orange         – pages 13-14
    "osso":       (231, 211, 139),   # light muted gold   – pages 15-16 (PADRONANZA DELLE OSSA)
    "codice":     ( 61, 100, 137),   # steel blue         – pages 17-19
    "grazia":     (199,  83, 127),   # hot pink           – pages 20-21
    "mezzanotte": (195, 176, 103),   # darker muted amber – pages 22-23 (PADRONANZA DELLA MEZZANOTTE)
    "saggio":     ( 41, 120,  61),   # forest green       – pages 24-26
    "splendore":  (219, 188,  19),   # bright gold        – pages 27-28
    "valore":     (207, 120,  27),   # orange             – pages 29-30
}

DOMAINS_ALL = list(DOMAIN_REF_COLORS.keys())


# ── Colour → domain ───────────────────────────────────────────────────────────

def _dominant_saturated_color(
    img_rgb: np.ndarray,
    x_frac: tuple[float, float] = (0.0, 0.25),
    y_frac: tuple[float, float] = (0.0, 0.25),
) -> tuple[int, int, int]:
    """Mean RGB of non-white, non-black, saturated pixels in a fractional sub-region."""
    h, w = img_rgb.shape[:2]
    x0, x1 = int(x_frac[0] * w), max(int(x_frac[1] * w), 1)
    y0, y1 = int(y_frac[0] * h), max(int(y_frac[1] * h), 1)
    region = img_rgb[y0:y1, x0:x1].astype(np.float32)
    if region.size == 0:
        return (128, 128, 128)

    r, g, b = region[:, :, 0], region[:, :, 1], region[:, :, 2]
    not_white = ~((r > 210) & (g > 210) & (b > 210))
    not_black = ~((r < 30)  & (g < 30)  & (b < 30))
    saturated  = (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)) > 20
    mask = not_white & not_black & saturated
    if mask.sum() < 8:
        mask = not_white & not_black
    if mask.sum() == 0:
        return (128, 128, 128)
    return (int(r[mask].mean()), int(g[mask].mean()), int(b[mask].mean()))


def rgb_to_domain(r: int, g: int, b: int) -> str:
    """Nearest-neighbour match against reference badge colours → Italian domain name."""
    best_domain, best_dist = "sconosciuto", float("inf")
    for domain, (dr, dg, db) in DOMAIN_REF_COLORS.items():
        dist = sqrt((r - dr) ** 2 + (g - dg) ** 2 + (b - db) ** 2)
        if dist < best_dist:
            best_dist, best_domain = dist, domain
    return best_domain


# ── PDF rendering ─────────────────────────────────────────────────────────────

def render_page(page: fitz.Page, dpi: int = DPI) -> np.ndarray:
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    return arr.copy()


# ── Grid detection ────────────────────────────────────────────────────────────

def _art_boxes(page: fitz.Page) -> list[fitz.Rect]:
    boxes: list[fitz.Rect] = []
    for d in page.get_drawings():
        r = d.get("rect")
        if r is None:
            continue
        rect = fitz.Rect(r)
        if (rect.width > 0 and rect.height > 0
                and abs(rect.width  - ART_W) / ART_W < ART_TOL
                and abs(rect.height - ART_H) / ART_H < ART_TOL):
            boxes.append(rect)
    return boxes


def _cluster(values: list[float], gap: float = 8.0) -> list[float]:
    if not values:
        return []
    vals = sorted(values)
    groups: list[list[float]] = [[vals[0]]]
    for v in vals[1:]:
        if v - groups[-1][-1] < gap:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [sum(g) / len(g) for g in groups]


GridParams = tuple[list[float], float, float, float, int]


def _params_from_art_boxes(page: fitz.Page) -> Optional[GridParams]:
    boxes = _art_boxes(page)
    if not boxes:
        return None
    x0s = _cluster([b.x0 for b in boxes])
    y0s = _cluster([b.y0 for b in boxes])
    n_cols, n_rows = len(x0s), len(y0s)
    if n_cols < 1 or n_rows < 1:
        return None
    col_span = ((x0s[-1] - x0s[0]) / (n_cols - 1)) if n_cols > 1 else (page.rect.width - 2 * x0s[0])
    row_span = ((y0s[-1] - y0s[0]) / (n_rows - 1)) if n_rows > 1 else (page.rect.height / n_rows)
    top_margin = max((page.rect.height - n_rows * row_span) / 2, 0.0)
    return (x0s, col_span, row_span, top_margin, n_rows)


def _build_grid(page: fitz.Page, params: GridParams) -> list[fitz.Rect]:
    x0s, col_span, row_span, top_margin, n_rows = params
    page_w, page_h = page.rect.width, page.rect.height
    INSET = 2.0
    rects: list[fitz.Rect] = []
    for ri in range(n_rows):
        for x0 in x0s:
            cx0 = x0 + INSET
            cy0 = top_margin + ri * row_span + INSET
            cx1 = min(page_w - 1, x0 + col_span - INSET)
            cy1 = min(page_h - 1, cy0 + row_span - 2 * INSET)
            rects.append(fitz.Rect(cx0, cy0, cx1, cy1))
    return sorted(rects, key=lambda r: (round(r.y0, -1), round(r.x0, -1)))


def _scan_reference_params(doc: fitz.Document) -> Optional[GridParams]:
    for page_num in range(len(doc)):
        params = _params_from_art_boxes(doc[page_num])
        if params and len(params[0]) == 3 and params[4] == 3:
            return params
    return None


def find_card_grid(
    page: fitz.Page, page_img: np.ndarray, ref: Optional[GridParams],
) -> tuple[list[fitz.Rect], str]:
    params = _params_from_art_boxes(page)
    if params:
        return _build_grid(page, params), "art-boxes"
    if ref is not None:
        return _build_grid(page, ref), "reference-grid"
    grid = _grid_from_image(page_img, page)
    return (grid, "image-contours") if grid else ([], "none")


def _grid_from_image(page_img: np.ndarray, page: fitz.Page) -> list[fitz.Rect]:
    pr = page.rect
    ph, pw = page_img.shape[:2]
    sx, sy = pr.width / pw, pr.height / ph
    gray = cv2.cvtColor(page_img, cv2.COLOR_RGB2GRAY)
    _, thr = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY_INV)
    kern = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kern)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_a, max_a = pw * ph * 0.04, pw * ph * 0.45
    rects: list[fitz.Rect] = []
    for c in contours:
        a = cv2.contourArea(c)
        if not (min_a < a < max_a):
            continue
        x, y, w, h = cv2.boundingRect(c)
        if not (0.35 < w / max(h, 1) < 1.1):
            continue
        rects.append(fitz.Rect(x * sx, y * sy, (x + w) * sx, (y + h) * sy))
    if len(rects) < 2:
        return []
    areas = [r.width * r.height for r in rects]
    med   = sorted(areas)[len(areas) // 2]
    rects = [r for r, a in zip(rects, areas) if abs(a - med) / med < 0.30]
    return sorted(rects, key=lambda r: (round(r.y0, -1), round(r.x0, -1)))


# ── Card image cropping ───────────────────────────────────────────────────────

def crop_card(page_img: np.ndarray, page: fitz.Page, rect: fitz.Rect) -> np.ndarray:
    pr = page.rect
    ph, pw = page_img.shape[:2]
    sx, sy = pw / pr.width, ph / pr.height
    x0 = max(0, int(rect.x0 * sx));  y0 = max(0, int(rect.y0 * sy))
    x1 = min(pw, int(rect.x1 * sx)); y1 = min(ph, int(rect.y1 * sy))
    return page_img[y0:y1, x0:x1]


def is_blank(img: np.ndarray, threshold: float = 0.97) -> bool:
    if img.size == 0 or min(img.shape[:2]) < 30:
        return True
    return bool(img.mean() / 255.0 > threshold)


# ── Text extraction & classification ──────────────────────────────────────────

def extract_spans(page: fitz.Page, rect: fitz.Rect) -> list[dict]:
    spans: list[dict] = []
    data = page.get_text("dict", clip=rect, flags=fitz.TEXT_PRESERVE_WHITESPACE)
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for sp in line.get("spans", []):
                text = re.sub(r"\s+", " ", sp.get("text", "")).strip()
                if not text:
                    continue
                flags = sp.get("flags", 0)
                bbox  = sp.get("bbox", [rect.x0, rect.y0, 0, 0])
                spans.append({
                    "text":   text,
                    "size":   round(sp.get("size", 0), 2),
                    "bold":   bool(flags & 16),
                    "italic": bool(flags & 1),
                    "x":      round(bbox[0] - rect.x0, 1),
                    "y":      round(bbox[1] - rect.y0, 1),
                })
    spans.sort(key=lambda s: (round(s["y"] / 4) * 4, s["x"]))
    return spans


_COST_RE   = re.compile(r"^\d{1,3}\+?$")
_COPY_RE   = re.compile(r"DH\s+MB|©|daggerheart", re.I)
_ICON_RE   = re.compile(r"^[•·\-–—|/\\<>▵▴◆★☆♦]{1,3}$")
_SPACED_RE = re.compile(r"^([A-ZÀÈÙÌÉÁÓ]{1,2} ){2,}[A-ZÀÈÙÌÉÁÓ]{1,2}\s*$")
_CAPS_RE   = re.compile(r"^[A-ZÀÈÙÌÉÁÓ][A-ZÀÈÙÌÉÁÓ\s'\-À-Ö0-9]{2,}$")


def _is_noise(text: str) -> bool:
    if len(text) <= 2:                return True
    if _COST_RE.match(text):          return True
    if _COPY_RE.search(text):         return True
    if _ICON_RE.match(text):          return True
    if _SPACED_RE.match(text):        return True
    return False


def _find_card_name(spans: list[dict]) -> str:
    # Pass 1: ALL-CAPS name (spell/ability cards: SIGILLO RUNICO, etc.)
    for s in spans:
        t = s["text"]
        if not _is_noise(t) and _CAPS_RE.match(t) and t.lower() not in _TIPO_WORDS:
            return t
    # Pass 2: first non-noise span (origin cards: Clank, Drakona, etc.)
    for s in spans:
        t = s["text"]
        if not _is_noise(t) and t.lower() not in _TIPO_WORDS:
            return t
    return "sconosciuta"


def classify_card(spans: list[dict]) -> str:
    compact = re.sub(r"\s+", "", " ".join(s["text"] for s in spans)).upper()
    if "ORIGINE" in compact:
        return CAT_ORIGIN
    if "COMUNITÀ" in compact or "COMUNITA" in compact:
        return CAT_COMMUNITY
    return "domain"


def build_metadata(
    spans:          list[dict],
    categoria:      str,
    dominio:        Optional[str],
    pagina:         int,
    idx_carta:      int,
    sottocategoria: Optional[str] = None,
) -> dict:
    meta: dict = {
        "categoria":    categoria,
        "dominio":      dominio,
        "pagina":       pagina,
        "indice_carta": idx_carta,
    }
    if sottocategoria:
        meta["sottocategoria"] = sottocategoria

    if not spans:
        meta["nome"] = "sconosciuta"
        return meta

    max_size     = max(s["size"] for s in spans)
    meta["nome"] = _find_card_name(spans)
    meta["testo"] = [s["text"] for s in spans]
    all_text      = " ".join(s["text"] for s in spans)

    m = re.search(r"DH\s+\w+\s+(\d+)\s*/\s*270", all_text)
    if m:
        meta["id_carta"] = f"{m.group(1)}/270"

    cost_spans = [s for s in spans
                  if _COST_RE.match(s["text"]) and s["size"] >= max_size * 0.45]
    if cost_spans:
        nums = [s["text"] for s in sorted(cost_spans, key=lambda s: s["x"])]
        if len(nums) >= 2:
            meta["soglia"], meta["livello"] = nums[0], nums[1]
        elif nums:
            meta["costo"] = nums[0]

    for kw in _TIPO_WORDS:
        if re.search(rf"\b{kw}\b", all_text, re.I):
            meta["tipo_carta"] = kw
            break

    abilities = re.findall(r"\b([A-ZÀÈÙÌÉÁÓ][a-zàèùìéáó][^\n:]{2,40}):", all_text)
    if abilities:
        meta["nome_abilita"] = [a.strip() for a in abilities[:6]]

    flavour = [s["text"] for s in spans
               if s.get("italic") and s["size"] < max_size * 0.85 and len(s["text"]) > 8]
    if flavour:
        meta["testo_sapore"] = " ".join(flavour)

    return meta


# ── Filename helper ───────────────────────────────────────────────────────────

def safe_filename(text: str, maxlen: int = 60) -> str:
    nfkd    = unicodedata.normalize("NFKD", text)
    ascii_  = nfkd.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^\w\s\-]", "", ascii_)
    slug    = re.sub(r"\s+", "_", cleaned).strip("_").lower()
    return slug[:maxlen] if slug else "carta"


# ── Main extraction loop ──────────────────────────────────────────────────────

def process_pdf(
    pdf_path:   Path = PDF_PATH,
    output_dir: Path = OUTPUT_DIR,
    dpi:        int  = DPI,
    debug:      bool = False,
) -> None:
    doc     = fitz.open(pdf_path)
    n_pages = len(doc)
    print(f"PDF: {pdf_path}  ({n_pages} pages, {dpi} DPI)")
    print(f"Output -> {output_dir}/\n")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    ref_params = _scan_reference_params(doc)
    if ref_params:
        rx0s, rcol, rrow, rtop, _ = ref_params
        print(f"Reference grid: x0s={[round(x,1) for x in rx0s]}, "
              f"col={rcol:.1f}, row={rrow:.1f}, top={rtop:.1f}\n")

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / CAT_ORIGIN).mkdir()
    (output_dir / CAT_COMMUNITY).mkdir()
    (output_dir / CAT_DOMAIN).mkdir()

    origin_count    = 0
    community_count = 0
    class_counts:   dict[str, int] = {}
    ability_counts: dict[str, int] = {}
    index: list[dict] = []
    total = 0

    for page_num in range(n_pages):
        page         = doc[page_num]
        page_img     = render_page(page, dpi)
        is_class_pg  = page_num in CLASS_PAGES

        grid, method = find_card_grid(page, page_img, ref_params)
        if not grid:
            print(f"[p{page_num+1:02d}] WARNING: no grid detected — skipping")
            continue

        kind = "classi" if is_class_pg else "abilita"
        print(f"[p{page_num+1:02d}] {len(grid)} cards  ({kind}, {method})")

        if debug:
            _save_debug_page(page_img, page, grid, output_dir, page_num)

        for cell_idx, card_rect in enumerate(grid):
            card_img = crop_card(page_img, page, card_rect)
            if is_blank(card_img):
                continue

            spans = extract_spans(page, card_rect)
            cat   = classify_card(spans)

            # ── Determine destination ────────────────────────────────────────
            if cat == "domain":
                if is_class_pg:
                    # Hard-coded lookup: class name → domain
                    nome    = _find_card_name(spans)
                    dominio = CLASS_DOMAIN.get(nome.upper())
                    if dominio is None:
                        # fuzzy: look for any key that is a substring of nome
                        for key, val in CLASS_DOMAIN.items():
                            if key in nome.upper():
                                dominio = val
                                break
                    dominio = dominio or "sconosciuto"
                    subcat  = "classi"
                    class_counts.setdefault(dominio, 0)
                    class_counts[dominio] += 1
                    seq = class_counts[dominio]
                else:
                    rgb     = _dominant_saturated_color(card_img)
                    dominio = rgb_to_domain(*rgb)
                    subcat  = "abilita"
                    ability_counts.setdefault(dominio, 0)
                    ability_counts[dominio] += 1
                    seq = ability_counts[dominio]

                card_dir = output_dir / CAT_DOMAIN / dominio / subcat
                card_dir.mkdir(parents=True, exist_ok=True)
                meta  = build_metadata(spans, "dominio", dominio,
                                       page_num + 1, cell_idx + 1, subcat)
                label = f"domini/{dominio}/{subcat}"

            elif cat == CAT_ORIGIN:
                origin_count += 1
                seq      = origin_count
                dominio  = None
                subcat   = None
                meta     = build_metadata(spans, CAT_ORIGIN, None,
                                          page_num + 1, cell_idx + 1)
                card_dir = output_dir / CAT_ORIGIN
                label    = CAT_ORIGIN

            else:  # CAT_COMMUNITY
                community_count += 1
                seq      = community_count
                dominio  = None
                subcat   = None
                meta     = build_metadata(spans, CAT_COMMUNITY, None,
                                          page_num + 1, cell_idx + 1)
                card_dir = output_dir / CAT_COMMUNITY
                label    = CAT_COMMUNITY

            # ── Save PNG + JSON ──────────────────────────────────────────────
            base      = f"{safe_filename(meta.get('nome', 'carta'))}_{seq:03d}"
            png_path  = card_dir / f"{base}.png"
            json_path = card_dir / f"{base}.json"

            Image.fromarray(card_img).save(png_path, "PNG", dpi=(dpi, dpi))

            rel_png  = str(png_path.relative_to(output_dir)).replace("\\", "/")
            rel_json = str(json_path.relative_to(output_dir)).replace("\\", "/")
            meta["img_path"]  = rel_png
            meta["json_path"] = rel_json

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            # Index entry (compact — for the frontend manifest)
            index.append({
                "id":              meta.get("id_carta", f"p{page_num+1}c{cell_idx+1}"),
                "nome":            meta.get("nome", "?"),
                "categoria":       meta["categoria"],
                "dominio":         dominio,
                "sottocategoria":  subcat,
                "tipo_carta":      meta.get("tipo_carta"),
                "livello":         _to_int(meta.get("livello")),
                "soglia":          _to_int(meta.get("soglia")),
                "pagina":          page_num + 1,
                "img":             rel_png,
                "json":            rel_json,
            })

            total += 1
            print(f"  [{label}] {meta.get('nome','?')[:42]!r}")

    # ── Write full index ─────────────────────────────────────────────────────
    idx_path = output_dir / "index.json"
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"\nIndex -> {idx_path}  ({len(index)} entries)")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"Total: {total} cards")
    print(f"  {CAT_ORIGIN}:     {origin_count}")
    print(f"  {CAT_COMMUNITY}:  {community_count}")
    print(f"  classi per dominio:")
    for d in DOMAINS_ALL:
        n = class_counts.get(d, 0)
        if n: print(f"    {d:<22} {n}")
    print(f"  abilita per dominio:")
    for d in DOMAINS_ALL:
        n = ability_counts.get(d, 0)
        if n: print(f"    {d:<22} {n}")

    doc.close()


def _to_int(val) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


# ── Debug helper ──────────────────────────────────────────────────────────────

def _save_debug_page(page_img, page, grid, out_dir, page_num):
    pr = page.rect
    ph, pw = page_img.shape[:2]
    sx, sy = pw / pr.width, ph / pr.height
    dbg = page_img.copy()
    for idx, rect in enumerate(grid):
        x0, y0 = int(rect.x0 * sx), int(rect.y0 * sy)
        x1, y1 = int(rect.x1 * sx), int(rect.y1 * sy)
        cv2.rectangle(dbg, (x0, y0), (x1, y1), (255, 0, 0), 4)
        cv2.putText(dbg, str(idx + 1), (x0 + 10, y0 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)
    debug_dir = out_dir / "_debug"
    debug_dir.mkdir(exist_ok=True)
    Image.fromarray(dbg).save(debug_dir / f"page_{page_num + 1:03d}.png")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description="Extract Daggerheart cards from the Italian printable PDF.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--pdf",    type=Path, default=PDF_PATH)
    p.add_argument("--output", type=Path, default=OUTPUT_DIR)
    p.add_argument("--dpi",    type=int,  default=DPI)
    p.add_argument("--debug",  action="store_true")
    args = p.parse_args()
    process_pdf(pdf_path=args.pdf, output_dir=args.output, dpi=args.dpi, debug=args.debug)


if __name__ == "__main__":
    main()
