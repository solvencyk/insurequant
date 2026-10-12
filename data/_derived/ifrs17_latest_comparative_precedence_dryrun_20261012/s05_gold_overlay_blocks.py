"""Read-only: list the gold-overlay (owner xlsx fills) blocks - (master, company, quarter) with item count and the note keywords.

Writes gold_overlay_blocks.csv next to this script. The point: a block that carries an owner overlay cell is a "gold conflict"
candidate for the latest-comparative precedence (owner cells are never overwritten by a dry-run candidate).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

csm = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
print("csm keys", list(csm["set"][0].keys()))
print("pl keys", list(pl["set"][0].keys()))
print("csm sample", json.dumps(csm["set"][0], ensure_ascii=False)[:400])
print("pl sample", json.dumps(pl["set"][0], ensure_ascii=False)[:400])

blocks = defaultdict(lambda: {"items": [], "notes": set()})
for master, doc in (("CSM_waterfall", csm), ("PL_breakdown", pl)):
    for c in doc["set"]:
        code = c.get("code") or c.get("원보험사코드")
        q = c.get("quarter") or c.get("공시분기")
        it = c.get("item") if "item" in c else c.get("항목번호")
        key = (master, code, q)
        blocks[key]["items"].append(it)
        n = c.get("note") or c.get("reason") or c.get("basis") or ""
        if n:
            blocks[key]["notes"].add(str(n)[:160])

rows = []
for (m, code, q), v in sorted(blocks.items(), key=lambda kv: (kv[0][0], str(kv[0][1]), str(kv[0][2]))):
    rows.append([m, code, q, len(v["items"]), ",".join(str(i) for i in sorted(v["items"], key=str)), " || ".join(sorted(v["notes"]))[:400]])
with open(OUT / "gold_overlay_blocks.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["master", "code", "quarter", "n_items", "items", "notes"])
    w.writerows(rows)
print("blocks", len(rows), "cells", sum(r[3] for r in rows))
by_m = defaultdict(int)
for r in rows:
    by_m[r[0]] += 1
print(dict(by_m))
