#!/usr/bin/env python3
"""
Daggerheart Card Extractor
==========================
Splits the Italian printable PDF (sources/carte_stampabili.pdf) into individual
card images organised by category:

  cards/
  ├── origine/          ← Origin cards    (text contains "ORIGINE")
  ├── comunità/         ← Community cards (text contains "COMUNITÀ")
  └── domini/
      ├── lama/         ← Blade domain    (red badge)
      ├── osso/         ← Bone domain     (purple/grey badge)
      ├── codice/       ← Codex domain    (blue badge)
      ├── fungale/      ← Fungal domain   (green badge)
      ├── grazia/       ← Grace domain    (pink/gold badge)
      ├── mezzanotte/   ← Midnight domain (dark badge)
      ├── saggio/       ← Sage domain     (teal badge)
      └── splendore/    ← Splendor domain (gold badge)
      (unknown colours → folder named after the RGB hex value)

Each card is saved as:
  <card_name>_<seq>.png   – raw card image cropped from the PDF page
  <card_name>_<seq>.json  – structured metadata extracted from card text

Usage (via uv):
  uv run python main.py
  uv run python main.py --pdf sources/carte_stampabili.pdf --output cards --dpi 200
  uv run python main.py --debug     # saves annotated page previews in cards/_debug/
"""

from __future__ import annotations

import sys

# Force UTF-8 output on Windows consoles (avoids cp1252 UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import colorsys
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Optional

import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

# ── Default configuration ─────────────────────────────────────────────────────
PDF_PATH   = Path("sources/carte_stampabili.pdf")
OUTPUT_DIR = Path("cards")
DPI        = 200          # render DPI (increase for higher-quality output)

# Art-box dimensions in PDF points (201.9 × 110.4 pts, tolerance ±12%)
ART_W, ART_H, ART_TOL = 201.9, 110.4, 0.12

# Category folder names (Italian)
CAT_ORIGIN    = "origine"
CAT_COMMUNITY = "comunità"
CAT_DOMAIN    = "domini"

# Words that denote card sub-type (excluded from card name detection)
_TIPO_WORDS: set[str] = {
    "azione", "reazione", "passivo", "abilità", "incantesimo",
    "rituale", "privilegio", "specializzazione", "maestria",
    "tratto", "caratteristica",
}


# ── Colour → domain name ──────────────────────────────────────────────────────

def _dominant_saturated_color(
    img_rgb: np.ndarray,
    x_frac: tuple[float, float] = (0.0, 0.25),
    y_frac: tuple[float, float] = (0.0, 0.25),
) -> tuple[int, int, int]:
    """
    Return the mean RGB of pixels in the fractional sub-region that are
    neither near-white nor near-black and have meaningful colour saturation.
    """
    h, w = img_rgb.shape[:2]
    x0, x1 = int(x_frac[0] * w), max(int(x_frac[1] * w), 1)
    y0, y1 = int(y_frac[0] * h), max(int(y_frac[1] * h), 1)
    region = img_rgb[y0:y1, x0:x1].astype(np.float32)

    if region.size == 0:
        return (128, 128, 128)

    r, g, b = region[:, :, 0], region[:, :, 1], region[:, :, 2]
    not_white = ~((r > 215) & (g > 215) & (b > 215))
    not_black = ~((r < 40)  & (g < 40)  & (b < 40))
    saturated  = (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)) > 30

    mask = not_white & not_black & saturated
    if mask.sum() < 8:
        mask = not_white & not_black
    if mask.sum() == 0:
        return (128, 128, 128)

    return (int(r[mask].mean()), int(g[mask].mean()), int(b[mask].mean()))


def rgb_to_domain(r: int, g: int, b: int) -> str:
    """Map a dominant badge colour to an Italian domain folder name."""
    if (r + g + b) / 3 < 55:
        return "mezzanotte"

    hv, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    hue = hv * 360

    if s < 0.18:
        return "osso" if v < 0.65 else "mezzanotte"

    if hue < 22 or hue >= 345:  return "lama"
    if hue < 80:                 return "splendore"
    if hue < 155:                return "fungale"
    if hue < 195:                return "saggio"
    if hue < 258:                return "codice"
    if hue < 312:                return "osso"
    return "grazia"


