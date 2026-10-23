# -*- coding: utf-8 -*-
"""scan the text files written for this load for kana (U+3040-U+30FF) and for a UTF-8 BOM"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
base = Path(__file__).resolve().parent.parent
bad = []
n = 0
for p in list(base.glob("answers/kr0099_kblife.md")) + list((base / "kr0099_kblife").glob("*.txt")) + list((base / "kr0099_kblife").glob("*.py")) + list((base / "kr0099_kblife").glob("*.json")):
    raw = p.read_bytes()
    n += 1
    if raw[:3] == b"\xef\xbb\xbf":
        bad.append((p.name, "BOM"))
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        continue
    if re.search(r"[\u3040-\u30ff]", t):
        bad.append((p.name, "kana"))
print("scanned", n, "files; problems:", bad)
