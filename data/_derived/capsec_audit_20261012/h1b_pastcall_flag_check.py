# -*- coding: utf-8 -*-
"""h1b: does the ledger flag past_call_outstanding agree with the call date at the numerator date 2026-06-30?
For every ledger bond with outstanding > 0 and issue_date <= 2022-12-31: flag vs (call_date < 2026-06-30) vs (call_date < the bond's own as_of).  Output h1b_pastcall_flag_check_<rev>.txt"""
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

REV = audit_io.resolved_rev()
led = audit_io.load_json("data/bonds/capital_securities_fy2026h1.json")["companies"]
L = ["PIN rev=%s ledger=%s" % (REV, audit_io.sha12("data/bonds/capital_securities_fy2026h1.json"))]
n = nflag = 0
rows = []
for c in led:
    for b in c.get("bonds", []):
        o = (b.get("outstanding_mn") or 0) / 100.0
        if o <= 0 or not b.get("issue_date") or b["issue_date"] > "2022-12-31":
            continue
        n += 1
        cd = b.get("call_date")
        flag = bool(b.get("past_call_outstanding"))
        nflag += flag
        by_numdate = bool(cd and cd < "2026-06-30")
        by_asof = bool(cd and cd < (b.get("as_of") or "9999"))
        rows.append((c["code"], c["company"], b["tier"], b["issue_date"], cd, b.get("call_source"), b.get("as_of"), round(o, 1), flag, by_asof, by_numdate))
L.append("pre-2023 bonds outstanding in the ledger: %d ; flagged past_call_outstanding: %d" % (n, nflag))
L.append("disagreements (flag != call_date < as_of of the bond)  [should be none]:")
for r in rows:
    if r[8] != r[9]:
        L.append("   FLAG-vs-ASOF %s %s %s issue %s call %s (%s) as_of %s out %s flag %s by_as_of %s by_numerator_date %s" % r)
L.append("disagreements (flag != call_date < 2026-06-30)  [matter for stale rows only]:")
for r in rows:
    if r[8] != r[10]:
        L.append("   FLAG-vs-2026-06-30 %s %s %s issue %s call %s (%s) as_of %s out %s flag %s by_as_of %s by_numerator_date %s" % r)
L.append("all flagged bonds:")
for r in rows:
    if r[8]:
        L.append("   %s %s %s issue %s call %s (%s) as_of %s out %s" % r[:8])
open(HERE + "h1b_pastcall_flag_check_%s.txt" % REV, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
