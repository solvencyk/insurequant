import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
live = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r["값"] for r in M.jload(M.ROOT / "PL_breakdown.json")}
snap = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r["값"] for r in M.jload(M.SNAP / "PL_breakdown.json")}
d = json.loads((M.MEASURE / "cands_R1.json").read_text(encoding="utf-8"))
for c in d["pl_cells"]:
    if c["code"] == "KR0083":
        k = (c["code"], c["q"], str(c["item"]))
        print(f"item {c['item']:>2} snapshot={snap.get(k)} live={live.get(k)} e20-candidate={c['new']}  same_as_live={abs((live.get(k) or 0) - c['new']) < 1e-6}")
