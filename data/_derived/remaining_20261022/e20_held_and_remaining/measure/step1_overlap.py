"""step1_overlap: which (company, quarter) did the parallel STEP 1 apply change in the LIVE PL/CSM masters since my start snapshot, and does any e20 candidate cell collide with it? READ-ONLY"""
import json, sys
from collections import Counter
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
def idx(rows): return {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): (r["값"], r.get("값_당분기")) for r in rows}
snap_pl, live_pl = idx(M.jload(M.SNAP / "PL_breakdown.json")), idx(M.jload(M.ROOT / "PL_breakdown.json"))
snap_cs, live_cs = idx(M.jload(M.SNAP / "CSM_waterfall.json")), idx(M.jload(M.ROOT / "CSM_waterfall.json"))
chg_pl = {k for k in set(snap_pl) | set(live_pl) if snap_pl.get(k) != live_pl.get(k)}
chg_cs = {k for k in set(snap_cs) | set(live_cs) if snap_cs.get(k) != live_cs.get(k)}
print("STEP-1-side changes since snapshot: PL cells", len(chg_pl), "buckets", len({(c, q) for c, q, i in chg_pl}), "| CSM cells", len(chg_cs))
print("  PL buckets:", sorted({(c, q) for c, q, i in chg_pl}))
mine = set()
import glob
for p in glob.glob(str(M.MEASURE / "cands_*.json")):
    d = json.loads(open(p, encoding="utf-8").read())
    for c in d["pl_cells"]:
        mine.add((c["code"], c["q"], str(c["item"])))
inter = mine & chg_pl
print("collisions with e20 candidate PL cells:", len(inter), sorted(inter)[:20])
mine_b = {(c, q) for c, q, i in mine}
print("bucket-level overlap:", sorted(mine_b & {(c, q) for c, q, i in chg_pl}))
