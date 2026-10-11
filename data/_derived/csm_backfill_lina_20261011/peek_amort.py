# -*- coding: utf-8 -*-
"""Read-only: how is the KR0074 amortisation schedule stored in the viz panel / master, and how does build_csm_sensitivity /
build_tidy_exports derive CSM_amortization.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")

p = json.loads((ROOT / "data/dart/viz/csm_amort_schedule.json").read_text(encoding="utf-8"))
print(type(p), list(p.keys())[:20] if isinstance(p, dict) else len(p))
if isinstance(p, dict):
    for k, v in p.items():
        if k in ("companies", "rows", "data"):
            continue
        print("key", k, str(v)[:300])
    comps = p.get("companies") or p.get("rows") or p.get("data")
    print("n", len(comps) if comps is not None else None)
    if isinstance(comps, list):
        for c in comps:
            if "라이나" in json.dumps(c, ensure_ascii=False)[:300] or c.get("code") == "KR0074" or c.get("원보험사코드") == "KR0074":
                print(json.dumps(c, ensure_ascii=False, indent=1)[:3000])
    elif isinstance(comps, dict):
        for k, c in comps.items():
            if "KR0074" in k or "라이나" in k:
                print(k, json.dumps(c, ensure_ascii=False, indent=1)[:3000])
