# -*- coding: utf-8 -*-
"""h1h: what changed between the previous audited state (rev OLD, default 6fd00720) and the new pin?  Expectation after the call-date correction:
only 메리츠 (30.8 -> 37.5), 아이엠라이프 (56.9 -> 70.4) and KB라이프 (0.0 -> 0.8) change in kics_tier2_utilization.json; tier1 JSON, forward JSON, timeline JSON, ledger and master are identical.
Compares (a) my recompute files of both pins (h1_*_<rev>.json), (b) the published tier2 JSON field by field, (c) the other audited artifacts byte-wise at both pins.
Output h1h_delta_vs_previous_<newrev>.txt"""
import json
import os
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

OLD = os.environ.get("AUDIT_OLD", "6fd00720")
NEW = audit_io.resolved_rev()
L = ["old pin %s -> new pin %s" % (OLD, NEW)]
mo = {x["code"]: x for x in json.load(open(HERE + "h1_tier2_recompute_47_%s.json" % OLD, encoding="utf-8"))}
mn = {x["code"]: x for x in json.load(open(HERE + "h1_tier2_recompute_47_%s.json" % NEW, encoding="utf-8"))}
chg_mine = [(c, mn[c]["name"], mo[c]["pct_mine"], mn[c]["pct_mine"]) for c in sorted(mn) if mo[c]["pct_mine"] != mn[c]["pct_mine"]]
chg_pub = [(c, mn[c]["name"], mo[c]["pct_pub"], mn[c]["pct_pub"]) for c in sorted(mn) if mo[c]["pct_pub"] != mn[c]["pct_pub"]]
L.append("my recompute (old pin = flag rule, new pin = call-date rule): pct changed for %d companies: %s" % (len(chg_mine), chg_mine))
L.append("published utilization_pct changed for %d companies: %s" % (len(chg_pub), chg_pub))
L.append("the two lists name the same companies with the same values: %s" % (sorted((c, round(b, 1)) for c, _, a, b in chg_mine) == sorted((c, b) for c, _, a, b in chg_pub)))
unchanged47 = len(mn) - len(chg_pub)
L.append("companies with unchanged published utilization: %d of %d" % (unchanged47, len(mn)))
# field-level diff of the published tier2 JSON
o2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json", OLD)["results"]}
n2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json", NEW)["results"]}
from collections import Counter
fields = Counter()
per_company = {}
for c in sorted(n2):
    ch = [k for k in sorted(set(o2[c]) | set(n2[c])) if o2[c].get(k) != n2[c].get(k)]
    if ch:
        per_company[c] = ch
    for k in ch:
        fields[k] += 1
L.append("tier2 JSON: companies with any changed field: %d %s" % (len(per_company), sorted(per_company)))
L.append("   changed fields (count of companies): " + ", ".join("%s:%d" % kv for kv in sorted(fields.items())))
for c, ch in per_company.items():
    L.append("   %s %s: %s" % (c, n2[c]["company"], ", ".join("%s %s -> %s" % (k, str(o2[c].get(k))[:40], str(n2[c].get(k))[:40]) for k in ch if k not in ("rule_flags", "numerator_source", "rule_basis"))))
# top-level (definition / count) block
a = {k: v for k, v in audit_io.load_json("kics_tier2_utilization.json", OLD).items() if k != "results"}
b = {k: v for k, v in audit_io.load_json("kics_tier2_utilization.json", NEW).items() if k != "results"}
L.append("tier2 JSON top-level block (definition text etc.) changed: %s" % (a != b))
if a != b:
    for k in sorted(set(a) | set(b)):
        if a.get(k) != b.get(k):
            L.append("   top-level key %s differs: old %s ... new %s" % (k, str(a.get(k))[:200], str(b.get(k))[:200]))
# byte-wise identity of the other audited artifacts
same = {}
for rel in ("kics_tier1_utilization.json", "kics_forward_capital.json", "kics_capital_securities_timeline.json", "data/bonds/capital_securities_fy2026h1.json",
            "data/bonds/capital_tier_registry.json", "kics_disclosure.json", "K-ICS.html", "theme.js", "download-survey.js", "report-widget.js", "kics_capital_securities.json"):
    try:
        same[rel] = audit_io.blob_bytes(rel, OLD) == audit_io.blob_bytes(rel, NEW)
    except Exception as exc:  # noqa: BLE001
        same[rel] = "n/a (%s)" % type(exc).__name__
L.append("byte-identical between the pins: " + ", ".join("%s=%s" % kv for kv in same.items()))
open(HERE + "h1h_delta_vs_previous_%s.txt" % NEW, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
