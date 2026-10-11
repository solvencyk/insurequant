# -*- coding: utf-8 -*-
"""Which QOQ_DELTA_WARN YELLOW rows are new after the Lina load (gate_after/qoq_warn.json.written_by_gate vs the pre-run file)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
before = json.loads((W / "gate_before" / "qoq_warn.json.pre_run").read_text(encoding="utf-8"))
after = json.loads((W / "gate_after" / "qoq_warn.json.written_by_gate").read_text(encoding="utf-8"))
key = lambda r: (r["company"], r["quarter"], r["item"])  # noqa: E731
bk = {key(r): r for r in before}
ak = {key(r): r for r in after}
print("before", len(before), "after", len(after))
for k in sorted(set(ak) - set(bk)):
    print("NEW   ", ak[k])
for k in sorted(set(bk) - set(ak)):
    print("GONE  ", bk[k])
for k in sorted(set(bk) & set(ak)):
    if bk[k] != ak[k]:
        print("CHANGED", bk[k], "->", ak[k])
