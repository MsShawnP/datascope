"""
Render samples/output/screenshots/strict_mode_comparison.png.

Produces a side-by-side comparison of the Field Rankings tab in standard mode
vs --strict-types mode for sample_mixed_types.xlsx. The two tables are rendered
directly with Pillow so the screenshot stays in sync with the actual scorer
output without needing a screen recording / Excel.

Usage:
    python tools/render_strict_mode_comparison.py
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "samples" / "output" / "screenshots" / "strict_mode_comparison.png"

# Make `scorer` importable so we can sanity-check the hardcoded numbers below
# against what the live code actually produces on the bundled sample.
sys.path.insert(0, str(ROOT))

NAVY = (31, 56, 100)
LIGHT_BLUE = (217, 225, 242)
GREEN = (99, 190, 123)
YELLOW = (255, 235, 132)
RED = (248, 105, 107)
ALT_ROW = (238, 242, 247)
WHITE = (255, 255, 255)
GREY_BORDER = (180, 180, 180)
TEXT = (33, 33, 33)
WHITE_TEXT = (255, 255, 255)
SUBTITLE = (80, 80, 80)


def score_color(value):
    if value >= 0.75:
        return GREEN
    if value >= 0.45:
        return YELLOW
    return RED


def _font(size, bold=False):
    path = (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    )
    return ImageFont.truetype(path, size)


def _draw_cell(draw, x, y, w, h, text, *, fill, text_color, font, align="center"):
    draw.rectangle([x, y, x + w, y + h], fill=fill, outline=GREY_BORDER, width=1)
    if text is None or text == "":
        return
    bbox = draw.textbbox((0, 0), str(text), font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    if align == "center":
        tx = x + (w - tw) // 2
    elif align == "left":
        tx = x + 8
    else:
        tx = x + w - tw - 8
    ty = y + (h - th) // 2 - bbox[1]
    draw.text((tx, ty), str(text), fill=text_color, font=font)


def _draw_table(draw, top_left, title, headers, rows, col_widths, score_col_idx):
    x0, y0 = top_left
    title_h = 32
    header_h = 28
    row_h = 26
    table_w = sum(col_widths)

    # Title bar
    draw.rectangle([x0, y0, x0 + table_w, y0 + title_h],
                   fill=LIGHT_BLUE, outline=GREY_BORDER, width=1)
    title_font = _font(13, bold=True)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    th = bbox[3] - bbox[1]
    draw.text((x0 + 10, y0 + (title_h - th) // 2 - bbox[1]),
              title, fill=NAVY, font=title_font)

    # Header row
    hy = y0 + title_h
    header_font = _font(11, bold=True)
    cx = x0
    for header, width in zip(headers, col_widths):
        _draw_cell(draw, cx, hy, width, header_h, header,
                   fill=NAVY, text_color=WHITE_TEXT, font=header_font)
        cx += width

    # Data rows
    body_font = _font(11)
    for r_idx, row in enumerate(rows):
        ry = hy + header_h + r_idx * row_h
        row_bg = ALT_ROW if r_idx % 2 == 1 else WHITE
        cx = x0
        for c_idx, (value, width) in enumerate(zip(row, col_widths)):
            if c_idx == score_col_idx:
                try:
                    fill = score_color(float(value))
                except (ValueError, TypeError):
                    fill = row_bg
            else:
                fill = row_bg
            align = "left" if c_idx == 1 else "center"
            _draw_cell(draw, cx, ry, width, row_h, value,
                       fill=fill, text_color=TEXT, font=body_font, align=align)
            cx += width

    return table_w, title_h + header_h + len(rows) * row_h


def main():
    # Source-of-truth rows are the actual current scorer outputs.
    standard_headers = ["rank", "field", "composite_score", "field_type",
                        "null_count", "unique_count"]
    standard_rows = [
        [1, "revenue",       "1.0000", "numeric_continuous",  0, 200],
        [2, "revenue_mixed", "0.9775", "numeric_continuous", 15, 185],
        [3, "customer_id",   "0.7750", "identifier",          0, 200],
        [4, "region",        "0.6287", "categorical_low",     0,   5],
    ]
    standard_widths = [50, 130, 130, 170, 90, 110]

    strict_headers = standard_headers + ["type_mix"]
    strict_rows = [
        [1, "revenue",       "1.0000", "numeric_continuous",  0, 200, "numeric:200"],
        [2, "revenue_mixed", "0.9708", "numeric_continuous",  0, 186, "numeric:185, str:15"],
        [3, "customer_id",   "0.8500", "identifier",          0, 200, "str:200"],
        [4, "region",        "0.7036", "categorical_low",     0,   5, "str:200"],
    ]
    strict_widths = [50, 130, 130, 170, 90, 110, 175]

    pad = 24
    gap = 32
    caption_h = 60
    title_h_outer = 56  # top header strip ("Field Rankings — ...")
    standard_w = sum(standard_widths)
    strict_w = sum(strict_widths)
    total_w = pad + standard_w + gap + strict_w + pad
    total_h = pad + title_h_outer + (32 + 28 + len(standard_rows) * 26) + caption_h + pad

    img = Image.new("RGB", (total_w, total_h), WHITE)
    draw = ImageDraw.Draw(img)

    title_font = _font(15, bold=True)
    draw.text((pad, pad),
              "Field Rankings — sample_mixed_types.xlsx (rank tab)",
              fill=NAVY, font=title_font)
    subtitle_font = _font(11)
    draw.text((pad, pad + 24),
              "Left: standard mode  ·  Right: --strict-types  "
              "(same input, scored two ways)",
              fill=SUBTITLE, font=subtitle_font)

    table_top = pad + title_h_outer
    _draw_table(
        draw, (pad, table_top),
        "Field Rankings — sample_mixed_types.xlsx",
        standard_headers, standard_rows, standard_widths,
        score_col_idx=2,
    )
    _draw_table(
        draw, (pad + standard_w + gap, table_top),
        "Field Rankings — sample_mixed_types.xlsx [strict-types]",
        strict_headers, strict_rows, strict_widths,
        score_col_idx=2,
    )

    # Caption beneath the tables
    caption_y = table_top + 32 + 28 + len(standard_rows) * 26 + 16
    cap_font = _font(11)
    cap_bold = _font(11, bold=True)

    line1 = "Standard mode: revenue_mixed scores 0.9775 and is classified as numeric_continuous —"
    line1b = " the 15 string cells were silently converted to NaN."
    draw.text((pad, caption_y), line1, fill=TEXT, font=cap_font)
    bbox = draw.textbbox((0, 0), line1, font=cap_font)
    draw.text((pad + (bbox[2] - bbox[0]), caption_y), line1b, fill=TEXT, font=cap_font)

    line2_a = "--strict-types: revenue_mixed scores 0.9708, still numeric_continuous,"
    line2_b = " and the new type_mix column exposes the breakdown: "
    line2_c = "numeric:185, str:15"
    line2_d = "."
    y2 = caption_y + 20
    draw.text((pad, y2), line2_a, fill=TEXT, font=cap_font)
    w = draw.textbbox((0, 0), line2_a, font=cap_font)[2]
    draw.text((pad + w, y2), line2_b, fill=TEXT, font=cap_font)
    w += draw.textbbox((0, 0), line2_b, font=cap_font)[2]
    draw.text((pad + w, y2), line2_c, fill=NAVY, font=cap_bold)
    w += draw.textbbox((0, 0), line2_c, font=cap_bold)[2]
    draw.text((pad + w, y2), line2_d, fill=TEXT, font=cap_font)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_PATH, format="PNG")
    print(f"Wrote {OUT_PATH.relative_to(ROOT)}  ({img.size[0]}×{img.size[1]})")

    _verify_against_live_scorer(standard_rows, strict_rows)


def _verify_against_live_scorer(standard_rows, strict_rows):
    """Run the scorer on the bundled sample and warn if any hardcoded row
    diverges from what the live code produces. Keeps the script honest."""
    sample = ROOT / "samples" / "input" / "sample_mixed_types.xlsx"
    if not sample.exists():
        print(f"  (skip verification — {sample.relative_to(ROOT)} not present)")
        return
    try:
        import pandas as pd
        from scorer import analyze, load_strict
    except ImportError as e:
        print(f"  (skip verification — {e})")
        return

    std_actual, _, _, _ = analyze(pd.read_excel(sample), strict_types=False)
    strict_actual, _, _, _ = analyze(load_strict(str(sample), 0), strict_types=True)

    mismatches = []
    for table_name, hardcoded, actual in (
        ("standard", standard_rows, std_actual),
        ("strict", strict_rows, strict_actual),
    ):
        for row in hardcoded:
            field, hc_score = row[1], row[2]
            actual_row = actual[actual["field"] == field]
            if actual_row.empty:
                mismatches.append(f"{table_name}/{field}: missing in actual output")
                continue
            live_score = f"{float(actual_row.iloc[0]['composite_score']):.4f}"
            if live_score != hc_score:
                mismatches.append(
                    f"{table_name}/{field}: hardcoded {hc_score} vs live {live_score}"
                )

    if mismatches:
        print("  WARNING: hardcoded rows are stale — rerender after updating:")
        for m in mismatches:
            print(f"    - {m}")
    else:
        print("  Verified against live scorer output ✓")


if __name__ == "__main__":
    main()
