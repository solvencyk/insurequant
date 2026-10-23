# -*- coding: utf-8 -*-
"""read-only: list <TITLE ...> lines (section structure) of an xml file with 1-based physical line numbers (split on \n). usage: list_titles.py <path>"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
lines = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").split("\n")
for i, t in enumerate(lines, 1):
    if t.startswith("<TITLE"):
        print(f"L{i}: {re.sub(chr(60) + '[^>]+>', '', t).strip()[:120]}")
print("total lines", len(lines))
