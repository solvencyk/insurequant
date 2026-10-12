# -*- coding: utf-8 -*-
"""x4: before/after of the published utilization JSONs (before2/ = state at the start of this round, root = now).
Lists every changed field per company, the full tier1 utilization and the tier1_overflow_into_tier2_eok table.
Output: x4_before_after.txt, x4_overflow_47.csv
Run (repo root): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capsec_reinstate_20261012/x4_before_after.py
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.stdout.reconfigure(encoding="utf-8")


def load(p):
    return {r["code"]: r for r in json.loads(p.read_text(encoding="utf-8"))["results"]}


def main():
    L = []
    for name in ("kics_tier1_utilization.json", "kics_tier2_utilization.json"):
        b, a = load(HERE / "before2" / name), load(ROOT / name)
        L.append(f"== {name}: changed fields")
        n = 0
        for code in a:
            for k in sorted(set(a[code]) | set(b.get(code, {}))):
                if a[code].get(k) != b.get(code, {}).get(k):
                    n += 1
                    L.append(f"  {code} {a[code]['company']} {k}: {b.get(code, {}).get(k)!r:.120} -> {a[code].get(k)!r:.120}")
        L.append(f"  (total {n} field changes)")
    t1b, t1a = load(HERE / "before2" / "kics_tier1_utilization.json"), load(ROOT / "kics_tier1_utilization.json")
    t2b, t2a = load(HERE / "before2" / "kics_tier2_utilization.json"), load(ROOT / "kics_tier2_utilization.json")
    L.append("\n== tier1 utilization_pct before -> after (47 companies; changed marked *)")
    for code in t1a:
        mark = "*" if t1b[code].get("utilization_pct") != t1a[code].get("utilization_pct") else " "
        L.append(f" {mark} {code} {t1a[code]['company'][:10]:12s} {t1b[code].get('utilization_pct')} -> {t1a[code].get('utilization_pct')}")
    L.append("\n== tier2 utilization_pct / numerator before -> after: changed rows")
    ch = [c for c in t2a if (t2b[c].get("utilization_pct"), t2b[c].get("numerator_eok")) != (t2a[c].get("utilization_pct"), t2a[c].get("numerator_eok"))]
    L.append("  " + (", ".join(ch) if ch else "none (tier2 unchanged for all 47)"))
    rows = []
    for code in t2a:
        rows.append(dict(code=code, company=t2a[code]["company"], overflow_before=t2b[code].get("tier1_overflow_into_tier2_eok"),
                         overflow_after=t2a[code].get("tier1_overflow_into_tier2_eok"),
                         tier1_json_overflow=t1a[code].get("tier1_hybrid_overflow_eok"),
                         tier2_numerator=t2a[code].get("numerator_eok"), tier2_rule=t2a[code].get("rule")))
    with open(HERE / "x4_overflow_47.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    L.append("\n== tier1_overflow_into_tier2_eok before -> after (rows that differ or are non-zero)")
    for r in rows:
        if r["overflow_before"] != r["overflow_after"] or (r["overflow_after"] or 0) != 0:
            L.append(f"  {r['code']} {r['company'][:10]:12s} {r['overflow_before']} -> {r['overflow_after']}  (tier1 json overflow {r['tier1_json_overflow']}; tier2 numerator {r['tier2_numerator']}, rule {r['tier2_rule']})")
    bad = [r["code"] for r in rows if r["overflow_after"] != r["tier1_json_overflow"]]
    L.append(f"\nconsistency tier2 field == tier1 json tier1_hybrid_overflow_eok for all 47: {'OK' if not bad else 'MISMATCH ' + str(bad)}")
    (HERE / "x4_before_after.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
