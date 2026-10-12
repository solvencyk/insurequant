"""Read-only: cell-level diff of the dry-run recommended blocks against the LIVE masters (ticket 20261012T2230Z).

Inputs  : dry-run candidate sources (cand/csm_adopt_overlay.json, cand/pl_latest_blocks.json, cand/db_pl_block_lat.json, bs_4q_scan.csv)
Output  : plan_diff.json (all candidate edits with the live old value), printed summary.
Nothing in the repository is written.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DRY = ROOT / "data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012"

CSM_BLOCKS = ["KR0069|2023.2Q", "KR0082|2023.1Q", "KR0087|2023.1Q", "KR1000|2025.1Q", "KR0104|2023.1Q",
              "KR0008|2023.1Q", "KR0008|2023.2Q", "KR0008|2023.3Q", "KR0001|2023.3Q"]
PL_BLOCKS = ["KR0008|2023.1Q", "KR0008|2023.2Q", "KR0008|2023.3Q", "KR0001|2023.3Q",
             "KR0011|2023.1Q", "KR0011|2023.2Q", "KR0011|2023.3Q"]
BS_COND = {("KR0003", "2023.4Q"), ("KR0073", "2023.4Q")}


def jl(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


csm_live = jl(ROOT / "CSM_waterfall.json")
pl_live = jl(ROOT / "PL_breakdown.json")
bs_live = jl(ROOT / "IFRS17_BS.json")
cidx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in csm_live}
pidx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in pl_live}
bidx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in bs_live}

csm_ov = jl(DRY / "cand/csm_adopt_overlay.json")
plb = jl(DRY / "cand/pl_latest_blocks.json")
dbl = jl(DRY / "cand/db_pl_block_lat.json")

plan = {"CSM": [], "PL": [], "BS": [], "notes": []}

# ---------------- CSM
for key in CSM_BLOCKS:
    kr, q = key.split("|")
    v = csm_ov[key]
    for k, x in v.items():
        ck = (kr, int(k), q)
        cur = cidx[ck]["값"] if ck in cidx else None
        if x is None:
            continue
        if ck not in cidx:
            plan["notes"].append(f"CSM {key} item {k}: live row absent")
            continue
        if cur != x:
            plan["CSM"].append({"block": key, "code": kr, "quarter": q, "item": int(k), "old": cur, "new": x})


# ---------------- PL
def pl_block_for(key):
    kr, q = key.split("|")
    if kr == "KR0011" and q in dbl:
        return {int(k): v for k, v in dbl[q].items()}, "db_pl_block_lat.json"
    for suffix in ("sumcheck", "prod"):
        b = plb.get(f"{kr}|{q}|{suffix}")
        if b:
            return {int(k): v for k, v in b["block"].items()}, f"pl_latest_blocks.json[{suffix}]"
    return None, None


for key in PL_BLOCKS:
    kr, q = key.split("|")
    blk, src = pl_block_for(key)
    for it in range(1, 33):
        ck = (kr, it, q)
        lat = blk.get(it)
        row = pidx.get(ck)
        cur = row["값"] if row else None
        if lat is None:
            if cur is not None:
                plan["notes"].append(f"PL {key} item {it}: current {cur} absent in latest block (candidate would blank it) -> KEEP")
            continue
        if row is None:
            plan["PL"].append({"block": key, "code": kr, "quarter": q, "item": it, "old": None, "new": lat, "row_absent": True})
        elif cur != lat:
            plan["PL"].append({"block": key, "code": kr, "quarter": q, "item": it, "old": cur, "new": lat, "row_absent": False})

# ---------------- BS (year-end blocks, RESTATED_STALE rows of the 4Q scan with final adopt verdict)
bsv = list(csv.DictReader(open(DRY / "bs_block_verdicts.csv", encoding="utf-8-sig")))
final = {(r["kr"], r["quarter"]): r["verdict_final"] for r in bsv}
bscan = [r for r in csv.DictReader(open(DRY / "bs_4q_scan.csv", encoding="utf-8-sig")) if r["cls"] == "RESTATED_STALE"]
for r in bscan:
    k2 = (r["kr"], r["quarter"])
    if not final.get(k2, "").startswith("최신 채택"):
        continue
    if r["later"] in ("", "None"):
        continue
    ck = (r["kr"], int(r["item"]), r["quarter"])
    cur = bidx[ck]["값"] if ck in bidx else None
    nv = float(r["later"])
    if ck in bidx and cur != nv:
        plan["BS"].append({"block": f"{r['kr']}|{r['quarter']}", "code": r["kr"], "quarter": r["quarter"], "item": int(r["item"]),
                           "old": cur, "new": nv, "account": r["account"], "orig": r["orig"], "later_rcept": r["later_rcept"],
                           "later_file": r["later_file"]})

(HERE / "plan_diff.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
from collections import Counter

print("CSM cells", len(plan["CSM"]), dict(Counter(c["block"] for c in plan["CSM"])))
print("PL cells", len(plan["PL"]), dict(Counter(c["block"] for c in plan["PL"])))
print("   of which blank->value:", sum(1 for c in plan["PL"] if c["old"] is None))
print("BS cells", len(plan["BS"]), len({c['block'] for c in plan["BS"]}), "blocks")
for n in plan["notes"]:
    print("NOTE", n)
