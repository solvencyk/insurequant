# -*- coding: utf-8 -*-
"""Per-cell provenance matrix for the 29 orphan-parent buckets.

For every item 2..12 present in the root master, say where it came from:
  GOLD      = data/_gold/user_pl_cells.json (owner/parser overlay, applied post-build)
  OVERRIDE  = build_pl_breakdown._GOLD_CELL_OVERRIDE
  BUILDER   = data/dart/viz/pl_breakdown_master.json (the builder produced it)
  ORPHAN    = in root master but in none of the above -> stale merge leftover
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_pl_breakdown as B  # noqa: E402

BUCKETS = [
    ("KR0002", "2023.1Q"), ("KR0002", "2023.2Q"),
    ("KR0003", "2023.2Q"), ("KR0003", "2023.3Q"),
    ("KR0004", "2023.4Q"), ("KR0004", "2024.4Q"), ("KR0004", "2025.4Q"),
    ("KR0005", "2023.2Q"),
    ("KR0029", "2023.4Q"), ("KR0029", "2024.4Q"), ("KR0029", "2025.4Q"),
    ("KR0068", "2023.1Q"), ("KR0068", "2023.2Q"),
    ("KR0069", "2023.1Q"), ("KR0069", "2023.2Q"),
    ("KR0071", "2023.1Q"), ("KR0071", "2023.2Q"),
    ("KR0073", "2023.1Q"), ("KR0073", "2023.2Q"),
    ("KR0074", "2023.4Q"), ("KR0075", "2023.4Q"),
    ("KR0083", "2023.1Q"), ("KR0083", "2023.2Q"),
    ("KR0094", "2023.1Q"), ("KR0094", "2023.2Q"),
    ("KR0095", "2023.4Q"), ("KR0097", "2023.4Q"),
    ("KR0104", "2023.1Q"), ("KR0104", "2023.2Q"),
]


def load_cells(p):
    rows = json.load(open(p, encoding="utf-8"))
    out = {}
    for r in rows:
        out.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
    return out


builder = load_cells(ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json")
master = load_cells(ROOT / "PL_breakdown.json")

gold = {}
gd = json.load(open(ROOT / "data" / "_gold" / "user_pl_cells.json", encoding="utf-8"))
for e in gd["set"]:
    gold[(e["원보험사코드"], e["공시분기"], e["항목번호"])] = e

ov = B._GOLD_CELL_OVERRIDE

print(f"{'회사':<8}{'분기':<9}{'item':>5} {'값':>14}  provenance   note")
counts = {}
for code, q in BUCKETS:
    m = master.get((code, q), {})
    bl = builder.get((code, q), {})
    for n in range(2, 13):
        v = m.get(n)
        if v is None:
            continue
        g = gold.get((code, q, n))
        if g is not None:
            src = "GOLD"
            note = (g.get("note") or "")[:90]
        elif (code, q) in ov and n in ov[(code, q)]:
            src = "OVERRIDE"
            note = ""
        elif bl.get(n) is not None:
            src = "BUILDER"
            note = ""
        else:
            src = "ORPHAN"
            note = "!! in root master only"
        counts[src] = counts.get(src, 0) + 1
        print(f"{code:<8}{q:<9}{n:>5} {v:>14,.1f}  {src:<11}  {note}")

print("\ncounts:", counts)
