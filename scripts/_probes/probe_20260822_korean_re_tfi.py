# -*- coding: utf-8 -*-
"""Extract '(1) 공통적용 경과조치' table's own 기본자본/보완자본 rows (pre/post) for
Korean Re (KR1000) across the 6 flagged quarters + 2024.4Q, using word-coordinates
(같은 방법론 as validation's own 2023.2Q check) to avoid the text-order-scramble risk.
Read-only. 2026-08-22."""
import io, sys
from pathlib import Path
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

quarters = ["FY2023_Q2", "FY2023_Q3", "FY2023_Q4", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"]

for q in quarters:
    pdf = ROOT / "data/disclosure" / q / "raw" / "KR1000_코리안리.pdf"
    doc = fitz.open(pdf)
    print(f"\n#### {q} pages={doc.page_count} ####")
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if "공통적용" in t and "보완자본" in t and "한도" in t:
            print(f"-- page idx {i} (printed {i+1}) --")
            words = doc[i].get_text("words")  # (x0,y0,x1,y1,word,block,line,word_no)
            # group by line (block,line)
            lines = {}
            for w in words:
                key = (w[5], w[6])
                lines.setdefault(key, []).append(w)
            # find lines containing 기본자본 or 보완자본 as a standalone/leading token
            for key in sorted(lines, key=lambda k: (lines[k][0][1],)):
                toks = sorted(lines[key], key=lambda w: w[0])
                text = "".join(tk[4] for tk in toks)
                if text.strip() in ("기본자본", "보완자본", "지급여력기준금액", "지급여력금액"):
                    print(f"   y={toks[0][1]:.1f} label='{text}'")
                    for tk in toks:
                        print(f"      tok='{tk[4]}' x0={tk[0]:.1f}")
    doc.close()
