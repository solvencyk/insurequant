"""p_hanwha: prototype of the Tier-2 PRIOR-column reader for 한화생명 (KR0068; OLD-life layout 1: 합계 = last numeric of the row; current table first, 전기/전분기 twin second).
prior variant = pick the SECOND matching table (production picks the first).  Production helpers unchanged.  READ-ONLY.  usage: p_hanwha.py <quarters csv>"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import prod as P  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
C = P.C


def layout1(tables, nth):
    pool_all = C._prefer_ofs(tables)
    rc = [t for t in pool_all if C._oll_l1_is(t)]
    pool = [t for t in rc if C._oll_l1_pure(t)] or rc
    revs = [t for t in pool if C._oll_l1_hassec(t, "보험수익")]
    res_ = [t for t in pool if C._oll_l1_hassec(t, "재보험수익")]
    out = {}
    rev_t = revs[nth] if len(revs) > nth else None
    re_t = res_[nth] if len(res_) > nth else None
    if rev_t is not None:
        d = C._oll_l1_collect(rev_t)
        if "csm" in d:
            out[4] = abs(d["csm"])
        if "ra" in d:
            out[5] = abs(d["ra"])
        if "exp" in d and "cact" in d:
            out[6] = abs(d["exp"]) - abs(d["cact"])
    if re_t is not None:
        d = C._oll_l1_collect(re_t)
        if "recsm" in d:
            out[9] = -abs(d["recsm"])
        if "rera" in d:
            out[10] = -abs(d["rera"])
        if "ract" in d and "rexp" in d:
            out[11] = abs(d["ract"]) - abs(d["rexp"])
    return out, [revs[nth].line_no if len(revs) > nth else None, res_[nth].line_no if len(res_) > nth else None], (len(revs), len(res_))


pl, names, inames = M.load_pl()
res, txt = {}, []
for q in sys.argv[1].split(","):
    m = pl[("KR0068", q)]
    tabs = P.tables_for("KR0068", M.later_fy(q))
    cur, lc, nc = layout1(tabs, 0)
    pri, lp, nc2 = layout1(tabs, 1)
    del tabs
    res[q] = {"master": {str(k): m.get(k) for k in (4, 5, 6, 9, 10, 11)}, "later_cur": cur, "later_prior": pri, "lines": [lc, lp], "n_tables": nc}
    txt.append(f"KR0068 {q}: master 4/5/6/9/10/11={[m.get(k) for k in (4, 5, 6, 9, 10, 11)]} | later cur {cur} L{lc} | later PRIOR(2nd table) {pri} L{lp}  (#rev/#re tables={nc})")
M.MEASURE.joinpath("p_hanwha.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("p_hanwha.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
