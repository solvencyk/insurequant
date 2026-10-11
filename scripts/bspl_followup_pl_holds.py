#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""List the PL candidates that are still held (status CAND = not loaded) (read-only)."""
import json, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/_derived/bspl_granularity_20261011/pl_candidates"
tot = Counter()
rows = []
for f in sorted(P.glob("KR*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    cands = d.get("candidates") or d.get("cells") or []
    for c in cands:
        tot[(c.get("item"), c.get("status"))] += 1
        if c.get("status") in ("CAND",):
            rows.append((d.get("code"), c))
print(sorted(tot.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))))
print(len(rows), "CAND")
for code, c in rows:
    print(code, json.dumps({k: c[k] for k in c if k not in ("basis",)}, ensure_ascii=False)[:420])
