# -*- coding: utf-8 -*-
"""ABL read-only: builder fresh sources (pl_breakdown_master.json / csm_waterfall_master_diag.json) vs live masters for KR0070 FY2023 buckets."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
CODE = "KR0070"
src = json.loads((ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
S = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in src}
L = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in live}
print("PL builder source vs live master (KR0070)")
for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]:
    print("--", q)
    for i in range(1, 33):
        s = S.get((CODE, i, q))
        l = L.get((CODE, i, q))
        sv = None if s is None else s.get("값")
        lv = None if l is None else l.get("값")
        flag = "" if sv == lv else "  <-- differs"
        print(f"   {i:>2} src={sv}  live={lv}{flag}")
csm_src = json.loads((ROOT / "data/dart/viz/csm_waterfall_master_diag.json").read_text(encoding="utf-8"))
csm_live = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
CS = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in csm_src}
CL = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in csm_live}
print("CSM builder source vs live master (KR0070)")
for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]:
    print("--", q)
    for i in range(1, 7):
        s = CS.get((CODE, i, q))
        l = CL.get((CODE, i, q))
        print(f"   {i} src={None if s is None else s.get('값')}  live={None if l is None else l.get('값')}")
