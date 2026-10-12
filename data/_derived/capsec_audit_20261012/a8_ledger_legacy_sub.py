# -*- coding: utf-8 -*-
"""a8: legacy (issued before 2023-01-01) subordinated debt per company from the per-bond ledger,
compared with the issuer-printed item 54 "(기발행 후순위채무)" and the legacy 신종 sum vs item 53.
Read-only; independent of the implementation. Output a8_ledger_legacy_sub.csv/.txt
Units: 백만원 in the ledger -> 억원 (/100).
"""
import csv
import json

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/capsec_audit_20261012/"
doc = json.load(open(ROOT + "/data/bonds/capital_securities_fy2026h1.json", encoding="utf-8"))
inp = json.load(open(OUT + "a2_inputs_2026_2Q.json", encoding="utf-8"))
CUT = "2023-01-01"
rows = []
for c in doc["companies"]:
    code = c["code"]
    r = inp.get(code, {})
    leg_sub = leg_sub_face = new_sub = leg_hyb = new_hyb = 0.0
    n_leg_sub = n_new_sub = 0
    asofs = set()
    for b in c.get("bonds", []):
        out = (b.get("outstanding_mn") or 0) / 100.0
        face = (b.get("face_amount_mn") or 0) / 100.0
        asofs.add(b.get("as_of"))
        iss = b.get("issue_date") or ""
        legacy = bool(iss) and iss < CUT
        if b.get("tier") == "subordinated":
            if legacy:
                leg_sub += out
                leg_sub_face += face
                n_leg_sub += 1
            else:
                new_sub += out
                n_new_sub += 1
        elif b.get("tier") == "hybrid":
            if legacy:
                leg_hyb += out
            else:
                new_hyb += out
    i54 = r.get("i54_pre")
    i53 = r.get("i53_pre")
    rows.append({
        "code": code, "company": c.get("company") or r.get("name"),
        "ledger_asof": "/".join(sorted(a for a in asofs if a)),
        "bs_sub_eok": None if c.get("bs_subordinated_mn") is None else round(c["bs_subordinated_mn"] / 100.0, 1),
        "ledger_legacy_sub_eok": round(leg_sub, 1), "ledger_new_sub_eok": round(new_sub, 1),
        "item54_printed": i54, "item54_minus_ledger_legacy": None if i54 is None else round(i54 - leg_sub, 1),
        "ledger_legacy_hybrid_eok": round(leg_hyb, 1), "item53_printed": i53,
        "item53_minus_ledger_legacy_hyb": None if i53 is None else round(i53 - leg_hyb, 1),
        "ledger_new_hybrid_eok": round(new_hyb, 1),
    })
cols = list(rows[0].keys())
with open(OUT + "a8_ledger_legacy_sub.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
with open(OUT + "a8_ledger_legacy_sub.txt", "w", encoding="utf-8", newline="\n") as f:
    f.write("code company | ledger_asof | BS sub | ledger legacy sub | ledger new sub | item54 | 54-ledgerlegacy | ledger legacy hyb | item53 | 53-ledgerlegacyhyb | ledger new hyb\n")
    for r in rows:
        if (r["ledger_legacy_sub_eok"] or r["item54_printed"] or r["ledger_legacy_hybrid_eok"] or r["item53_printed"]
                or r["ledger_new_sub_eok"] or r["ledger_new_hybrid_eok"]):
            f.write("%s %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s\n" % (
                r["code"], (r["company"] or "")[:7], r["ledger_asof"], r["bs_sub_eok"], r["ledger_legacy_sub_eok"],
                r["ledger_new_sub_eok"], r["item54_printed"], r["item54_minus_ledger_legacy"],
                r["ledger_legacy_hybrid_eok"], r["item53_printed"], r["item53_minus_ledger_legacy_hyb"], r["ledger_new_hybrid_eok"]))
print("done", len(rows))
