#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reasons the zero-proof pass gave for the zero-valued cells that are still held (read-only)."""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
rep = json.loads((ROOT / "data/_derived/bspl_followup_20261011/zero_proof_report.json").read_text(encoding="utf-8"))
print(type(rep), (list(rep.keys())[:10] if isinstance(rep, dict) else len(rep)))
rows = rep if isinstance(rep, list) else rep.get("cells") or rep.get("report") or []
print(len(rows))
if rows:
    print(json.dumps(rows[0], ensure_ascii=False)[:600])
c = Counter()
g = defaultdict(list)
for r in rows:
    c[(r.get("verdict"), (r.get("reason") or "")[:90])] += 1
for k, n in c.most_common(40):
    print(n, k)
