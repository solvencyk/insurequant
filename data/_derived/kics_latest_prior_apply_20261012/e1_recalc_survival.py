"""e1: does the standard derived-fill step (scripts/recalc_kics_derived.recalc) keep the new values?  (READ-ONLY, in memory only)

candidate = live master + all 16 plans.  recalc(candidate) is run on a deep copy; every cell that recalc changes is listed and the touched
(code, quarter) buckets are checked cell by cell against the planned new values.  The same recalc on the live master gives the baseline
noise (cells recalc already moves today, unrelated to this ticket).  Also checks the held KR0070_2024.3Q item 22 case.
"""
import copy
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
import recalc_kics_derived as rk  # noqa: E402

rows = read_rows()
plans = merge_plans(APPLIED)
cand = copy.deepcopy(rows)
n = apply_to_rows(cand, plans["edits"])
print("candidate built, cells", n)


def cellmap(rs):
    return {(r["원보험사코드"], r["공시분기"], r["항목번호"]): (r.get("값"), r.get("값_적용후", "<nokey>")) for r in rs}


def run_recalc(rs):
    c = copy.deepcopy(rs)
    stats = rk.recalc(c)
    return c, stats


base_after, base_stats = run_recalc(rows)
cand_after, cand_stats = run_recalc(cand)
print("recalc stats live:", base_stats)
print("recalc stats cand:", cand_stats)
b0, b1 = cellmap(rows), cellmap(base_after)
c0, c1 = cellmap(cand), cellmap(cand_after)
base_moves = {k for k in b0 if b0[k] != b1.get(k)}
cand_moves = {k for k in c0 if c0[k] != c1.get(k)}
print("cells recalc moves on live master:", len(base_moves), "| on candidate:", len(cand_moves))
new_moves = cand_moves - base_moves
print("cells recalc moves ONLY on the candidate (would revert / alter ticket cells):", len(new_moves))
planned = {(e["code"], e["q"], e["item"]) for e in plans["edits"]}
touched_buckets = {(e["code"], e["q"]) for e in plans["edits"]}
for k in sorted(new_moves):
    print("   ", k, c0[k], "->", c1[k], "| planned cell" if k in planned else "")
# the 16 buckets: any recalc move at all inside a touched bucket (even if also moved on live)?
inside = sorted(k for k in cand_moves if (k[0], k[1]) in touched_buckets)
print("recalc moves inside the 16 touched buckets (candidate):", len(inside))
for k in inside:
    print("   ", k, c0[k], "->", c1[k], "| also moved on live" if k in base_moves else "")
# planned cells whose new value survives recalc
lost = []
for e in plans["edits"]:
    k = (e["code"], e["q"], e["item"])
    val = c1.get(k)
    idx = 0 if e["field"] == "값" else 1
    if val is None or val[idx] != e["new"]:
        lost.append((k, e["field"], e["new"], None if val is None else val[idx]))
print("planned cells NOT surviving recalc:", len(lost))
for x in lost:
    print("   ", x)

# ---- the held block KR0070_2024.3Q item 22 (0 -> 1): would recalc zero it again?
hold = copy.deepcopy(rows)
for r in hold:
    if (r["원보험사코드"], r["공시분기"], r["항목번호"]) == ("KR0070", "2024.3Q", 22):
        r["값"] = "1"
        r["값_적용후"] = "1"
h_after, _ = run_recalc(hold)
for r in h_after:
    if (r["원보험사코드"], r["공시분기"], r["항목번호"]) == ("KR0070", "2024.3Q", 22):
        print("KR0070 2024.3Q item22 after recalc, starting from 1:", r["값"], "(post", r.get("값_적용후"), ")")
