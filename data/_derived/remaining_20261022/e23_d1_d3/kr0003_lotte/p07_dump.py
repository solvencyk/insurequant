# -*- coding: utf-8 -*-
"""Read-only compact dump of physical lines of a DART xml: usage p07_dump.py <rel path under repo> <first line> <last line> [--raw]"""
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
rel, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
raw = "--raw" in sys.argv
L = open(ROOT + rel, encoding="utf-8", errors="replace").read().split("\n")
TAG = re.compile(r"<[^>]+>")
for i in range(a - 1, min(b, len(L))):
    s = L[i]
    if raw:
        print(f"{i+1}: {s[:300]}")
        continue
    t = TAG.sub("", s).strip()
    m = re.match(r"\s*<(TABLE|/TABLE|THEAD|/THEAD|TBODY|TR|/TR|TITLE)\b", s, re.I)
    mark = ""
    if m:
        mark = "<" + m.group(1).upper() + ">"
        ctx = re.search(r'ACONTEXT="([^"]*)"', s)
    ctx = re.search(r'ACONTEXT="([^"]*)"', s)
    attrs = ""
    cs = re.search(r'(COLSPAN|ROWSPAN)="(\d+)"', s)
    if cs:
        attrs = f" [{cs.group(1)}={cs.group(2)}]"
    if ctx:
        attrs += " ctx=" + ctx.group(1)[:20]
    if t or mark:
        print(f"{i+1}: {mark}{attrs} {t[:200]}")
