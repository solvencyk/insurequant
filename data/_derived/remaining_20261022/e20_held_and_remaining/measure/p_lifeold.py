"""p_lifeold: prototype of the Tier-2 PRIOR-column reader for the 'OLD life' note family (layout 2: 구분-row, period columns; used by 농협/흥국/KDB/푸본/ABL FY2023 quarters).
Change under test = ONE function: scripts.pl_breakdown.companies._oll_num picks ns[idx] (pair: 누적 = ns[1]; single: ns[0]); the prior variant picks the same cell one period block
to the right (pair: ns[3]; single: ns[1]).  Monkeypatched IN PROCESS ONLY (nothing is written).  Compared with the master legs of the same filing (fidelity) and the CSM prior amortisation.
usage: p_lifeold.py <code> <quarters csv>"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import prod as P  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
C = P.C
to_num = C.to_num
orig_num = C._oll_num


def prior_num(r, mi):
    mode, idx = mi
    ns = [to_num(c) for c in r if to_num(c) is not None]
    if not ns:
        return None
    if mode == "pair":
        return ns[3] if len(ns) > 3 else None
    return ns[1] if len(ns) > 1 else None


code = sys.argv[1]
qs = sys.argv[2].split(",")
pl, names, inames = M.load_pl()
res, txt = {}, []
for q in qs:
    m = pl[(code, q)]
    # fidelity: production reader on the original filing reproduces master 4/5/6/9/10/11 ?
    C._oll_num = orig_num
    tabs_o = P.tables_for(code, M.fy_of(q))
    o = C.extract_tier2_life_old(tabs_o)
    del tabs_o
    tabs_l = P.tables_for(code, M.later_fy(q))
    C._oll_num = orig_num
    cur = C.extract_tier2_life_old(tabs_l)
    C._oll_num = prior_num
    pri = C.extract_tier2_life_old(tabs_l)
    C._oll_num = orig_num
    del tabs_l
    res[q] = {"orig_run": o, "master": {str(k): m.get(k) for k in (4, 5, 6, 9, 10, 11)}, "later_current_col": cur, "later_prior_col": pri}
    txt.append(f"{code} {q}: master 4/5/6/9/10/11={[m.get(k) for k in (4, 5, 6, 9, 10, 11)]}\n    orig-filing run   {o}\n    later current col {cur}\n    later PRIOR col   {pri}")
M.MEASURE.joinpath(f"p_lifeold_{code}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath(f"p_lifeold_{code}.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
