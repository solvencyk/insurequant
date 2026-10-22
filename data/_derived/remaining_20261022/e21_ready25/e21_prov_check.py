"""e21_prov_check: provenance sidecar vs sandbox-emitter output for the target companies, at HEAD (before the apply) and now (READ-ONLY; the emitter writes only under the scratchpad)"""
import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_apply as A
import e21_plan_lib as P
sys.stdout.reconfigure(encoding="utf-8")
head_rows = P.head_json("PL_breakdown.json"); head_gold = P.head_json("data/_gold/user_pl_cells.json"); head_prov = P.head_json("PL_breakdown_provenance.json")
live_rows = A.load_json("PL_breakdown.json"); live_gold = A.load_json("data/_gold/user_pl_cells.json"); live_prov = A.load_json("PL_breakdown_provenance.json")
def diff_blocks(rows, gold, prov, tag):
    sub = [r for r in rows if r["원보험사코드"] in A.CODES]
    emit = A.run_emitter(sub, gold, tag)
    lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in prov["cells"] if c["company_code"] in A.CODES}
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit["cells"] if c["company_code"] in A.CODES}
    bad = sorted(k for k in set(lk) | set(ek) if lk.get(k) != ek.get(k))
    return bad, len(ek), len(lk)
b0, n0, l0 = diff_blocks(head_rows, head_gold, head_prov, "check_head")
b1, n1, l1 = diff_blocks(live_rows, live_gold, live_prov, "check_live")
print("HEAD : emitter blocks", n0, "sidecar blocks", l0, "differing", len(b0), b0)
print("LIVE : emitter blocks", n1, "sidecar blocks", l1, "differing", len(b1), b1)
print("differing now but not at HEAD:", sorted(set(b1) - set(b0)))
print("differing at HEAD but fixed now:", sorted(set(b0) - set(b1)))
