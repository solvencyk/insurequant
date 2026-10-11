# -*- coding: utf-8 -*-
"""Step 35 (read-only): for the companies whose annual amortisation panel entry equals their PRIOR-year closing CSM (s34), does
CSM_amortization.json 2025.4Q hold the same (prior-year) schedule?  (compare master y1..y8 with panel yearly y1..y8, 1dp)"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")

census = json.loads((W / "s34_amort_panel_year_census.json").read_text(encoding="utf-8"))
panel = {c["company"]: c for c in json.loads((ROOT / "data/dart/viz/csm_amort_schedule.json").read_text(encoding="utf-8"))["companies"]}
am = json.loads((ROOT / "CSM_amortization.json").read_text(encoding="utf-8"))
by = {}
for r in am:
    by.setdefault((r["원수사명"], r["공시분기"]), {})[r["경과차년"]] = r["상각액"]
sus = [r for r in census if r["verdict"].startswith("EQUALS FY(N-1)")] + [r for r in census if r["company"] == "라이나생명보험"]
print("suspect panel entries:", len(sus))
for r in sus:
    nm = r["master_name"] or r["company"]
    m = by.get((nm, "2025.4Q"), {})
    y = panel[r["company"]].get("yearly") or {}
    same = [m.get(i) is not None and y.get(f"y{i}") is not None and abs(m[i] - y[f"y{i}"]) < 0.051 for i in range(1, 9)]
    print(f"  {r['company']:<14s} master 2025.4Q y1..y3 = {[m.get(i) for i in (1, 2, 3)]} | panel y1..y3 = {[y.get(f'y{i}') for i in (1, 2, 3)]} | master==panel for y1..y8: {sum(same)}/8")
