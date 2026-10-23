# -*- coding: utf-8 -*-
"""read-only: print physical lines [start, end] (split on \n, 1-based) of an xml file. usage: peek_lines.py <path> <start> <end> [raw]"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
path, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
raw = len(sys.argv) > 4
lines = Path(path).read_text(encoding="utf-8", errors="replace").split("\n")
for i in range(a, min(b, len(lines)) + 1):
    t = lines[i - 1]
    if not raw:
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "|", t)).strip()
        t = re.sub(r"(\|\s*)+", "|", t)
    print(f"L{i}: {t[:240]}")
