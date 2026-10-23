# -*- coding: utf-8 -*-
"""read-only: no Japanese kana and no CJK ideograph (outside Hangul) in the Korean text files this load wrote (answer + INDEX)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
files = [HERE.parent / "answers/kr0072_kdb.md", HERE / "INDEX.txt"]
bad = 0
for f in files:
    t = f.read_text(encoding="utf-8")
    for n, line in enumerate(t.split("\n"), 1):
        for ch in line:
            o = ord(ch)
            if 0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0xFF66 <= o <= 0xFF9F:
                print(f"{f.name}:{n}: U+{o:04X} {ch!r}")
                bad += 1
print("kana/ideograph hits:", bad)
