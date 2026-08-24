# -*- coding: utf-8 -*-
"""Read-only probe: KR0073(교보생명보험) 2023.1Q TFI(공통적용경과조치) table,
items 47/48/49/50/51. Pure investigation -- writes findings to a JSON file
under scripts/_probes/, never touches kics_disclosure.json.

Step 1: locate the page(s) where '공통적용' + '보완자본' + '한도' all co-occur.
Step 2: dump that page's get_text().splitlines() in order (line-scramble check).
Step 3: dump get_text("words") coordinates for the label lines + numeric tokens
so we can reconstruct the true (label -> value) pairing by y-proximity.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import fitz  # noqa: E402

PDF = REPO / "data" / "disclosure" / "FY2023_Q1" / "raw" / "KR0073_교보생명보험.pdf"
OUT = REPO / "scripts" / "_probes" / "_kr0073_2023q1_tfi_out.json"

out: dict = {"pdf": str(PDF), "exists": PDF.exists()}

doc = fitz.open(PDF)
n = doc.page_count
out["page_count"] = n

page_texts = [doc[i].get_text() for i in range(n)]
matched = [i for i, t in enumerate(page_texts)
           if "공통적용" in t and "보완자본" in t and "한도" in t]
out["matched_pages_0idx"] = matched

# also loosen: pages with '해약환급금 부족분' (item49 label head) in case the
# 3-keyword page and the item49 label sit on different pages
label49_pages = [i for i, t in enumerate(page_texts) if "해약환급금 부족분" in t]
out["label49_pages_0idx"] = label49_pages
kibon_pages = [i for i, t in enumerate(page_texts) if "기본자본" in t]
out["kibon_pages_0idx"] = kibon_pages
scr_pages = [i for i, t in enumerate(page_texts) if "지급여력기준금액" in t]
out["scr_pages_0idx"] = scr_pages

out["per_page_char_count"] = [len(t) for t in page_texts]

# dump line-order for every matched page (+/- 1 page for context)
include = sorted(set(matched) | {i + 1 for i in matched} | {i - 1 for i in matched
                  if i - 1 >= 0})
out["dumped_pages_0idx"] = include

dumps = {}
for i in include:
    if i < 0 or i >= n:
        continue
    lines = page_texts[i].splitlines()
    dumps[str(i)] = [{"line_no": k, "text": l} for k, l in enumerate(lines)]
out["line_dumps"] = dumps

# words (coords) for matched pages + neighbors
words_dump = {}
for i in include:
    if i < 0 or i >= n:
        continue
    words = doc[i].get_text("words")  # (x0,y0,x1,y1, word, block_no, line_no, word_no)
    words_dump[str(i)] = [
        {"x0": round(w[0], 1), "y0": round(w[1], 1), "x1": round(w[2], 1),
         "y1": round(w[3], 1), "text": w[4], "block": w[5], "line": w[6], "word": w[7]}
        for w in words
    ]
out["words_dump"] = words_dump

doc.close()

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
print(f"matched_pages_0idx={matched} label49_pages={label49_pages} "
      f"kibon_pages={kibon_pages[:10]} scr_pages={scr_pages}")