# ── PDF rendering ─────────────────────────────────────────────────────────────

def render_page(page: fitz.Page, dpi: int = DPI) -> np.ndarray:
    """Render a PDF page to an (H, W, 3) uint8 RGB numpy array."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    return arr.copy()


# ── Grid detection ────────────────────────────────────────────────────────────

def _art_boxes(page: fitz.Page) -> list[fitz.Rect]:
    """Return all drawing rectangles that match the art-box dimensions."""
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
    """Collapse nearby float values into their group mean."""
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


# GridParams: (x0s, col_span, row_span, top_margin, n_rows)
GridParams = tuple[list[float], float, float, float, int]


def _params_from_art_boxes(page: fitz.Page) -> Optional[GridParams]:
    """Derive grid parameters from art-box positions on a page."""
    boxes = _art_boxes(page)
    if not boxes:
        return None

    x0s = _cluster([b.x0 for b in boxes])
    y0s = _cluster([b.y0 for b in boxes])
    n_cols = len(x0s)
    n_rows = len(y0s)

    if n_cols < 1 or n_rows < 1:
        return None

    col_span = ((x0s[-1] - x0s[0]) / (n_cols - 1)) if n_cols > 1 else (page.rect.width - 2 * x0s[0])
    row_span = ((y0s[-1] - y0s[0]) / (n_rows - 1)) if n_rows > 1 else (page.rect.height / n_rows)
    top_margin = max((page.rect.height - n_rows * row_span) / 2, 0.0)

    return (x0s, col_span, row_span, top_margin, n_rows)


def _build_grid(page: fitz.Page, params: GridParams) -> list[fitz.Rect]:
    """Build a card grid from precomputed grid parameters."""
    x0s, col_span, row_span, top_margin, n_rows = params
    page_w = page.rect.width
    page_h = page.rect.height
    INSET  = 2.0   # shrink each cell slightly to avoid pixel bleed from adjacent cards

    rects: list[fitz.Rect] = []
    for ri in range(n_rows):
        for x0 in x0s:
            cx0 = x0 + INSET
            cy0 = top_margin + ri * row_span + INSET
            cx1 = min(page_w - 1, x0  + col_span - INSET)
            cy1 = min(page_h - 1, cy0 + row_span - 2 * INSET)
            rects.append(fitz.Rect(cx0, cy0, cx1, cy1))

    return sorted(rects, key=lambda r: (round(r.y0, -1), round(r.x0, -1)))


def _scan_reference_params(doc: fitz.Document) -> Optional[GridParams]:
    """
    Pre-scan the PDF to find the most reliable grid parameters.

    We pick the page whose art-box layout yields the most complete grid
    (n_cols==3, n_rows==3).  This reference is later used for pages that
    have no art boxes (origin/community pages).
    """
    best: Optional[GridParams] = None
    for page_num in range(len(doc)):
        params = _params_from_art_boxes(doc[page_num])
        if params is None:
            continue
        x0s, col_span, row_span, top_margin, n_rows = params
        n_cols = len(x0s)
        if n_cols == 3 and n_rows == 3:
            best = params
            break          # first clean 3×3 is good enough
    return best


def find_card_grid(
    page:      fitz.Page,
    page_img:  np.ndarray,
    ref:       Optional[GridParams],
) -> tuple[list[fitz.Rect], str]:
    """
    Return (card_rects, method_name) for `page`.

    Priority:
      1. Art-box detection  — works for domain/class/spell pages
      2. Reference-grid     — fallback for origin/community pages (no art boxes)
      3. Image contours     — last resort
    """
    # 1. Art-box grid
    params = _params_from_art_boxes(page)
    if params:
        return _build_grid(page, params), "art-boxes"

    # 2. Reference-grid (from a page that does have art boxes)
    if ref is not None:
        return _build_grid(page, ref), "reference-grid"

    # 3. Image-based contour detection
    grid = _grid_from_image(page_img, page)
    if grid:
        return grid, "image-contours"

    return [], "none"


def _grid_from_image(page_img: np.ndarray, page: fitz.Page) -> list[fitz.Rect]:
    """Last-resort grid detection via image contour analysis."""
    pr      = page.rect
    ph, pw  = page_img.shape[:2]
    sx, sy  = pr.width / pw, pr.height / ph

    gray    = cv2.cvtColor(page_img, cv2.COLOR_RGB2GRAY)
    _, thr  = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY_INV)
    kern    = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed  = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kern)
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
    areas  = [r.width * r.height for r in rects]
    med    = sorted(areas)[len(areas) // 2]
    rects  = [r for r, a in zip(rects, areas) if abs(a - med) / med < 0.30]
    return sorted(rects, key=lambda r: (round(r.y0, -1), round(r.x0, -1)))


# ── Card image cropping ───────────────────────────────────────────────────────

def crop_card(page_img: np.ndarray, page: fitz.Page, rect: fitz.Rect) -> np.ndarray:
    pr      = page.rect
    ph, pw  = page_img.shape[:2]
    sx, sy  = pw / pr.width, ph / pr.height

    x0 = max(0, int(rect.x0 * sx))
    y0 = max(0, int(rect.y0 * sy))
    x1 = min(pw, int(rect.x1 * sx))
    y1 = min(ph, int(rect.y1 * sy))
    return page_img[y0:y1, x0:x1]


def is_blank(img: np.ndarray, threshold: float = 0.97) -> bool:
    if img.size == 0 or min(img.shape[:2]) < 30:
        return True
    return bool(img.mean() / 255.0 > threshold)


# ── Text extraction & classification ──────────────────────────────────────────

def extract_spans(page: fitz.Page, rect: fitz.Rect) -> list[dict]:
    """Return all text spans inside `rect`, sorted top-to-bottom then left-to-right."""
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
_SPACED_RE = re.compile(r"^([A-ZÀÈÙÌÉÁÓ]{1,2} ){2,}[A-ZÀÈÙÌÉÁÓ]{1,2}\s*$")  # "O R I G I N E" / "C O M U N I TÀ"
_CAPS_RE   = re.compile(r"^[A-ZÀÈÙÌÉÁÓ][A-ZÀÈÙÌÉÁÓ\s'\-À-Ö0-9]{2,}$")  # ALL-CAPS card name


def _is_noise(text: str) -> bool:
    """Return True for text that can never be a card name."""
    if len(text) <= 2:
        return True
    if _COST_RE.match(text):
        return True
    if _COPY_RE.search(text):
        return True
    if _ICON_RE.match(text):
        return True
    if _SPACED_RE.match(text):    # "O R I G I N E" / "C O M U N I T À"
        return True
    return False


def _find_card_name(spans: list[dict]) -> str:
    """
    Find the most likely card name from spans using a two-pass strategy:

    Pass 1 – prefer ALL-CAPS names (e.g. "SIGILLO RUNICO", "TROVATORE",
             "PRIVILEGIATA").  These are unambiguous card-name markers in
             Daggerheart and can be distinguished from the lowercase card-type
             labels ("incantesimo", "abilità").

    Pass 2 – fall back to the first non-noise span in reading order (handles
             mixed-case origin names like "Clank", "Drakona").
    """
    # Pass 1: ALL-CAPS name (not a tipo keyword, not noise, not copyright)
    for s in spans:
        t = s["text"]
        if (not _is_noise(t)
                and _CAPS_RE.match(t)
                and t.lower() not in _TIPO_WORDS):
            return t

    # Pass 2: any non-noise span
    for s in spans:
        t = s["text"]
        if not _is_noise(t) and t.lower() not in _TIPO_WORDS:
            return t

    return "sconosciuta"


def classify_card(spans: list[dict]) -> str:
    """Return CAT_ORIGIN, CAT_COMMUNITY, or 'domain'."""
    compact = re.sub(r"\s+", "", " ".join(s["text"] for s in spans)).upper()
    if "ORIGINE" in compact:
        return CAT_ORIGIN
    if "COMUNITÀ" in compact or "COMUNITA" in compact:
        return CAT_COMMUNITY
    return "domain"


def build_metadata(
    spans:     list[dict],
    categoria: str,
    dominio:   Optional[str],
    pagina:    int,
    idx_carta: int,
) -> dict:
    """Build structured metadata from text spans."""
    meta: dict = {
        "categoria":    categoria,
        "dominio":      dominio,
        "pagina":       pagina,
        "indice_carta": idx_carta,
    }

    if not spans:
        meta["nome"] = "sconosciuta"
        return meta

    max_size = max(s["size"] for s in spans)
    meta["nome"] = _find_card_name(spans)

    # ── All ordered text for reference ────────────────────────────────────────
    meta["testo"] = [s["text"] for s in spans]
    all_text = " ".join(s["text"] for s in spans)

    # ── Card ID ───────────────────────────────────────────────────────────────
    m = re.search(r"DH\s+\w+\s+(\d+)\s*/\s*270", all_text)
    if m:
        meta["id_carta"] = f"{m.group(1)}/270"

    # ── Cost / threshold (large numbers on ability/spell cards) ───────────────
    cost_spans = [s for s in spans
                  if _COST_RE.match(s["text"]) and s["size"] >= max_size * 0.45]
    if cost_spans:
        nums = [s["text"] for s in sorted(cost_spans, key=lambda s: s["x"])]
        if len(nums) >= 2:
            meta["soglia"], meta["livello"] = nums[0], nums[1]
        elif nums:
            meta["costo"] = nums[0]

    # ── Card sub-type ─────────────────────────────────────────────────────────
    for kw in _TIPO_WORDS:
        if re.search(rf"\b{kw}\b", all_text, re.I):
            meta["tipo_carta"] = kw
            break

    # ── Ability names on class cards ("Name:" pattern) ────────────────────────
    abilities = re.findall(
        r"\b([A-ZÀÈÙÌÉÁÓ][a-zàèùìéáó][^\n:]{2,40}):",
        all_text,
    )
    if abilities:
        meta["nome_abilita"] = [a.strip() for a in abilities[:6]]

    # ── Flavour text (italic, smaller font) ───────────────────────────────────
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


# ── Main extraction loop ───────────────────────────────────────────────────────

def process_pdf(
    pdf_path:   Path = PDF_PATH,
    output_dir: Path = OUTPUT_DIR,
    dpi:        int  = DPI,
    debug:      bool = False,
) -> None:
    doc     = fitz.open(pdf_path)
    n_pages = len(doc)
    print(f"PDF: {pdf_path}  ({n_pages} pages, {dpi} DPI output)")
    print(f"Output -> {output_dir}/")

    # Always start fresh: remove any previous extraction
    if output_dir.exists():
        shutil.rmtree(output_dir)
        print(f"Removed previous output directory.\n")

    # Pre-scan: find reference grid from the first clean 3×3 art-box page
    ref_params = _scan_reference_params(doc)
    if ref_params:
        rx0s, rcol, rrow, rtop, rn = ref_params
        print(f"Reference grid: x0s={[round(x,1) for x in rx0s]}, "
              f"col_span={rcol:.1f}, row_span={rrow:.1f}, top_margin={rtop:.1f}\n")

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / CAT_ORIGIN).mkdir(exist_ok=True)
    (output_dir / CAT_COMMUNITY).mkdir(exist_ok=True)
    (output_dir / CAT_DOMAIN).mkdir(exist_ok=True)

    counters: dict[str, int]      = {CAT_ORIGIN: 0, CAT_COMMUNITY: 0}
    domain_counters: dict[str, int] = {}
    total = 0

    for page_num in range(n_pages):
        page     = doc[page_num]
        page_img = render_page(page, dpi)

        grid, method = find_card_grid(page, page_img, ref_params)
        if not grid:
            print(f"[page {page_num + 1:02d}] WARNING: no card grid detected — skipping")
            continue

        print(f"[page {page_num + 1:02d}] {len(grid)} cards  (method: {method})")

        if debug:
            _save_debug_page(page_img, page, grid, output_dir, page_num)

        for cell_idx, card_rect in enumerate(grid):
            card_img = crop_card(page_img, page, card_rect)

            if is_blank(card_img):
                continue

            spans = extract_spans(page, card_rect)
            cat   = classify_card(spans)

            # ── Domain card ─────────────────────────────────────────────────
            if cat == "domain":
                rgb     = _dominant_saturated_color(card_img)
                dominio = rgb_to_domain(*rgb)
                domain_counters.setdefault(dominio, 0)
                domain_counters[dominio] += 1
                seq      = domain_counters[dominio]
                meta     = build_metadata(spans, "dominio", dominio,
                                          page_num + 1, cell_idx + 1)
                card_dir = output_dir / CAT_DOMAIN / dominio
                card_dir.mkdir(exist_ok=True)
                label    = f"domini/{dominio}"

            # ── Origin card ─────────────────────────────────────────────────
            elif cat == CAT_ORIGIN:
                counters[CAT_ORIGIN] += 1
                seq      = counters[CAT_ORIGIN]
                meta     = build_metadata(spans, CAT_ORIGIN, None,
                                          page_num + 1, cell_idx + 1)
                card_dir = output_dir / CAT_ORIGIN
                label    = CAT_ORIGIN

            # ── Community card ──────────────────────────────────────────────
            else:
                counters[CAT_COMMUNITY] += 1
                seq      = counters[CAT_COMMUNITY]
                meta     = build_metadata(spans, CAT_COMMUNITY, None,
                                          page_num + 1, cell_idx + 1)
                card_dir = output_dir / CAT_COMMUNITY
                label    = CAT_COMMUNITY

            # ── Save PNG + JSON ─────────────────────────────────────────────
            base      = f"{safe_filename(meta.get('nome', 'carta'))}_{seq:03d}"
            png_path  = card_dir / f"{base}.png"
            json_path = card_dir / f"{base}.json"

            Image.fromarray(card_img).save(png_path, "PNG", dpi=(dpi, dpi))
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            total += 1
            print(f"  [{label}] '{meta.get('nome', '?')[:42]}' -> {png_path.name}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"Done! {total} cards extracted to '{output_dir}/'")
    print(f"  {CAT_ORIGIN:<20}: {counters[CAT_ORIGIN]}")
    print(f"  {CAT_COMMUNITY:<20}: {counters[CAT_COMMUNITY]}")
    print(f"  {CAT_DOMAIN:<20}:")
    for d, c in sorted(domain_counters.items()):
        print(f"    {d:<22}: {c}")

    doc.close()


# ── Debug helper ───────────────────────────────────────────────────────────────

def _save_debug_page(
    page_img: np.ndarray,
    page:     fitz.Page,
    grid:     list[fitz.Rect],
    out_dir:  Path,
    page_num: int,
) -> None:
    pr      = page.rect
    ph, pw  = page_img.shape[:2]
    sx, sy  = pw / pr.width, ph / pr.height

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


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract Daggerheart cards from the Italian printable PDF.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--pdf",    type=Path, default=PDF_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--dpi",    type=int,  default=DPI)
    parser.add_argument("--debug",  action="store_true")
    args = parser.parse_args()
    process_pdf(
        pdf_path   = args.pdf,
        output_dir = args.output,
        dpi        = args.dpi,
        debug      = args.debug,
    )


if __name__ == "__main__":
    main()
