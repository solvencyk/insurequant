# -*- coding: utf-8 -*-
"""e9: the issuance panel reads kics_capital_securities_timeline.json; its source is the bond ledger data/bonds/capital_securities_fy2026h1.json.
Re-derive the timeline from the ledger (pinned revision) and compare bond by bond:
   every ledger bond with an issue_date  -> one timeline row (tier, issue_date, call_date, coupon_pct, face_eok = face_amount_mn / 100,
   outstanding_eok = outstanding_mn / 100, as_of); bonds without an issue_date are excluded (as the file's source line says); redeemed bonds (outstanding 0) are included.
Also: companies that have ledger bonds but no timeline entry (the panel would show only dashes).   Output e9_timeline_vs_ledger_<rev>.txt"""
import sys
from collections import Counter

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
tl = audit_io.load_json("kics_capital_securities_timeline.json")["securities"]
led = {c["code"]: c for c in audit_io.load_json("data/bonds/capital_securities_fy2026h1.json")["companies"]}
L = ["PIN rev=%s timeline=%s ledger=%s" % (audit_io.resolved_rev(), audit_io.sha12("kics_capital_securities_timeline.json"), audit_io.sha12("data/bonds/capital_securities_fy2026h1.json"))]
bad = []
n_led_bonds = n_tl_rows = 0
no_tl = []
for code, c in sorted(led.items()):
    bonds = [b for b in c.get("bonds", []) if b.get("issue_date")]
    n_led_bonds += len(bonds)
    rows = tl.get(code, [])
    n_tl_rows += len(rows)
    if bonds and not rows:
        no_tl.append(code)
        continue
    want = Counter()
    for b in bonds:
        want[(b["tier"], b["issue_date"], b.get("call_date"), b.get("coupon_pct"), round((b.get("face_amount_mn") or 0) / 100.0, 4),
              round((b.get("outstanding_mn") or 0) / 100.0, 4), b.get("as_of"))] += 1
    got = Counter()
    for r in rows:
        got[(r["tier"], r["issue_date"], r.get("call_date"), r.get("coupon_pct"), round(float(r["face_eok"]), 4), round(float(r["outstanding_eok"]), 4), r.get("as_of"))] += 1
    if want != got:
        bad.append((code, c["company"], sorted((want - got).items()), sorted((got - want).items())))
L.append("ledger bonds with an issue_date: %d ; timeline rows: %d (companies in timeline: %d)" % (n_led_bonds, n_tl_rows, len(tl)))
L.append("companies with ledger bonds (issue_date present) but no timeline entry: %s" % (no_tl or "none"))
L.append("companies whose timeline rows differ from the ledger-derived rows: %d" % len(bad))
for b in bad:
    L.append("   %s %s | in ledger not in timeline: %s | in timeline not in ledger: %s" % b)
extra = sorted(set(tl) - set(led))
L.append("timeline companies not in ledger: %s" % (extra or "none"))
open(HERE + "e9_timeline_vs_ledger" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
