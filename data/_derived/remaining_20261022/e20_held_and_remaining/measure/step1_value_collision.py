import json, sys, glob
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
snap = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r["값"] for r in M.jload(M.SNAP / "PL_breakdown.json")}
live = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r["값"] for r in M.jload(M.ROOT / "PL_breakdown.json")}
chg = {k for k in snap if snap[k] != live.get(k) and not (snap[k] is not None and live.get(k) is not None and abs(snap[k] - live[k]) < 1e-9)}
print("STEP 1 VALUE (YTD) changes since snapshot:", len(chg), "buckets", len({(c, q) for c, q, i in chg}))
mine = set()
for p in glob.glob(str(M.MEASURE / "cands_*.json")):
    d = json.loads(open(p, encoding="utf-8").read())
    for c in d["pl_cells"]:
        mine.add((c["code"], c["q"], str(c["item"])))
print("collision (YTD value cells) with e20 candidates:", sorted(mine & chg))
print("STEP 1 touched YTD buckets:", sorted({(c, q) for c, q, i in chg}))
