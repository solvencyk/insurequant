# -*- coding: utf-8 -*-
"""Dump rows of the separate-basis note 50 (회계정책의 변경) tables of FY2025 Q1/Q2/Q3 filings: 재작성이 포괄손익계산서에 미치는 영향."""
import re, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
import KR0083_xml as X
RNG = {"FY2025_Q1": (41532, 41800), "FY2025_Q2": (43874, 44140), "FY2025_Q3": (38139, 38405)}
RE_P = re.compile(r"<P[^>]*>(.*?)</P>")
RE_TAG = re.compile(r"<[^>]+>")
L = []
for fy, (a, b) in RNG.items():
    lines = X.load_lines(fy)
    L.append(f"=== {fy} {X.FILES[fy]} L{a}-L{b}")
    cur = None
    for i in range(a - 1, b):
        l = lines[i]
        if l.startswith("<TR"):
            cur = (i + 1, [])
        elif l.startswith("</TR"):
            if cur and cur[1]:
                L.append(f"  R{cur[0]} " + " | ".join(f"{t}@{ln}" for t, ln in cur[1]))
            cur = None
        else:
            m = RE_P.search(l) if ("<P" in l) else None
            txt = None
            if m:
                txt = RE_TAG.sub("", m.group(1)).replace("\u3000", " ").strip()
            elif l.startswith("<SPAN") or l.startswith("<TE") or l.startswith("<TH"):
                mm = re.search(r">([^<]*)(</SPAN>|</T[EH]>)?\s*$", l)
                txt = mm.group(1).strip() if mm else None
            if txt:
                if cur is not None:
                    cur[1].append((txt, i + 1))
                else:
                    L.append(f"  T L{i+1}: {txt[:600]}")
open("KR0083_note50_dump.txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print(len(L))
