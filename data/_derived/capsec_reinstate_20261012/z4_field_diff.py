# -*- coding: utf-8 -*-
"""Field-level diff of the deployed utilization JSONs (+forward) against before3/ snapshots, and the request-3 before/after table.
Writes z4_tier1_limit_before_after_47.csv (request 3: utilization_pct unchanged for all 47) and z4_field_diff.txt."""
import csv, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


out = []
b1 = {r["code"]: r for r in load(HERE / "before3/kics_tier1_utilization.json")["results"]}
a1 = {r["code"]: r for r in load(ROOT / "kics_tier1_utilization.json")["results"]}
assert b1.keys() == a1.keys() and len(a1) == 47
rows = []
bad_pct = []
for c in a1:
    b, a = b1[c], a1[c]
    if b["utilization_pct"] != a["utilization_pct"]:
        bad_pct.append(c)
    rows.append([c, a["company"], a.get("binding_leg"), b["utilization_pct"], a["utilization_pct"],
                 b["tier1_hybrid_limit_eok"], a["tier1_hybrid_limit_eok"], a["tier1_hybrid_limit_strict_eok"],
                 a["tier1_legacy_limit_eok"], b["tier1_hybrid_recognized_eok"], a["tier1_hybrid_recognized_eok"]])
with (HERE / "z4_tier1_limit_before_after_47.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["code", "company", "binding_leg", "util_before", "util_after", "printed_limit_before", "printed_limit_after",
                "limit_10pct", "limit_15pct", "recognized_before", "recognized_after"])
    w.writerows(rows)
out.append(f"tier1 utilization_pct changed for: {bad_pct} (must be [])")
chg = [r for r in rows if r[5] != r[6]]
out.append(f"tier1 printed limit changed for {len(chg)} companies; binding_leg of changed: {sorted(set(str(r[2]) for r in chg))}")
for r in chg[:3]:
    out.append(f"   e.g. {r[0]} {r[1]} {r[5]} -> {r[6]} (10% = {r[7]}, 15% = {r[8]})")
ok = all(r[6] == (r[7] if r[2] in (None, "basic_10") else r[8]) for r in rows)
out.append(f"after: printed limit == 10% for leg None/basic_10 and 15% for legacy_15, for all 47: {ok}")


def diff_doc(name, bpath, apath, key):
    b = {r[key]: r for r in load(bpath)["results" if key == "code" else None]} if key == "code" else None
    return b


for tier, f in (("tier1", "kics_tier1_utilization.json"), ("tier2", "kics_tier2_utilization.json")):
    bd, ad = load(HERE / "before3" / f), load(ROOT / f)
    bm = {r["code"]: r for r in bd["results"]}
    am = {r["code"]: r for r in ad["results"]}
    fields = {}
    for c in am:
        for k in set(am[c]) | set(bm[c]):
            if am[c].get(k) != bm[c].get(k):
                fields.setdefault(k, []).append(c)
    out.append(f"== {tier}: fields with changes (field: n companies)")
    for k, v in sorted(fields.items()):
        out.append(f"   {k}: {len(v)} {v[:8]}")
    top = {k: (bd.get(k) == ad.get(k)) for k in bd if k != "results"}
    out.append(f"   top-level changed keys: {[k for k, same in top.items() if not same]}")

# forward
bf = load(HERE / "before3/kics_forward_capital.json")
af = load(ROOT / "kics_forward_capital.json")
out.append(f"forward root file changed vs before3: {bf != af}")
(HERE / "z4_field_diff.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
