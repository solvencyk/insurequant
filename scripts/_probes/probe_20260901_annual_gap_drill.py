"""Drill into the ANNUAL-quarter gaps: which cells, what raw exists, what report_kind."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
CEN = json.loads((ROOT / "data" / "_derived" / "pl_coverage_census_20260901.json").read_text(encoding="utf-8"))
grid, pc = CEN["grid"], CEN["per_company"]
ANNUAL = ["2023.4Q", "2024.4Q", "2025.4Q"]

print("=== ALL annual cells that are NOT a_in_master ===")
for code in sorted(grid):
    for q in ANNUAL:
        cell = grid[code][q]
        if cell["verdict"] != "a_in_master":
            print(f"{code:7s} {pc[code]['name'][:22]:22s} {q}  {cell['verdict']:22s} raw={cell['raw']}")

print()
print("=== every raw dir on disk for the gap companies (all FY, all kinds) ===")
targets = ["KR0080", "KR0075", "KR1010", "KR0050", "KR0076", "KR1098", "KR0150"]
for code in targets:
    print(f"--- {code} {pc[code]['name']}")
    hits = []
    for d in sorted((ROOT / "data" / "dart").glob("FY*/raw/*")):
        if d.name.split("_")[0] == code:
            meta = {}
            mp = d / "meta.json"
            if mp.exists():
                meta = json.loads(mp.read_text(encoding="utf-8"))
            n_xml = len(list(d.rglob("*.xml")))
            hits.append(
                f"    {d.parent.parent.name:12s} {d.name[:52]:52s} period={meta.get('period')} "
                f"kind={meta.get('report_kind')} no_filing={meta.get('no_filing')} n_xml={n_xml}"
            )
    print("\n".join(hits) if hits else "    (no raw dirs at all)")

print()
print("=== extracted/ artifacts for AIA (KR0080) ===")
for p in sorted((ROOT / "data" / "dart").glob("extracted*/**/*")):
    if p.is_file() and ("아이에이" in p.name or "AIA" in p.name.upper() or "에이아이에이" in p.name):
        print(f"    {p.relative_to(ROOT)}")
