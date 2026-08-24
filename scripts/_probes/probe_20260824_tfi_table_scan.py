"""여러 회사·분기의 [공통적용 경과조치] 표를 raw PDF 에서 찾아 그 행들만 뽑는다.

item47(보완자본 한도 적용 전)의 스코프가 회사별로 다르다는 판정의 **반증용 대조군**.
INCL 사(한화생명·AIA)와 EXCL 사(IBK연금)의 같은 표를 나란히 놓는다. 읽기 전용.
"""
from __future__ import annotations

from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "validation" / "probe_20260824_tfi_tables.txt"

TARGETS = [
    ("data/disclosure/FY2025_Q2/raw/KR0068_한화생명.pdf", "KR0068 한화생명 2025.2Q (INCL, 한도 구속)"),
    ("data/disclosure/FY2025_Q1/raw/KR0068_한화생명.pdf", "KR0068 한화생명 2025.1Q (INCL, 한도 미구속)"),
    ("data/disclosure/FY2025_Q3/raw/KR0068_한화생명.pdf", "KR0068 한화생명 2025.3Q (INCL, 한도 미구속)"),
    ("data/disclosure/FY2025_Q3/raw/KR1011_IBK연금보험.pdf", "KR1011 IBK연금 2025.3Q (EXCL, 한도 구속)"),
    ("data/disclosure/FY2025_Q3/raw/KR0080_에이아이에이생명보험.pdf", "KR0080 AIA 2025.3Q (INCL 투표)"),
]

ANCHOR = "보완자본 한도 적용 전"
ROWS = ["지급여력금액", "기본자본", "보완자본", "보완자본 한도 적용 전", "보완자본 한도",
        "해약환급금", "기발행", "지급여력기준금액", "지급여력비율"]


def scan(rel: str, label: str) -> list[str]:
    p = ROOT / rel
    lines = [f"########## {label}", f"  file: {rel}"]
    if not p.exists():
        lines.append("  !! MISSING")
        return lines
    doc = fitz.open(p)
    hit = None
    for i in range(len(doc)):
        flat = doc[i].get_text("text").replace(" ", "").replace("\n", "")
        if ANCHOR.replace(" ", "") in flat:
            hit = i
            break
    if hit is None:
        lines.append("  !! anchor not found (스캔본이거나 표 미기재)")
        doc.close()
        return lines
    page = doc[hit]
    lines.append(f"  page (1-based) = {hit + 1}")
    words = page.get_text("words")
    band: dict[int, list] = {}
    for w in words:
        band.setdefault(round(w[1] / 3.0), []).append(w)
    for key in sorted(band):
        ws = sorted(band[key], key=lambda w: w[0])
        txt = " ".join(w[4] for w in ws)
        flat = txt.replace(" ", "")
        if any(r.replace(" ", "") in flat for r in ROWS) or any(c.isdigit() for c in txt):
            lines.append(f"   y={ws[0][1]:6.1f} | " + "  ".join(f"{w[4]}@{w[0]:.0f}" for w in ws))
    doc.close()
    return lines


if __name__ == "__main__":
    out: list[str] = []
    for rel, label in TARGETS:
        out.extend(scan(rel, label))
        out.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT}")
