"""Read-only: print master PL items of a company-quarter.  usage: python s87_peek_master_pl.py KR0068 2023.2Q [2023.1Q ...]"""
import json, sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
kr = sys.argv[1]
qs = sys.argv[2:]
rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in rows}
L = {r["항목번호"]: r.get("항목명") for r in rows}
for q in qs:
    print("=" * 60, kr, q)
    for i in range(1, 33):
        v = M.get((kr, q, i))
        if v is not None:
            print(f"  {i:>2} {str(L.get(i))[:24]:<24} {v}")
