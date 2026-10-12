# -*- coding: utf-8 -*-
"""c5: which registry/census classifications are NOT backed by primary evidence (issuer filing / issuer K-ICS table)?
Reads census_securities_final.csv (parser-kics census round 2) and the registry at the pinned revision; classifies the evidence basis into
   PRIMARY      issuer_filing (사업보고서·증권신고서 text) and/or the issuer's K-ICS table item 53
   SECONDARY    press / rating-agency report only
   OWNER        owner instruction or an owner excerpt whose original sentence the census could not locate
   INDIRECT     issuer filing read by analogy (wording differs from the usual step-up sentence)
   ISSUER_TABLE_ONLY  residual item-6 amounts with no ledger security (classified by the X test only)
and merges the per-security X-test verdict of c2 (same revision pin).  Output: c5_evidence_grade_<rev>.csv / .txt
"""
import csv
import sys

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
census = list(csv.DictReader(open(ROOT + "/data/_derived/capital_securities_classification_census_20261012/census_securities_final.csv", encoding="utf-8-sig")))
reg = audit_io.load_json("data/bonds/capital_tier_registry.json")["companies"]


def grade(basis):
    b = basis.lower()
    if "owner" in b:
        return "OWNER"
    if "indirect" in b:
        return "INDIRECT"
    if b.startswith("issuer_filing") or "issuer_filing" in b:
        return "PRIMARY"
    if "press" in b or "rating" in b:
        return "SECONDARY"
    return "OTHER"


def reg_lookup(code, issue_date, amount):
    """the security's entry in the PINNED registry (the census csv stores the registry type as of the census time, which is stale after dbbffcb5)."""
    ents = reg.get(code, {}).get("securities", [])
    cands = [s for s in ents if (s.get("issue_date") or "")[:10] == (issue_date or "")[:10]]
    if not cands:
        # registry rows without a ledger date (e.g. "2026.2Q") -> match by amount within 2 eok
        try:
            a = float(amount)
            cands = [s for s in ents if abs(s["amount_eok"] - a) <= 2.0 and "-" not in (s.get("issue_date") or "")]
        except Exception:
            cands = []
    if len(cands) > 1:
        try:
            a = float(amount)
            cands.sort(key=lambda s: abs(s["amount_eok"] - a))
        except Exception:
            pass
    return cands[0] if cands else None


rows = []
for c in census:
    g = grade(c["a_basis"])
    rs = reg_lookup(c["code"], c["issue_date"], c["outstanding_eok"])
    rows.append({"code": c["code"], "company": c["company"], "security": c["name"], "issue_date": c["issue_date"], "amount": c["outstanding_eok"],
                 "census_type": c["type"], "registry_type_now": rs["type"] if rs else "n/a",
                 "registry_issuer_type_now": (rs.get("issuer_type") or "") if rs else "",
                 "census_time_registry_type": c["registry_type_now"],
                 "grade": g, "basis": c["a_basis"]})
# residual (non-ledger) item-6 amounts in the registry
for code, ent in reg.items():
    for s in ent["securities"]:
        if s.get("amount_basis", "").startswith("항목 6") or s.get("amount_basis", "").startswith("항목 53") and s.get("issue_date") in (None, "") or "채권원장에 없는" in s["name"] or "채권원장 밖" in s["name"]:
            rows.append({"code": code, "company": ent["company"], "security": s["name"], "issue_date": s.get("issue_date"), "amount": s["amount_eok"],
                         "census_type": "", "registry_type_now": s["type"], "registry_issuer_type_now": s.get("issuer_type") or "",
                         "census_time_registry_type": "",
                         "grade": "ISSUER_TABLE_ONLY", "basis": s["evidence"][:140]})
cols = list(rows[0].keys())
with open(HERE + "c5_evidence_grade" + SUF + ".csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
L = ["PIN rev=%s registry=%s" % (audit_io.resolved_rev(), audit_io.sha12("data/bonds/capital_tier_registry.json"))]
from collections import Counter
cnt = Counter(r["grade"] for r in rows)
L.append("grade counts: " + ", ".join("%s %d" % kv for kv in sorted(cnt.items())))
for gname in ("OWNER", "SECONDARY", "INDIRECT", "ISSUER_TABLE_ONLY"):
    L.append("-- %s" % gname)
    for r in rows:
        if r["grade"] == gname:
            L.append("   %s %s | %s | %s | %s | pinned-registry type=%s issuer_type=%s (census-time %s) | %s" % (
                r["code"], r["company"], (r["security"] or "")[:44], r["issue_date"], r["amount"], r["registry_type_now"], r["registry_issuer_type_now"],
                r["census_time_registry_type"] or "-", r["basis"][:90]))
open(HERE + "c5_evidence_grade" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
