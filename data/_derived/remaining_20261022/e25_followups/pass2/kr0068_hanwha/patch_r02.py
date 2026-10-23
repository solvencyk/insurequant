# -*- coding: utf-8 -*-
import io
p = "r02_hw_read.py"
s = io.open(p, encoding="utf-8").read()

# 1) optional reinsurance rows (the annual prior table carries no 재보험 sections)
old = """    ract = find(rr, "re_rev", "발생재보험금및재보험서비스비용회수액")
    rexp = find(rr, "re_cost", "회수예상보험금및보험서비스비용")
    rera = find(rr, "re_cost", "위험해제로인한위험조정의변동")
    recsm = find(rr, "re_cost", "제공받은서비스의재보험계약마진")
    rec["rows"] = {k: x for k, x in dict(csm=csm, ra=ra, exp=exp, cact=cact, ract=ract, rexp=rexp, rera=rera, recsm=recsm).items()}
    A = lambda x: abs(x["cum"]["v"])  # noqa: E731
    it = {4: A(csm), 5: A(ra), 6: A(exp) - A(cact), 9: -A(recsm), 10: -A(rera), 11: A(ract) - A(rexp)}
    rec["items"] = it
    if pair:
        A3 = lambda x: abs(x["m3"]["v"])  # noqa: E731
        rec["items_3m"] = {4: A3(csm), 5: A3(ra), 6: A3(exp) - A3(cact), 9: -A3(recsm), 10: -A3(rera), 11: A3(ract) - A3(rexp)}
"""
new = """    has_re = any(x["sec"] == "re_rev" for x in rr)
    if has_re:
        ract = find(rr, "re_rev", "발생재보험금및재보험서비스비용회수액")
        rexp = find(rr, "re_cost", "회수예상보험금및보험서비스비용")
        rera = find(rr, "re_cost", "위험해제로인한위험조정의변동")
        recsm = find(rr, "re_cost", "제공받은서비스의재보험계약마진")
    rows_ = dict(csm=csm, ra=ra, exp=exp, cact=cact)
    if has_re:
        rows_.update(ract=ract, rexp=rexp, rera=rera, recsm=recsm)
    rec["rows"] = rows_
    A = lambda x: abs(x["cum"]["v"])  # noqa: E731
    it = {4: A(csm), 5: A(ra), 6: A(exp) - A(cact)}
    if has_re:
        it.update({9: -A(recsm), 10: -A(rera), 11: A(ract) - A(rexp)})
    rec["items"] = it
    if pair:
        A3 = lambda x: abs(x["m3"]["v"])  # noqa: E731
        rec["items_3m"] = {4: A3(csm), 5: A3(ra), 6: A3(exp) - A3(cact)}
        if has_re:
            rec["items_3m"].update({9: -A3(recsm), 10: -A3(rera), 11: A3(ract) - A3(rexp)})
"""
assert s.count(old) == 1
s = s.replace(old, new)

old2 = """    i3_note = sums["rev"]["total"] - sums["cost"]["total"]
    i8_note = sums["re_rev"]["total"] - sums["re_cost"]["total"]
"""
new2 = """    i3_note = sums["rev"]["total"] - sums["cost"]["total"]
    i8_note = (sums["re_rev"]["total"] - sums["re_cost"]["total"]) if has_re else None
"""
assert s.count(old2) == 1
s = s.replace(old2, new2)

old3 = """    i12 = m[8] - (it[9] + it[10] + it[11])
    rec["items"]["7"], rec["items"]["12"] = i7, i12"""
new3 = """    i12 = (m[8] - (it[9] + it[10] + it[11])) if has_re else None
    rec["items"]["7"], rec["items"]["12"] = i7, i12"""
assert s.count(old3) == 1
s = s.replace(old3, new3)

old4 = """    rr_other = [x for x in rr if x["sec"] == "re_rev" and x["norm"] not in ("소계",) and not x["norm"].startswith("총") and x is not ract]
    rc_other = [x for x in rr if x["sec"] == "re_cost" and x["norm"] not in ("소계",) and not x["norm"].startswith("총") and x not in (rexp, rera, recsm)]
    other12 = sum(x["cum"]["v"] for x in rr_other) - sum(x["cum"]["v"] for x in rc_other)
    rec["closure7"] = dict(rev_other=[x["label"] for x in rev_other], cost_other=[x["label"] for x in cost_other], value=other7, derived=i7, diff=i7 - other7)
    rec["closure12"] = dict(rr_other=[x["label"] for x in rr_other], rc_other=[x["label"] for x in rc_other], value=other12, derived=i12, diff=i12 - other12)"""
new4 = """    rec["closure7"] = dict(rev_other=[x["label"] for x in rev_other], cost_other=[x["label"] for x in cost_other], value=other7, derived=i7, diff=i7 - other7)
    if pair:
        o3 = sum(x["m3"]["v"] for x in rev_other) - sum(x["m3"]["v"] for x in cost_other)
        rec["other7_3m"] = o3
    if has_re:
        rr_other = [x for x in rr if x["sec"] == "re_rev" and x["norm"] not in ("소계",) and not x["norm"].startswith("총") and x is not ract]
        rc_other = [x for x in rr if x["sec"] == "re_cost" and x["norm"] not in ("소계",) and not x["norm"].startswith("총") and x not in (rexp, rera, recsm)]
        other12 = sum(x["cum"]["v"] for x in rr_other) - sum(x["cum"]["v"] for x in rc_other)
        rec["closure12"] = dict(rr_other=[x["label"] for x in rr_other], rc_other=[x["label"] for x in rc_other], value=other12, derived=i12, diff=i12 - other12)
        if pair:
            rec["other12_3m"] = sum(x["m3"]["v"] for x in rr_other) - sum(x["m3"]["v"] for x in rc_other)"""
assert s.count(old4) == 1
s = s.replace(old4, new4)

old5 = """    PR(f"  3: master {m[3]} vs note 총수익-총비용 {i3_note:,.0f}; 8: master {m[8]} vs note {i8_note:,.0f}")
    PR(f"  derived 7 = {i7:,.3f} vs other-rows {other7:,.0f} (diff {i7 - other7:+.3f}); derived 12 = {i12:,.3f} vs other-rows {other12:,.0f} (diff {i12 - other12:+.3f})")
    if pair:
        PR("  3M (합계 3개월): " + " ".join(f"{k}={v:,.0f}" for k, v in rec["items_3m"].items()))"""
new5 = """    PR(f"  3: master {m[3]} vs note 총수익-총비용 {i3_note:,.0f}; 8: master {m[8]} vs note {i8_note}")
    PR(f"  derived 7 = {i7:,.3f} vs other-rows {other7:,.0f} (diff {i7 - other7:+.3f})" + (f"; derived 12 = {i12:,.3f} vs other-rows {rec['closure12']['value']:,.0f} (diff {rec['closure12']['diff']:+.3f})" if has_re else "; (no 재보험 sections in this table)"))
    if pair:
        PR("  3M (합계 3개월): " + " ".join(f"{k}={v:,.0f}" for k, v in rec["items_3m"].items()) + f" | other7_3m={rec['other7_3m']:,.0f}" + (f" other12_3m={rec['other12_3m']:,.0f}" if has_re else ""))"""
assert s.count(old5) == 1
s = s.replace(old5, new5)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
