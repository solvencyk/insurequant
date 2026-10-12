# -*- coding: utf-8 -*-
"""e10: the downloadable sheet public_exports/자본성증권발행현황.json (one row per bond) against the bond ledger it is built from.
Expected row per ledger bond with an issue_date (any outstanding): company, issue date, 종류 (신종자본증권 = hybrid, 후순위채 = subordinated), 액면가_억 = face_mn/100,
잔액_억 = outstanding_mn/100, 콜만기도래일 = call_date (blank when call_date_unconfirmed or no call date), 법정만기일 = legal_maturity, 콜근거 = call_source
(DB손해 제1·2회: 「공시 원문 상충(콜일 미확정)」; 하나손해 추정 행: estimated_no_filing).   Output e10_issuance_sheet_vs_ledger_<rev>.txt"""
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

REV = audit_io.resolved_rev()
sheet = audit_io.load_json("public_exports/자본성증권발행현황.json")
led = audit_io.load_json("data/bonds/capital_securities_fy2026h1.json")["companies"]
L = ["PIN rev=%s sheet=%s ledger=%s" % (REV, audit_io.sha12("public_exports/자본성증권발행현황.json"), audit_io.sha12("data/bonds/capital_securities_fy2026h1.json"))]


def norm_name(n):
    return (n or "").replace(" ", "")


names = {}
for c in led:
    names[c["code"]] = c["company"]
# company-name matching between the sheet (display names) and the ledger (formal names): by containment of the shorter in the longer
def same_company(a, b):
    a, b = norm_name(a), norm_name(b)
    return a == b or a in b or b in a


exp = []
for c in led:
    for b in c.get("bonds", []):
        if not b.get("issue_date"):
            continue
        exp.append({"company": c["company"], "issue": b["issue_date"], "kind": "신종자본증권" if b["tier"] == "hybrid" else "후순위채",
                    "face": (b.get("face_amount_mn") or 0) / 100.0, "out": (b.get("outstanding_mn") or 0) / 100.0,
                    "call": None if b.get("call_date_unconfirmed") else b.get("call_date"), "mat": b.get("legal_maturity"), "src": b.get("call_source"),
                    "cdu": bool(b.get("call_date_unconfirmed")), "est": bool(b.get("estimated")), "used": False})
bad = []
unmatched_sheet = []
for r in sheet:
    m = [e for e in exp if not e["used"] and same_company(e["company"], r["회사명"]) and e["issue"] == r["발행일"] and e["kind"] == r["종류"] and abs(e["face"] - (r["액면가_억"] or 0)) <= 0.006]
    if not m:
        unmatched_sheet.append((r["회사명"], r["구분"], r["발행일"], r["종류"], r["액면가_억"]))
        continue
    e = m[0]
    e["used"] = True
    probs = []
    if abs(e["out"] - (r["잔액_억"] or 0)) > 0.006:
        probs.append("잔액 ledger %s sheet %s" % (e["out"], r["잔액_억"]))
    if (e["call"] or None) != (r["콜만기도래일"] or None):
        probs.append("콜만기도래일 ledger %s sheet %s" % (e["call"], r["콜만기도래일"]))
    if (e["mat"] or None) != (r["법정만기일"] or None):
        probs.append("법정만기일 ledger %s sheet %s" % (e["mat"], r["법정만기일"]))
    if e["cdu"] and "상충" not in (r["콜근거"] or ""):
        probs.append("콜근거 should say the filings conflict, sheet says %s" % r["콜근거"])
    if e["est"] and "estimated" not in (r["콜근거"] or ""):
        probs.append("콜근거 should mark the estimated row, sheet says %s" % r["콜근거"])
    if not e["cdu"] and not e["est"] and e["src"] and e["src"] != r["콜근거"]:
        probs.append("콜근거 ledger %s sheet %s" % (e["src"], r["콜근거"]))
    if probs:
        bad.append((r["회사명"], r["구분"], probs))
left = [e for e in exp if not e["used"]]
L.append("sheet rows %d ; ledger bonds with an issue date %d" % (len(sheet), len(exp)))
L.append("sheet rows that match no ledger bond: %d %s" % (len(unmatched_sheet), unmatched_sheet))
L.append("ledger bonds with no sheet row: %d %s" % (len(left), [(e["company"], e["issue"], e["kind"], e["face"], e["out"]) for e in left]))
L.append("rows whose fields differ from the ledger (잔액, 콜만기도래일, 법정만기일, 콜근거): %d" % len(bad))
for nm, g, probs in bad:
    L.append("   %s | %s | %s" % (nm, g, "; ".join(probs)))
open(HERE + "e10_issuance_sheet_vs_ledger_%s.txt" % REV, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
