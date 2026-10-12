"""Read-only: print master vs latest-comparative PL items for the blocks in cand/pl_block_lat_probe.json  (usage: python s78_show_pl_probe.py [KR|quarter ...])"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
rep = json.loads((HERE / "cand" / "pl_block_lat_probe.json").read_text(encoding="utf-8"))
M, LBL = {}, {}
for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")):
    M[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
    LBL[r["항목번호"]] = r.get("항목명") or r.get("항목")
flt = sys.argv[1:]
for key, v in rep.items():
    if flt and not any(f in key for f in flt):
        continue
    kr, q = key.split("|")
    print("=" * 100)
    print(key, "later", v["later"], "| bridge cur", v["bridge_current"], "| bridge lat", v["bridge_latest"])
    lat = {int(k): x for k, x in v["latest_block"].items()}
    for i in range(1, 33):
        c, l = M.get((kr, q, i)), lat.get(i)
        if c is None and l is None:
            continue
        flag = "" if c == l else ("  <-- differs" if c is not None and l is not None else "  <-- one side empty")
        print(f"  {i:>2} {str(LBL.get(i))[:26]:<26} cur={c!s:>14}  lat={l!s:>14}{flag}")
