"""a32_csm_test2: 롯데 / 미래에셋 CSM readers (+ 미래에셋 PL4) vs the READY candidates (READ-ONLY)"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_csm2 as C2  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(ROOT + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/cands_READY_all.json", encoding="utf-8").read())
csm = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(ROOT + "CSM_waterfall.json", encoding="utf-8").read())}
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(ROOT + "PL_breakdown.json", encoding="utf-8").read())}
cc = {(c["code"], c["q"], c["item"]): c["new"] for c in d["csm_cells"]}
cp = {(c["code"], c["q"], c["item"]): c["new"] for c in d["pl_cells"]}


def cmp_vec(code, q, res):
    print(f"== {code} {q}: exact={[round(x, 4) for x in res['vec_exact']]} 2dp={res['vec']} 1dp={res['vec1']} src={res['src']}")
    for i in range(1, 7):
        got2, got1 = res["vec"][i - 1], res["vec1"][i - 1]
        cand = cc.get((code, q, i))
        old = csm.get((code, i, q))
        ref = cand if cand is not None else old
        tag = "CAND" if cand is not None else "keep"
        ok2 = ref is not None and abs(got2 - ref) <= 0.0501
        ok1 = ref is not None and abs(got1 - ref) < 1e-6
        cl = res["cells"].get(i, [])
        print(f"   csm item{i} 2dp={got2} 1dp={got1} {tag}={ref} master={old} {'OK2' if ok2 else 'DIFF2'} {'OK1' if ok1 else 'DIFF1'}  n_cells={len(cl)} first={[(c['line'], c['printed']) for c in cl[:3]]}")
    if "check_group_row_5" in res:
        print("   group-row 현행서비스 CSM cell", res["check_group_row_5"], "== amort", res["cells"][5][0]["printed"])


for q in ("2023.1Q", "2024.1Q", "2024.2Q", "2024.3Q"):
    try:
        res = C2.lotte_csm(q)
    except Exception as e:  # noqa: BLE001
        print(f"== KR0003 {q}: ERROR {type(e).__name__}: {e}")
        continue
    cmp_vec("KR0003", q, res)
res = C2.mirae_q1()
cmp_vec("KR0079", "2024.1Q", res)
print("   PL4 (Q1 product tables, 합계 col sum) =", res["pl4_mn"], "| equal(CSM소계==합계) per table:", [p["equal"] for p in res["pl4_parts"]], "| master PL4", pl.get(("KR0079", 4, "2024.1Q")), "cand", cp.get(("KR0079", "2024.1Q", 4)))
for q in ("2024.2Q", "2024.3Q"):
    res = C2.mirae_wide(q)
    cmp_vec("KR0079", q, res)
    print("   PL4 wide-row sum =", res["pl4_mn"], "| non-CSM cells abs max per item:", res["non_csm_cells_abs_max"], "| master PL4", pl.get(("KR0079", 4, q)), "cand", cp.get(("KR0079", q, 4)))
