# -*- coding: utf-8 -*-
"""f1: audit of the call dates in the per-bond ledger (data/bonds/capital_securities_fy2026h1.json) that drive the Forward Outlook
call deductions and the 'next call' big cell.
For hybrids and subordinated bonds the standard Korean structure is 'call = issue date + 5 years' (후순위 10NC5, 신종 30/40/NC5).  Flag every bond with
outstanding amount whose call date is not issue + 5 years (+-3 days) together with the call_source, and show whether the flag changes the
screen's 'next call' cell or a Forward Outlook year-end.
Read-only; output f1_call_date_audit.txt / .csv
"""
import csv
import json
from datetime import date

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
doc = json.load(open(ROOT + "/data/bonds/capital_securities_fy2026h1.json", encoding="utf-8"))


def pd(s):
    if not s:
        return None
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d)


rows = []
for c in doc["companies"]:
    for b in c.get("bonds", []):
        out = (b.get("outstanding_mn") or 0) / 100.0
        i, k = pd(b.get("issue_date")), pd(b.get("call_date"))
        if out <= 0 or i is None or k is None:
            continue
        try:
            exp = date(i.year + 5, i.month, i.day)
        except ValueError:
            exp = date(i.year + 5, i.month, 28)
        diff = (k - exp).days
        if abs(diff) > 3:
            rows.append({"code": c["code"], "company": c.get("company"), "tier": b.get("tier"), "issue": b.get("issue_date"), "call": b.get("call_date"),
                         "expected_issue_plus5y": exp.isoformat(), "diff_days": diff, "call_source": b.get("call_source"), "outstanding_eok": round(out, 1),
                         "name": (b.get("name") or "")[:60]})
L = ["bonds with outstanding > 0 whose call date is not issue + 5y (+-3 days): %d" % len(rows)]
for r in rows:
    L.append("  %s %s %-12s issue %s call %s (expected %s, %+d days) src=%s out=%s | %s" % (
        r["code"], (r["company"] or "")[:6], r["tier"], r["issue"], r["call"], r["expected_issue_plus5y"], r["diff_days"], r["call_source"], r["outstanding_eok"], r["name"][:40]))
open(HERE + "f1_call_date_audit.txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
if rows:
    with open(HERE + "f1_call_date_audit.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
print("\n".join(L))
