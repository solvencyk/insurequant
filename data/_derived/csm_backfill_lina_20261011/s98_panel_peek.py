# -*- coding: utf-8 -*-
"""Read-only: current state of the Lina entry in data/dart/viz/csm_amort_schedule.json (another agent is correcting this panel)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")
p = json.loads((ROOT / "data/dart/viz/csm_amort_schedule.json").read_text(encoding="utf-8"))["companies"]
for c in p:
    if c["company"] in ("라이나생명보험", "삼성생명", "흥국화재"):
        print(c["company"], c.get("period"), "y1", (c.get("yearly") or {}).get("y1"), "total", (c.get("buckets") or {}).get("total"), "keys", [k for k in c.keys() if k.startswith("_")])
