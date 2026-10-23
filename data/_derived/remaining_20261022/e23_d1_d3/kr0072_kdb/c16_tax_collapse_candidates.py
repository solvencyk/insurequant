# -*- coding: utf-8 -*-
"""read-only: which (company, quarter) cells would make the item-23 constructive mutation (item 23 recomputed as 22 - 24) hit PL_YTD_COLLAPSE_TO_ZERO: the recomputed value is exactly 0.0 while the previous quarter of
the SAME FY holds a non-zero item 23.  Evaluated on the PRE-LOAD backup and on the live (post-load) PL master."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb"


def cands(path):
    rows = json.loads(path.read_text(encoding="utf-8"))
    v = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in rows}
    out = []
    for (c, i, q), x in v.items():
        if i != 23:
            continue
        n = int(q[5])
        if n == 1:
            continue
        pq = f"{q[:4]}.{n - 1}Q"
        a, b, p23 = v.get((c, 22, q)), v.get((c, 24, q)), v.get((c, 23, pq))
        if a is None or b is None or p23 is None:
            continue
        if abs(a - b) <= 5e-7 and abs(p23) > 0:
            out.append((c, q, a, b, p23))
    return sorted(out)


SIM = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e23_kr0072_sim")   # byte-identical to what --apply wrote (c18_sim_vs_applied.txt)
for tag, p in (("PRE-LOAD (backup = reverted tree)", BK / "PL_breakdown.json"), ("POST-LOAD (--out-dir simulation = the applied masters)", SIM / "PL_breakdown.json")):
    r = cands(p)
    print(f"{tag}: {len(r)} cells where 22 == 24 (recomputed item 23 would be exactly 0.0) and the previous quarter's item 23 is non-zero:")
    for x in r:
        print("    ", x)
