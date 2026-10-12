# -*- coding: utf-8 -*-
"""e9: the issuance panel reads kics_capital_securities_timeline.json; its source is the bond ledger data/bonds/capital_securities_fy2026h1.json.
Re-derive the timeline from the ledger (pinned revision) and compare bond by bond.

Spec (2026-10-13 coordinator message + publishing/designer changelogs):
   every ledger bond with an issue_date and a non-zero face -> one timeline row: tier, issue_date, call_date, coupon_pct, face_eok = face_amount_mn / 100,
   outstanding_eok = outstanding_mn / 100, as_of ;  redeemed bonds (outstanding 0) are included ; bonds without an issue_date are excluded.
   Exceptions of the new state:
     - ledger call_date_unconfirmed = true (DB손해 제1·2회)  -> timeline outstanding_eok = null and call_date_unconfirmed = true (the screen then shows the date only)
     - ledger estimated = true (하나손해 2026-06-29 999억)    -> timeline row carries estimated = true (coupon / call null)
   Values are compared with a tolerance of 0.006 억 (the timeline is rounded to 2 decimals).
Also: companies that have ledger bonds but no timeline entry (the panel would show only dashes).
Output e9_timeline_vs_ledger_<rev>.txt"""
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

REV = audit_io.resolved_rev()
tl = audit_io.load_json("kics_capital_securities_timeline.json")["securities"]
led = {c["code"]: c for c in audit_io.load_json("data/bonds/capital_securities_fy2026h1.json")["companies"]}
L = ["PIN rev=%s timeline=%s ledger=%s" % (REV, audit_io.sha12("kics_capital_securities_timeline.json"), audit_io.sha12("data/bonds/capital_securities_fy2026h1.json"))]


def near(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= 0.006


def key_of(tier, issue, call, coupon):
    return (tier, issue, call, None if coupon is None else round(float(coupon), 4))


bad = []
n_led = n_tl = n_zero_face = 0
no_tl = []
flag_rows = []
for code, c in sorted(led.items()):
    bonds = [b for b in c.get("bonds", []) if b.get("issue_date")]
    zero = [b for b in bonds if not (b.get("face_amount_mn") or 0)]
    n_zero_face += len(zero)
    bonds = [b for b in bonds if (b.get("face_amount_mn") or 0)]
    n_led += len(bonds)
    rows = tl.get(code, [])
    n_tl += len(rows)
    if bonds and not rows:
        no_tl.append(code)
        continue
    want = {}
    for b in bonds:
        k = key_of(b["tier"], b["issue_date"], b.get("call_date"), b.get("coupon_pct"))
        out = None if b.get("call_date_unconfirmed") else (b.get("outstanding_mn") or 0) / 100.0
        want.setdefault(k, []).append({"face": (b.get("face_amount_mn") or 0) / 100.0, "out": out, "as_of": b.get("as_of"),
                                       "cdu": bool(b.get("call_date_unconfirmed")), "est": bool(b.get("estimated"))})
    got = {}
    for r in rows:
        k = key_of(r["tier"], r["issue_date"], r.get("call_date"), r.get("coupon_pct"))
        got.setdefault(k, []).append({"face": float(r["face_eok"]), "out": None if r.get("outstanding_eok") is None else float(r["outstanding_eok"]), "as_of": r.get("as_of"),
                                      "cdu": bool(r.get("call_date_unconfirmed")), "est": bool(r.get("estimated"))})
    probs = []
    for k in sorted(set(want) | set(got), key=str):
        w, g = want.get(k, []), got.get(k, [])
        if len(w) != len(g):
            probs.append((k, "count ledger %d / timeline %d" % (len(w), len(g))))
            continue
        for a, b in zip(sorted(w, key=lambda x: (x["face"], str(x["out"]))), sorted(g, key=lambda x: (x["face"], str(x["out"])))):
            if not (near(a["face"], b["face"]) and near(a["out"], b["out"]) and a["as_of"] == b["as_of"] and a["cdu"] == b["cdu"] and a["est"] == b["est"]):
                probs.append((k, "ledger %s / timeline %s" % (a, b)))
    for a in sum(want.values(), []):
        if a["cdu"] or a["est"]:
            flag_rows.append((code, c["company"], a))
    if probs:
        bad.append((code, c["company"], probs))
L.append("ledger bonds with an issue_date and a non-zero face: %d (zero-face bonds not listed by the timeline: %d) ; timeline rows: %d (companies in timeline: %d)" % (n_led, n_zero_face, n_tl, len(tl)))
L.append("companies with ledger bonds but no timeline entry: %s" % (no_tl or "none"))
L.append("companies whose timeline rows differ from the ledger-derived rows (face, outstanding, as_of, call_date_unconfirmed, estimated, within 0.006): %d" % len(bad))
for code, nm, probs in bad:
    for p in probs:
        L.append("   %s %s %s %s" % (code, nm, p[0], p[1]))
L.append("rows carrying the new markers (ledger side): %s" % [(c, n, a["face"], "call_date_unconfirmed" if a["cdu"] else "estimated") for c, n, a in flag_rows])
tl_markers = [(code, r["issue_date"], r["face_eok"], r.get("outstanding_eok"), "call_date_unconfirmed" if r.get("call_date_unconfirmed") else "estimated")
              for code, rows in tl.items() for r in rows if r.get("call_date_unconfirmed") or r.get("estimated")]
L.append("rows carrying the new markers (timeline side): %s" % tl_markers)
extra = sorted(set(tl) - set(led))
L.append("timeline companies not in ledger: %s" % (extra or "none"))
open(HERE + "e9_timeline_vs_ledger_%s.txt" % REV, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
