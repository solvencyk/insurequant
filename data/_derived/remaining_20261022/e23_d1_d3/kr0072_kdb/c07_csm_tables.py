# -*- coding: utf-8 -*-
"""read-only: every table in the filing whose header names 보험계약마진 (CSM) with the nearest preceding <P> captions (3 deep), section and its first body label, to find the issued general-model roll-forward tables."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
rel = sys.argv[1]
L = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
TAG = re.compile(r"<[^>]+>")


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ")).strip()


titles = [(i, clean(s)) for i, s in enumerate(L) if s.startswith("<TITLE")]


def sect(i):
    cur = None
    for k, t in titles:
        if k <= i:
            cur = (k + 1, t)
        else:
            break
    return cur


tabs, stack = [], []
for i, s in enumerate(L):
    if re.match(r"\s*<TABLE\b", s):
        if stack:
            stack[-1][1] = True
        stack.append([i, False])
    elif re.match(r"\s*</TABLE", s) and stack:
        a, ch = stack.pop()
        if not ch:
            tabs.append((a, i))
tabs.sort()
for a, b in tabs:
    txt = " ".join(clean(x) for x in L[a:b + 1])
    if "보험계약마진" in txt and ("기초" in txt and ("신계약" in txt or "최초 인식" in txt)):
        caps = []
        k = a - 1
        while k > 0 and len(caps) < 3:
            t = clean(L[k])
            if t and not t.startswith("<"):
                caps.append((k + 1, t[:80]))
            k -= 1
            if a - k > 60:
                break
        first = [clean(x) for x in L[a:b + 1] if re.match(r"\s*<T[DEH]", x) and clean(x)][:8]
        print(f"table L{a+1}-L{b+1} sect {sect(a)} caps {caps}\n      first cells {first}")
