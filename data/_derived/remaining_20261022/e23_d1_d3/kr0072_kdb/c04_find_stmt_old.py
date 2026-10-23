# -*- coding: utf-8 -*-
"""read-only: locate every table in a filing whose first column contains 보험서비스결과|보험손익 and 법인세 rows (income statement candidates), with line numbers and section."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
rel = sys.argv[1]
L = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
titles = [(i, re.sub(r"<[^>]+>", "", s).strip()) for i, s in enumerate(L) if s.startswith("<TITLE")]


def sect(i):
    cur = None
    for k, t in titles:
        if k <= i:
            cur = (k + 1, t)
        else:
            break
    return cur


tabs = []
stack = []
for i, s in enumerate(L):
    if re.match(r"\s*<TABLE\b", s):
        stack.append(i)
    elif re.match(r"\s*</TABLE", s) and stack:
        tabs.append((stack.pop(), i))
tabs.sort()
for a, b in tabs:
    txt = " ".join(re.sub(r"<[^>]+>", "", x).strip() for x in L[a:b + 1])
    if ("법인세" in txt and ("보험서비스결과" in txt or "보험손익" in txt) and "당기순" in txt) or ("당기순이익" in txt and "총포괄" in txt):
        print(f"table L{a+1}-L{b+1} rows~{sum(1 for x in L[a:b+1] if x.lstrip().startswith('<TR'))} section {sect(a)}")
