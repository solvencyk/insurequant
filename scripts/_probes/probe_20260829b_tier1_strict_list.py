# -*- coding: utf-8 -*-
"""List every tier1 company with utilization_pct_strict > 100 (the 7 the coordinator's
follow-up refers to), and confirm the 6 primary-overage companies are a subset."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]

t1 = json.loads((REPO / "kics_tier1_utilization.json").read_text(encoding="utf-8"))["results"]
strict_over = [r for r in t1 if (r.get("utilization_pct_strict") or 0) > 100.0]
primary_over = {r["code"] for r in t1 if (r.get("utilization_pct") or 0) > 100.0}

print(f"strict>100: {len(strict_over)} companies")
for r in sorted(strict_over, key=lambda r: -r["utilization_pct_strict"]):
    tag = "ALSO primary>100" if r["code"] in primary_over else "STRICT-ONLY"
    print(f"  {r['company']:14s} {r['code']}  primary={r['utilization_pct']:>7.1f}  "
          f"strict={r['utilization_pct_strict']:>7.1f}  ratio={r['utilization_pct_strict']/r['utilization_pct']:.4f}"
          f"  [{tag}]" if r['utilization_pct'] else f"  {r['company']} {r['code']} primary=0 strict={r['utilization_pct_strict']}")

print(f"\ntotal rows needing '>100' 비고 (primary row for the 6 + strict row for the 7): "
      f"{len(primary_over) + len(strict_over)}")
