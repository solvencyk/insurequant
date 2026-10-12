"""e2: after the apply, run recalc_kics_derived.recalc on a deep copy of the LIVE master (in memory) and check the 65 ticket cells survive."""
import copy, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
from lib_apply import *  # noqa: F401,F403
utf8_stdout()
import recalc_kics_derived as rk
rows = read_rows()
after = copy.deepcopy(rows)
stats = rk.recalc(after)
plans = merge_plans(APPLIED)
cm = lambda rs: {(r["원보험사코드"], r["공시분기"], r["항목번호"]): (r.get("값"), r.get("값_적용후", "<nokey>")) for r in rs}
a, b = cm(rows), cm(after)
moves = {k for k in a if a[k] != b.get(k)}
touched = {(e["code"], e["q"]) for e in plans["edits"]}
inside = sorted(k for k in moves if (k[0], k[1]) in touched)
lost = [(e["code"], e["q"], e["item"], e["field"]) for e in plans["edits"]
        if b[(e["code"], e["q"], e["item"])][0 if e["field"] == "값" else 1] != e["new"]]
print("recalc stats:", {k: v for k, v in stats.items() if v})
print("cells recalc would move on the live master (all buckets):", len(moves), "| inside the 16 touched buckets:", len(inside), inside)
print("ticket cells that do NOT survive recalc:", len(lost), lost)
