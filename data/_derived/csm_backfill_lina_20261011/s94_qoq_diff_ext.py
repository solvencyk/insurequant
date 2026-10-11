# -*- coding: utf-8 -*-
"""Step 94 (read-only): QOQ_DELTA_WARN rows that are new after the extension load (gate_ext_after vs gate_ext_before outputs)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
before = json.loads((W / "gate_ext_before" / "qoq_warn.json.written_by_gate").read_text(encoding="utf-8"))
after = json.loads((W / "gate_ext_after" / "qoq_warn.json.written_by_gate").read_text(encoding="utf-8"))
key = lambda r: (r["company"], r["quarter"], r["item"])  # noqa: E731
bk, ak = {key(r): r for r in before}, {key(r): r for r in after}
print("before", len(before), "after", len(after))
for k in sorted(set(ak) - set(bk)):
    print("NEW    ", ak[k])
for k in sorted(set(bk) - set(ak)):
    print("GONE   ", bk[k])
for k in sorted(set(bk) & set(ak)):
    if bk[k] != ak[k]:
        print("CHANGED", bk[k], "->", ak[k])
