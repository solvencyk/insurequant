"""a28_csm_test1: 한화 / 메리츠 CSM readers + 한화 PL4 note vs the READY candidates (READ-ONLY)"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_csm as C  # noqa: E402

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
        print(f"   csm item{i} 2dp={got2} 1dp={got1} {tag}={ref} master={old} {'OK2' if ok2 else 'DIFF2'} {'OK1' if ok1 else 'DIFF1'}  cells={[(c['line'], c['printed']) for c in res['cells'].get(i, [])]}")
    if "check_group_row_5" in res:
        g = res["check_group_row_5"]
        print("   group-row 현행서비스 CSM cell", g, "== amort sub-row", res["cells"][5][0]["printed"])


for q in ("2023.1Q", "2023.2Q", "2023.3Q"):
    res = C.hanwha_csm(q)
    cmp_vec("KR0068", q, res)
    p = C.hanwha_note_pl4(q)
    print(f"   PL4 note: {p['val_mn']} (printed {p['part']['printed']} @L{p['part']['line']} n_numeric={p['part']['n_numeric']}) current-table cell {p['current_cell']} | master PL4 {pl.get(('KR0068', 4, q))} cand {cp.get(('KR0068', q, 4))}")
for q in ("2023.1Q", "2023.2Q"):
    cmp_vec("KR0001", q, C.meritz_csm(q))
