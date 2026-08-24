# -*- coding: utf-8 -*-
"""Read-only raw PDF page dump (plain text + y-grouped word coordinates).

Usage:
  python probe_20260824_reaudit_dump_pages.py <pdf-rel-path> <pages csv> <ABS out path>
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]


def dump(pdf_path: Path, pages: list[int], out: Path) -> None:
    doc = fitz.open(pdf_path)
    lines = [f"### {pdf_path.name} pages(1-based)={pages} total={len(doc)}", ""]
    for p in pages:
        if p - 1 >= len(doc) or p < 1:
            lines.append(f"-- page {p}: OUT OF RANGE (doc has {len(doc)}) --")
            continue
        page = doc[p - 1]
        lines.append(f"===== page {p} (plain text) =====")
        lines.append(page.get_text("text"))
        lines.append(f"===== page {p} (words, y-grouped, x coords) =====")
        words = page.get_text("words")
        rows: dict[int, list] = {}
        for w in words:
            rows.setdefault(round(w[1] / 3.0), []).append(w)
        for key in sorted(rows):
            ws = sorted(rows[key], key=lambda w: w[0])
            lines.append(f"  y={ws[0][1]:7.1f} | " + "  ".join(f"{w[4]}@{w[0]:.0f}" for w in ws))
        lines.append("")
    doc.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}  ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    dump(ROOT / sys.argv[1], [int(x) for x in sys.argv[2].split(",")], Path(sys.argv[3]))
