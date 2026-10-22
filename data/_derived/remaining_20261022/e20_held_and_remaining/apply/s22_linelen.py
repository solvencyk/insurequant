#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 22 (read-only): longest lines (BYTES, the unit scripts/doc_rotate.py --check uses, limit 1200) of the edited TODO, current vs the pre-edit copy."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
SP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad")
for label, p in (("current", ROOT / "TODO_parser_ifrs17.md"), ("pre-edit", SP / "e20_backup" / "docs_pre" / "TODO_parser_ifrs17.md")):
    lines = p.read_bytes().split(b"\n")
    rank = sorted(((len(s), i + 1, s.decode("utf-8")[:60]) for i, s in enumerate(lines)), reverse=True)[:5]
    print(label, "lines", len(lines))
    for n, i, s in rank:
        print(f"  L{i}: {n} bytes: {s}")
