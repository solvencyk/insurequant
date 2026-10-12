"""s1: 47 companies x 2 tiers judgment table for `securities_summary` (value / null + basis bonds).

Also cross-checks each company's `issued_since_2023_eok` against the bond ledger (kics_capital_securities.json,
the table the utilization rules read) and the deployed JSON rows against this computation.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_summary_20261012/s1_judgment_table.py
Output: s1_judgment_table.csv (utf-8-sig) + s1_judgment_table.txt (summary) in this folder.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import capital_securities_summary as S  # noqa: E402

Q = "2026.2Q"


def main() -> int:
    as_of = S.quarter_end(Q)
    doc = json.loads(S.BONDS_PATH.read_text(encoding="utf-8"))
    ledger = json.loads((REPO / "kics_capital_securities.json").read_text(encoding="utf-8"))["rows"]
    led_since: dict[tuple, float] = {}
    for r in ledger:
        if (r.get("발행일") or "") >= S.SINCE:
            k = (r["원보험사코드"], "hybrid" if r.get("종류") == "신종자본증권" else "subordinated")
            led_since[k] = led_since.get(k, 0.0) + (r.get("잔액_억") or 0.0)
    t1 = {r["code"]: r for r in json.loads((REPO / "kics_tier1_utilization.json").read_text(encoding="utf-8"))["results"]}
    t2 = {r["code"]: r for r in json.loads((REPO / "kics_tier2_utilization.json").read_text(encoding="utf-8"))["results"]}
    rows, lines = [], []
    n_null = {"hybrid": 0, "subordinated": 0}
    mism_ledger, mism_deployed = [], []
    for c in doc["companies"]:
        code, name = c["code"], c["company"]
        summ = S.summarize_company(c.get("bonds") or [], as_of)
        for tier in ("hybrid", "subordinated"):
            v = summ[tier]
            live = [b for b in (c.get("bonds") or []) if b["tier"] == tier and (b.get("outstanding_mn") or 0) > 0]
            if v is None:
                n_null[tier] += 1
                why = "잔액이 남은 증권 없음" + (f" (원천 bonds {len(c.get('bonds') or [])}건, 잔액 0 또는 해당 tier 없음)")
                rows.append([code, name, tier, "", "", "", "", "", "", "", why, ""])
                continue
            dated = [b for b in live if b.get("issue_date")]
            last_name = ""
            if dated:
                last = max(dated, key=lambda b: (b["issue_date"], b["outstanding_mn"]))
                last_name = last["name"]
            notes = []
            if any(not b.get("issue_date") for b in live):
                notes.append("발행일 미상 증권 제외")
            if dated and v["latest_coupon_pct"] is None:
                notes.append("최근 발행 증권의 쿠폰이 원천에 없음 -> null")
            call_names = ""
            if v["next_call_date"]:
                call_names = " | ".join(b["name"] for b in live
                                        if not b.get("past_call_outstanding") and b.get("call_date") == v["next_call_date"])
            led = led_since.get((code, tier), 0.0)
            if abs(round(led) - v["issued_since_2023_eok"]) > 1:
                mism_ledger.append((code, name, tier, v["issued_since_2023_eok"], round(led, 1)))
            rows.append([code, name, tier, v["latest_coupon_pct"], v["latest_issue_date"], v["issued_since_2023_eok"],
                         v["next_call_date"], v["next_call_eok"], v["next_call_estimated"], v["balance_as_of"],
                         "; ".join(notes), f"latest={last_name} | call={call_names}"])
            dep = (t1[code] if code in t1 else {}).get("securities_summary"), (t2[code] if code in t2 else {}).get("securities_summary")
            for i, d in enumerate(dep):
                if d is None or d.get(tier) != v or d.get("as_of") != as_of:
                    mism_deployed.append((code, tier, "t1" if i == 0 else "t2"))
    with (HERE / "s1_judgment_table.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "company", "tier", "latest_coupon_pct", "latest_issue_date", "issued_since_2023_eok",
                    "next_call_date", "next_call_eok", "next_call_estimated", "balance_as_of", "note", "basis_bonds"])
        w.writerows(rows)
    lines.append(f"as_of={as_of} companies={len(doc['companies'])}")
    lines.append(f"tier object null: hybrid {n_null['hybrid']} / subordinated {n_null['subordinated']}")
    lines.append(f"vs ledger issued_since_2023 (|diff|>1억): {len(mism_ledger)}")
    for m in mism_ledger:
        lines.append("  " + str(m))
    lines.append(f"deployed rows != computed: {len(mism_deployed)} {mism_deployed[:10]}")
    (HERE / "s1_judgment_table.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
