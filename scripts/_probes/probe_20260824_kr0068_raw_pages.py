"""KR0068 2025.2Q raw PDF p16-19 전문 덤프 (좌표 포함) — 조사용, 읽기 전용."""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]


def dump(pdf_path: Path, pages: list[int], out: Path, label: str) -> None:
    doc = fitz.open(pdf_path)
    lines = [f"### {label} — {pdf_path.name} (pages 1-based {pages})", ""]
    for p in pages:
        if p - 1 >= len(doc):
            lines.append(f"-- page {p}: OUT OF RANGE (doc has {len(doc)}) --")
            continue
        page = doc[p - 1]
        lines.append(f"===== page {p} (plain text) =====")
        lines.append(page.get_text("text"))
        lines.append(f"===== page {p} (words, y-grouped) =====")
        words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
        rows: dict[int, list] = {}
        for w in words:
            key = round(w[1] / 3.0)
            rows.setdefault(key, []).append(w)
        for key in sorted(rows):
            ws = sorted(rows[key], key=lambda w: w[0])
            txt = "  ".join(f"{w[4]}@{w[0]:.0f}" for w in ws)
            lines.append(f"  y={ws[0][1]:7.1f} | {txt}")
        lines.append("")
    doc.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    pdf = ROOT / sys.argv[1]
    pages = [int(x) for x in sys.argv[2].split(",")]
    out = ROOT / "artifacts" / "validation" / sys.argv[3]
    dump(pdf, pages, out, sys.argv[4] if len(sys.argv) > 4 else pdf.stem)
