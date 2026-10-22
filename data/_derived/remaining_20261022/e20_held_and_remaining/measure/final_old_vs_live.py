"""final_old_vs_live: for every candidate cell (all scenarios) compare the recorded `old` (start snapshot) with the CURRENT live master (HEAD after STEP 1).  READ-ONLY -> final_old_vs_live.txt"""
import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
pl = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r["값"] for r in M.jload(M.ROOT / "PL_breakdown.json")}
cs = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r["값"] for r in M.jload(M.ROOT / "CSM_waterfall.json")}
out, tot, bad = [], 0, 0
for scn in ("R0_KBlife_2024Q1_fix", "R1", "R1b_KB_siblings", "R2", "R2b_Lotte_2023_1Q2Q", "N1_KBlife_A", "N4_ABL_FY2023", "N5_KDB_FY2023", "N6c_HD_FY2023_IRlegs", "N7_Lotte_FY2023Q4"):
    d = json.loads((M.MEASURE / f"cands_{scn}.json").read_text(encoding="utf-8"))
    for kind, cells, live in (("PL", d["pl_cells"], pl), ("CSM", d["csm_cells"], cs)):
        n = b = 0
        for c in cells:
            lv = live.get((c["code"], c["q"], str(c["item"])))
            n += 1
            same = (lv is None and c["old"] is None) or (lv is not None and c["old"] is not None and abs(lv - c["old"]) < 1e-6)
            if not same:
                b += 1
                out.append(f"  DIFF {scn} {kind} {c['code']} {c['q']} item{c['item']}: snapshot-old={c['old']} live={lv} candidate-new={c['new']}")
        tot += n
        bad += b
        out.append(f"{scn:<24} {kind:<3} cells={n:4d} old==live: {n - b:4d}  differ: {b}")
out.append(f"TOTAL cells {tot}  differ {bad}")
M.MEASURE.joinpath("final_old_vs_live.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out)[:6000])
