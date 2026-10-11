#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cells per category / company of hold_reasons_5c.json (read-only)."""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / "data/_derived/bspl_followup_20261011/hold_reasons_5c.json").read_text(encoding="utf-8"))
c = Counter(); z = Counter(); g = Counter(); byco = defaultdict(Counter)
for r in rows:
    c[r["category"]] += r["n_cells"]; z[r["category"]] += r["n_zero"]; g[r["category"]] += 1
    byco[r["category"]][r["key"].split("|")[0]] += r["n_cells"]
print("total", sum(c.values()), "cells in", sum(g.values()), "groups")
for k in sorted(c, key=lambda k: -c[k]):
    print(f"{k:<34} cells {c[k]:>4} (zero-valued {z[k]:>3}) groups {g[k]:>3}  " + " ".join(f"{co}:{n}" for co, n in sorted(byco[k].items())))
