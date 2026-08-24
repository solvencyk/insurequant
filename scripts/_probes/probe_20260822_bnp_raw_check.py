# -*- coding: utf-8 -*-
"""Read-only: is BNP카디프's item47 == item48 an extraction defect or what the
issuer actually printed? docling MD says identical; this reads the raw PDF with
fitz using word x-coordinates so a merged/duplicated column cannot fool us.

2026-08-22 validation iter-5. Modifies nothing."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    ("FY2024_Q3", "KR0075_비엔피파리바카디프생명보험_amended.pdf"),
    ("FY2024_Q4", "KR0075_비엔피파리바카디프생명보험.pdf"),
    ("FY2025_Q1", "KR0075_비엔피파리바카디프생명보험.pdf"),
]

for fy, fn in TARGETS:
    p = ROOT / "data" / "disclosure" / fy / "raw" / fn
    if not p.exists():
        cand = list((ROOT / "data" / "disclosure" / fy / "raw").glob("KR0075*"))
        if not cand:
            print(f"!! no raw for {fy}")
            continue
        p = cand[0]
    doc = fitz.open(p)
    print(f"===== {fy}  {p.name}  pages={len(doc)}")
    for pno in range(len(doc)):
        page = doc[pno]
        txt = page.get_text()
        if "보완자본 한도" not in txt.replace(" ", "").replace("보완자본한도", "보완자본 한도"):
            if "한도" not in txt:
                continue
        words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
        # group words into rows by y, then print rows whose text mentions 한도/초과분
        rows = {}
        for w in words:
            key = round(w[1] / 3.0)
            rows.setdefault(key, []).append((w[0], w[4]))
        hits = []
        for key in sorted(rows):
            ws = sorted(rows[key])
            line = " ".join(t for _, t in ws)
            flat = line.replace(" ", "")
            if any(k in flat for k in ("보완자본한도", "해약환급금부족분", "보완자본", "지급여력기준금액")):
                hits.append((key, ws, line))
        if not hits:
            continue
        print(f"  -- page {pno+1} --")
        for key, ws, line in hits:
            xs = "  ".join(f"[x={x:.0f}]{t}" for x, t in ws)
            print(f"    {line}")
            print(f"        {xs}")
        break
    doc.close()
    print()
