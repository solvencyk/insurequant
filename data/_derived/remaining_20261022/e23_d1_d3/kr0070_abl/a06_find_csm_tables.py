# -*- coding: utf-8 -*-
"""read-only: list leaf tables whose body has a row label starting 'I. 기초' / containing '기초 보험계약순' in the given section; print caption guess, header leaf texts and the CSM-relevant rows. usage: a06 <rel> <section title regex>"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from abl_lib import *  # noqa

sys.stdout.reconfigure(encoding="utf-8")
rel, sec = sys.argv[1], sys.argv[2]
L = lines_of(rel)
a0, b0 = section_range(L, sec)
print(f"section {sec!r}: lines {a0 + 1}..{b0 + 1}")
for (a, b) in all_tables(L):
    if not (a0 <= a <= b0):
        continue
    rows = table_rows(L, a, b)
    labs = [norm_label(r["cells"][0]["text"]) for r in rows if r["cells"]]
    if not any(x.startswith("기초보험계약순부채") or x.startswith("기초재보험계약순") for x in labs):
        continue
    # caption guess: nearest non-empty text line above matching N) ...
    cap, k, seen = None, a - 1, 0
    while k > 0 and seen < 60:
        t = clean(L[k])
        if t:
            seen += 1
            if re.match(r"^\(?\d\)\s*(당분기|당반기|당기|전분기|전반기|전기|분기|반기)", t) or re.match(r"^\(\d\)", t) or re.match(r"^[가나다라]\.", t):
                cap = (k + 1, t[:100])
                break
        k -= 1
    hdr = [(c["text"], c["line"]) for r in rows[:3] for c in r["cells"] if c["tag"] == "TH"]
    print(f"table L{a + 1}-{b + 1} caption {cap} unit {unit_above(L, a + 1, 80)} header {[h[0] for h in hdr]}")
    for r in rows:
        cs = r["cells"]
        if not cs:
            continue
        nl = norm_label(cs[0]["text"])
        if nl.startswith(("기초보험계약순", "기초재보험계약순")) or "처음인식" in nl or nl.startswith(("보험금융비용", "보험계약마진을조정", "서비스제공으로당기손익")) or re.match(r"^(분기말|반기말|기말|전분기말|전반기말|전기말)(재)?보험계약순", nl):
            print("   ", cs[0]["text"][:60], "|", " | ".join(f"{c['text']}@{c['line']}" for c in cs[1:]))
