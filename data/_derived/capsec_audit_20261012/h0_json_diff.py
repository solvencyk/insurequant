# -*- coding: utf-8 -*-
"""h0b: field-level diff of kics_tier1_utilization.json / kics_tier2_utilization.json between the old pin (dbbffcb5) and the new pin.  Output h0_json_diff_<newrev>.txt"""
import sys
from collections import Counter, defaultdict

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

OLD = "dbbffcb5"
NEW = audit_io.resolved_rev()
L = []
for fn in ("kics_tier1_utilization.json", "kics_tier2_utilization.json"):
    o = {r["code"]: r for r in audit_io.load_json(fn, OLD)["results"]}
    n = {r["code"]: r for r in audit_io.load_json(fn, NEW)["results"]}
    L.append("== %s : %d -> %d companies" % (fn, len(o), len(n)))
    fields = Counter()
    pct = []
    for c in sorted(n):
        keys = set(o[c]) | set(n[c])
        ch = [k for k in sorted(keys) if o[c].get(k) != n[c].get(k)]
        for k in ch:
            fields[k] += 1
        if o[c].get("utilization_pct") != n[c].get("utilization_pct"):
            pct.append((c, n[c]["company"], o[c].get("utilization_pct"), n[c].get("utilization_pct")))
    L.append("   changed fields (count of companies): " + ", ".join("%s:%d" % kv for kv in sorted(fields.items())))
    L.append("   utilization_pct changed for %d companies:" % len(pct))
    for x in pct:
        L.append("      %s %s %s -> %s" % x)
open(HERE + "h0_json_diff_%s.txt" % NEW, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
