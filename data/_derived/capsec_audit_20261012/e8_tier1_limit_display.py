# -*- coding: utf-8 -*-
"""e8: which 인정한도 does the screen print under the tier1 donut (number line '기본자본 자본증권 X억원 / 인정한도 Y억원')?
The page prints kics_tier1_utilization.json tier1_hybrid_limit_eok.  The screen's subtitle (and definition_memo.md section 2) say: 10% of SCR is the rule,
15% only for grandfathered (기발행, item 53) hybrids.  List the companies where Y = 15% x SCR although item 53 = 0 (no grandfathered hybrid).
Independent: pinned JSON + my own dump of the master.   Output e8_tier1_limit_display_<rev>.txt"""
import json
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
rows = audit_io.load_json("kics_tier1_utilization.json")["results"]
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
L = ["PIN rev=%s tier1=%s" % (audit_io.resolved_rev(), audit_io.sha12("kics_tier1_utilization.json"))]
cnt = {}
off = []
for r in rows:
    cnt[r.get("binding_leg")] = cnt.get(r.get("binding_leg"), 0) + 1
    c = r["code"]
    scr = inp[c]["i14_pre"]
    l53 = inp[c].get("i53_pre") or 0.0
    lim = r.get("tier1_hybrid_limit_eok")
    if lim is not None and scr and abs(lim / scr - 0.15) < 0.002 and l53 == 0:
        off.append((c, r["company"], round(lim), round(0.10 * scr), r["utilization_pct"], r.get("binding_leg")))
L.append("binding_leg counts: %s" % cnt)
L.append("companies printing Y = 15%% x SCR with item 53 = 0 (no grandfathered hybrid): %d of %d  (the percentage is 0.0 for all of them, only the printed Y differs from the 10%% rule)" % (len(off), len(rows)))
for x in off:
    L.append("   %s %s | printed Y %d | 10%% x SCR would be %d | utilization %.1f | binding_leg %s" % x)
open(HERE + "e8_tier1_limit_display" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L[:6]))
