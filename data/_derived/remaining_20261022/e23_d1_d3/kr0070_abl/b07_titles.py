# -*- coding: utf-8 -*-
"""read-only: list the <TITLE> lines (with 1-based physical line) of the KR0070 filings used by this load. usage: b07_titles.py <rel> [regex]"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from abl_lib import *  # noqa

sys.stdout.reconfigure(encoding="utf-8")
rel = sys.argv[1]
rx = re.compile(sys.argv[2]) if len(sys.argv) > 2 else None
L = lines_of(rel)
print(f"{rel}: {len(L)} lines")
for k, t in titles(L):
    if rx is None or rx.search(t):
        print(f"  L{k + 1}: {t[:110]}")
