"""s2c_core_completeness.py -- step 2c (READ-ONLY).  Population-level completeness of the CORE block (items 1..23) in the latest filing's printed column.

For every (company, quarter Q) with at least one later filing: which filing/column is the latest, was it readable, and does it print a number for
every master item 1..23 that is non-zero in the master (a dash is only acceptable where the master is 0).  Also records the same for the
NEXT filing's 직전 column only (F(Q+1).prev) -- the literal reading of "the prior column of the next disclosure".
Output: core_completeness.json (one record per block) and core_completeness_summary.txt
"""
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402

utf8_stdout()
rows = read_rows()
midx, names = master_index(rows)
codes = sorted(names)


def load(period, code):
    f = CACHE / f"core_{period}_{code}.json"
    return read_json(f) if f.exists() else None


def printed(rec, c):
    """-> ({item:(val)} printed numbers, {item} mapped-but-blank) or None if the filing is not usable"""
    if not rec or rec["status"] not in ("OK", "VISION_ONLY"):
        return None
    d = rec["cols"].get(c)
    if not d:
        return None
    nums = {int(k): v[0] for k, v in d.items() if v[0] is not None}
    blanks = {int(k) for k, v in d.items() if v[0] is None}
    return nums, blanks


def completeness(code, q, rec, col):
    m = midx[(code, q)]
    pr = printed(rec, col)
    if pr is None:
        return {"readable": False, "status": rec["status"] if rec else "NO_REC", "missing_items": None, "master_nonzero": None}
    nums, blanks = pr
    need = [it for it in range(1, 24) if it in m and num(m[it][0]) is not None and abs(num(m[it][0])) >= 0.5]
    missing = [it for it in need if it not in nums]
    return {"readable": True, "status": "OK", "master_nonzero": len(need), "missing_items": missing, "complete": not missing}


out = []
for code in codes:
    for q in QUARTERS[:-1]:
        if (code, q) not in midx:
            continue
        q1, q2 = qadd(q, 1), qadd(q, 2)
        r1 = load(period_of(q1), code) if q1 else None
        r2 = load(period_of(q2), code) if q2 else None
        rec = {"code": code, "name": names[code], "quarter": q, "even": is_even(q), "applier": None}
        rec["next"] = completeness(code, q, r1, "prev") if q1 else None            # F(Q+1).직전분기
        rec["next2"] = completeness(code, q, r2, "prev2") if q2 else None          # F(Q+2).전전분기
        # latest = F(Q+2) if readable else F(Q+1)
        if rec["next2"] and rec["next2"]["readable"]:
            rec["latest"], rec["latest_label"] = rec["next2"], "F(Q+2).전전분기"
        elif rec["next"] and rec["next"]["readable"]:
            rec["latest"], rec["latest_label"] = rec["next"], "F(Q+1).직전분기"
        else:
            rec["latest"], rec["latest_label"] = None, None
        out.append(rec)

write_json_lf(OUT / "core_completeness.json", out)
lines = []
for kind, sel in (("odd (1Q/3Q)", lambda r: not r["even"]), ("even (2Q/4Q)", lambda r: r["even"])):
    for lab in ("latest", "next"):
        blocks = [r for r in out if sel(r)]
        if lab == "next":
            blocks = [r for r in blocks if r["next"] is not None]
        tot = len(blocks)
        read = [r for r in blocks if (r[lab] or {}).get("readable")]
        comp = [r for r in read if r[lab].get("complete")]
        lines.append(f"{kind:13s} column={lab:6s} blocks={tot:3d} readable={len(read):3d} complete-core={len(comp):3d} "
                     f"({100*len(comp)/max(1,len(read)):.1f}% of readable, {100*len(comp)/max(1,tot):.1f}% of all)")
bq = defaultdict(Counter)
for r in out:
    L = r["latest"]
    key = "UNREADABLE" if not L else ("COMPLETE" if L.get("complete") else "CORE_GAP")
    bq[r["quarter"]][key] += 1
lines.append("")
for q in QUARTERS[:-1]:
    lines.append(f"{q}  {dict(bq[q])}")
gaps = [(r["code"], r["quarter"], r["latest"]["missing_items"]) for r in out if r["latest"] and not r["latest"].get("complete")]
lines.append("\ncore gaps (latest readable but missing master-nonzero items): " + str(len(gaps)))
for g in gaps[:60]:
    lines.append("  " + str(g))
(OUT / "core_completeness_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
