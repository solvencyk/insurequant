# -*- coding: utf-8 -*-
"""Read-only. Locate the prior-period-error note ('전기오류') in the FY2024 Q3 / Q2 / Q1 reports of KR0104 and dump the note text + effect tables (text only, with line numbers)."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import KR0104_xml as X
TAG = re.compile(r"<[^>]+>")
out = []
for fy in ("FY2024_Q3", "FY2024_Q2", "FY2024_Q1"):
    L = X.load_lines(fy)
    hits = [i for i, l in enumerate(L, 1) if "전기오류의 성격" in l]
    out.append(f"== {fy} {X.FILES[fy]} hits {hits}")
    if not hits:
        continue
    s = hits[0]
    e = s
    # collect until next <TITLE of same or higher level after 400 lines max
    n = 0
    for i in range(s - 1, min(len(L), s + 1800)):
        t = TAG.sub("", L[i]).replace("\u3000", " ").strip()
        if t:
            out.append(f"L{i+1} {t[:300]}")
            n += 1
        if n > 260:
            break
(Path(__file__).resolve().parent / "KR0104_s1_note.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print(len(out))
