# -*- coding: utf-8 -*-
"""Dump 保険引受の状況 pages (by-line tables) for the 5 non-life samples to scratch text files."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "J-ESR"))
import extract_esr_template_samples as X  # noqa: E402

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
PAGES = {
    "au_nonlife": [3, 4, 5],
    "meijiyasuda_nonlife": [33, 34, 35],
    "tokiomarine_nichido": [89, 90, 91],
    "mitsui_sumitomo": [94, 95, 96, 97, 98, 99],
    "sompo_japan": [117, 118, 119, 120],
}
for comp in X.COMPANIES:
    k = comp["key"]
    if k not in PAGES:
        continue
    if comp.get("profit_pdf"):
        p = X.SAMPLES / comp["profit_pdf"]
        doc = X.fitz.open(str(p)) if p.exists() else None
        if doc is None:
            print(k, "profit pdf missing"); continue
    else:
        doc, _ = X.open_company_pdf(comp)
    buf = []
    for pno in PAGES[k]:
        buf.append(f"===== page {pno} =====")
        lines = X.page_lines(doc, [pno])
        if comp.get("vertical_labels"):
            lines = X.merge_vertical(lines)
        for _, ln in lines:
            buf.append(ln)
    (OUT / f"{k}.txt").write_text("\n".join(buf), encoding="utf-8")
    print(k, len(buf))
