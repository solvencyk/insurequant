"""Check whether KR0079 (미래에셋생명) 2025.2Q / 2025.3Q rows already exist in the committed
PL_breakdown.json / pl_breakdown_master.json, and if so what item4/5/6/9/10/11 currently hold.
Read-only, does not touch any master.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

for name in ("PL_breakdown.json", "data/dart/viz/pl_breakdown_master.json"):
    p = ROOT / name
    d = json.load(open(p, encoding="utf-8"))
    print(f"\n=== {name} ({len(d)} rows) ===")
    rows = [r for r in d if r.get("회사Code") == "KR0079"
            or r.get("회사코드") == "KR0079"]
    if not rows:
        # try generic key scan
        sample = d[0]
        print("  keys:", list(sample.keys()))
        rows = [r for r in d if "KR0079" in str(r.values())]
    quarters = sorted({r.get("공시분기") or r.get("period") for r in rows})
    print("  KR0079 rows:", len(rows), " quarters present:", quarters)
    for r in rows:
        q = r.get("공시분기") or r.get("period")
        if q in ("2025.2Q", "2025.3Q"):
            print(" ", r)
