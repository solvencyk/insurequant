"""c1_inventory.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY on every repo file; writes only next to this script.

Step 1 of the 신종자본증권 / 후순위채 classification census: one row per security, merged from
  - data/bonds/capital_securities_fy2026h1.json   (47 companies, latest per-company snapshot: 2026-06-30 or 2025-12-31)   = primary
  - data/bonds/capital_securities_fy2025.json     (39 companies, 2025-12-31)  -> adds securities that vanished in H1 2026 (redeemed)
  - data/bonds/disclosure/2026q1_per_bond.json    (2026.1Q 경영공시 per-bond, only KR0005 has a schedule)
  - kics_capital_securities.json                  (채권원장 rows -> what the current screen ledger credits as 기본자본/보완자본 per bond)
  - data/bonds/capital_tier_registry.json         (current 분류 등재부: type + evidence per security group)
Output: census_inventory.json / census_inventory.csv (utf-8-sig for Excel) in this directory.

Run (repo root):  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c1_inventory.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def jl(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


h1 = jl("data/bonds/capital_securities_fy2026h1.json")
fy25 = jl("data/bonds/capital_securities_fy2025.json")
q1 = jl("data/bonds/disclosure/2026q1_per_bond.json")
led = jl("kics_capital_securities.json")
reg = jl("data/bonds/capital_tier_registry.json")

HYB, SUB = "hybrid", "subordinated"


def eok(mn):
    return None if mn is None else round(float(mn) / 100.0, 2)


def b_key(code, tier, issue, face_mn, coupon=None):
    return (code, tier, issue, int(round(float(face_mn))) if face_mn is not None else None, coupon)


# ---------------------------------------------------------------------------------------------- rows from the two bond files
rows: dict[tuple, dict] = {}
for src_name, d in (("fy2025", fy25), ("h1", h1)):
    for c in d["companies"]:
        for b in c.get("bonds", []):
            k = b_key(c["code"], b["tier"], b.get("issue_date"), b.get("face_amount_mn"), b.get("coupon_pct"))
            r = rows.get(k)
            if r is None:
                r = {
                    "code": c["code"], "company": c["company"], "tier": b["tier"], "name": b["name"],
                    "issue_date": b.get("issue_date"), "call_date": b.get("call_date"), "call_source": b.get("call_source"),
                    "legal_maturity": b.get("legal_maturity"), "coupon_pct": b.get("coupon_pct"),
                    "face_eok": eok(b.get("face_amount_mn")), "outstanding_eok": eok(b.get("outstanding_mn")),
                    "as_of": b.get("as_of"), "date_estimate": b.get("date_estimate"), "bond_notes": b.get("notes"),
                    "source_file": b.get("source_file"), "in_fy2025": False, "in_h1": False,
                }
                rows[k] = r
            r["in_" + ("fy2025" if src_name == "fy2025" else "h1")] = True
            if src_name == "h1":  # the H1 file wins for the displayed values
                r.update({"name": b["name"], "call_date": b.get("call_date"), "call_source": b.get("call_source"),
                          "coupon_pct": b.get("coupon_pct"), "outstanding_eok": eok(b.get("outstanding_mn")), "as_of": b.get("as_of"),
                          "source_file": b.get("source_file"), "bond_notes": b.get("notes"), "date_estimate": b.get("date_estimate")})

for r in rows.values():
    if r["in_fy2025"] and not r["in_h1"]:
        r["status"] = "fy2025 목록에만 있음(2026 상반기 중 상환·미갱신 - 확인 필요)"
    elif r["in_h1"]:
        r["status"] = "h1 목록(%s 기준)" % r["as_of"]
    else:
        r["status"] = "?"

# ---------------------------------------------------------------------------------------------- 2026.1Q per-bond (KR0005 only)
q1_extra = []
for c in q1["companies"]:
    if c.get("status") == "DISCLOSURE_PERBOND":
        for b in c.get("bonds", []):
            hit = [k for k, r in rows.items() if r["code"] == c["company_code"] and r["issue_date"] == b["issue_date"]]
            q1_extra.append((c["company_code"], b["issue_date"], b["kind"], b["amount_eok"], b["rate_pct"], b["maturity_date"], bool(hit)))
            for k in hit:
                rows[k]["in_2026q1_per_bond"] = True
for r in rows.values():
    r.setdefault("in_2026q1_per_bond", False)

# ---------------------------------------------------------------------------------------------- ledger (current screen allocation)
led_by = defaultdict(list)
for lr in led["rows"]:
    led_by[(lr["원보험사코드"], "hybrid" if lr["종류"] == "신종자본증권" else "subordinated", lr["발행일"], int(round(lr["액면가_억"] * 100)))].append(lr)
for k, r in rows.items():
    lk = (r["code"], r["tier"], r["issue_date"], int(round((r["face_eok"] or 0) * 100)))
    lr = led_by.get(lk)
    if lr and len(lr) > 1:  # same code/date/face (e.g. KR0083 후순위 19호 / 26호): pair by the ledger's 구분 = bond name
        lr = [x for x in lr if x["구분"] == r["name"]] or lr
    if lr:
        r["in_ledger"] = True
        r["ledger_tier1_eok"] = lr[0]["기본자본인정액_억"]
        r["ledger_tier2_eok"] = lr[0]["보완자본인정액_억"]
        r["ledger_legacy_flag"] = lr[0]["경과조치"]
    else:
        r["in_ledger"] = False
        r["ledger_tier1_eok"] = r["ledger_tier2_eok"] = r["ledger_legacy_flag"] = None

# ---------------------------------------------------------------------------------------------- registry match (hybrids only)
reg_cos = reg["companies"]


def parse_reg_dates(s):
    """-> (exact_date or None, (lo, hi) or None, month_prefix or None)"""
    if not s:
        return None, None, None
    s = s.strip()
    if "~" in s:
        lo, hi = s.split("~")
        return None, (lo, hi), None
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s, None, None
    if " " in s and s.split(" ")[0].count("-") == 2:
        return s.split(" ")[0], None, None
    if len(s) == 7 and s[4] == "-":
        return None, None, s
    return None, None, s  # e.g. '2024.4Q'


def quarter_of(date):
    y, m, _ = date.split("-")
    return f"{y}.{(int(m) - 1) // 3 + 1}Q"


def reg_match(r):
    ent = reg_cos.get(r["code"])
    if not ent or r["tier"] != HYB or not r["issue_date"]:
        return None
    best = None
    for i, s in enumerate(ent["securities"]):
        exact, rng, other = parse_reg_dates(s.get("issue_date"))
        if exact and exact == r["issue_date"]:
            return i
        if rng and rng[0] <= r["issue_date"] <= rng[1]:
            best = best if best is not None else i
        if other and other == r["issue_date"][:7]:
            best = best if best is not None else i
        if other and other.endswith("Q") and other == quarter_of(r["issue_date"]):
            best = best if best is not None else i
    return best


for r in rows.values():
    i = reg_match(r)
    ent = reg_cos.get(r["code"])
    if i is None:
        r["registry_type"] = None
        r["registry_unconfirmed"] = None
        r["registry_entry"] = None
        r["registry_evidence"] = None
    else:
        s = ent["securities"][i]
        r["registry_type"] = s["type"]
        r["registry_unconfirmed"] = s.get("type_unconfirmed")
        r["registry_entry"] = s["name"]
        r["registry_evidence"] = s.get("evidence")

# registry entries that match NO bond row (e.g. 채권원장 밖 금액, 2026.2Q 신규 미등재 증권) -> reported separately
unmatched_reg = []
for code, ent in reg_cos.items():
    for i, s in enumerate(ent["securities"]):
        if not any(r["code"] == code and r["registry_entry"] == s["name"] for r in rows.values()):
            unmatched_reg.append({"code": code, "company": ent["company"], "entry": s["name"], "issue_date": s.get("issue_date"),
                                  "amount_eok": s.get("amount_eok"), "amount_basis": s.get("amount_basis"), "type": s["type"],
                                  "type_unconfirmed": s.get("type_unconfirmed")})

out = sorted(rows.values(), key=lambda r: (r["code"], r["tier"], r["issue_date"] or "9999", r["name"]))
(HERE / "census_inventory.json").write_text(json.dumps({"rows": out, "registry_entries_without_bond_row": unmatched_reg,
                                                      "q1_per_bond_kr0005": q1_extra}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
cols = ["code", "company", "tier", "name", "issue_date", "call_date", "call_source", "legal_maturity", "coupon_pct", "face_eok", "outstanding_eok",
        "as_of", "status", "in_fy2025", "in_h1", "in_2026q1_per_bond", "in_ledger", "ledger_tier1_eok", "ledger_tier2_eok", "ledger_legacy_flag",
        "registry_type", "registry_unconfirmed", "registry_entry", "registry_evidence", "date_estimate", "bond_notes", "source_file"]
with open(HERE / "census_inventory.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in out:
        w.writerow(r)

# ---------------------------------------------------------------------------------------------- console summary
print("securities:", len(out), "| companies with >=1:", len({r["code"] for r in out}), "| of 47 in h1 file:", len(h1["companies"]))
print("by tier:", dict(Counter(r["tier"] for r in out)))
print("status:", dict(Counter(r["status"][:30] for r in out)))
print("in_ledger:", dict(Counter(r["in_ledger"] for r in out)))
print("hybrid registry types:", dict(Counter((r["registry_type"], r["registry_unconfirmed"]) for r in out if r["tier"] == HYB)))
print("hybrid with issue_date >= 2023-01-01 and NO registry match:", [(r["code"], r["issue_date"], r["name"][:30]) for r in out if r["tier"] == HYB and (r["issue_date"] or "") >= "2023-01-01" and r["registry_type"] is None])
print("hybrid with issue_date < 2023-01-01 and NO registry match:", [(r["code"], r["issue_date"], r["name"][:30]) for r in out if r["tier"] == HYB and (r["issue_date"] or "") < "2023-01-01" and r["registry_type"] is None])
print("securities without issue_date:", [(r["code"], r["tier"], r["name"][:40]) for r in out if not r["issue_date"]])
print("registry entries without a bond row:", len(unmatched_reg))
for u in unmatched_reg:
    print("   ", u["code"], u["company"], "|", u["entry"][:40], "|", u["issue_date"], u["amount_eok"], u["type"], u["type_unconfirmed"])
