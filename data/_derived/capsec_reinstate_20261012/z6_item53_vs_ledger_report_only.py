# -*- coding: utf-8 -*-
"""REPORT ONLY (no data changed): does the printed item 53 (경과조치 기발행 신종, the tier1 legacy 15% leg) include post-2022 hybrids?
Compares printed item 53 (2026.2Q) with the ledger's pre-2023 hybrid outstanding (data/bonds/capital_securities_fy2026h1.json) and
the registry's legacy_tfi total, and lists post-2022 hybrids in the ledger. Output z6_item53_vs_ledger_report_only.csv/.txt."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
p53 = {r["원보험사코드"]: (r.get("원수사명"), float(str(r["값"]).replace(",", "") or 0)) for r in recs
       if r["공시분기"] == "2026.2Q" and r["항목번호"] == 53 and str(r["값"]).replace(",", "").replace(".", "").replace("-", "").isdigit()}
led = json.loads((ROOT / "data/bonds/capital_securities_fy2026h1.json").read_text(encoding="utf-8"))
reg = json.loads((ROOT / "data/bonds/capital_tier_registry.json").read_text(encoding="utf-8"))["companies"]
rows = []
for c in led["companies"]:
    code = c["code"]
    pre = sum((b.get("outstanding_mn") or 0) / 100 for b in c["bonds"] if b["tier"] == "hybrid" and (b.get("issue_date") or "") < "2023-01-01")
    post = [(b["issue_date"], (b.get("outstanding_mn") or 0) / 100) for b in c["bonds"] if b["tier"] == "hybrid" and (b.get("issue_date") or "") >= "2023-01-01"]
    rlegacy = sum(s["amount_eok"] for s in (reg.get(code) or {}).get("securities", []) if s["type"] == "legacy_tfi")
    name, printed = p53.get(code, (c["company"], 0.0))
    if printed or pre or rlegacy:
        rows.append([code, name, printed, round(pre, 2), round(printed - pre, 2), round(rlegacy, 2), round(sum(a for _, a in post), 2), len(post), c.get("as_of")])
with (HERE / "z6_item53_vs_ledger_report_only.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["code", "company", "printed_item53_eok", "ledger_pre2023_hybrid_eok", "printed_minus_ledger", "registry_legacy_tfi_eok",
                "ledger_post2022_hybrid_outstanding_eok", "n_post2022_hybrids", "ledger_as_of"])
    w.writerows(rows)
L = ["REPORT ONLY - printed item 53 (tier1 legacy leg) vs ledger pre-2023 hybrid outstanding, 2026.2Q",
     "code company printed53 | ledger_pre2023 | printed-ledger | registry_legacy | post2022 hybrid out (n) | as_of"]
for r in rows:
    flag = "  <== printed exceeds ledger pre-2023 by > 2억" if r[4] > 2 else ""
    L.append(f"{r[0]} {str(r[1])[:9]:9s} {r[2]:10.1f} | {r[3]:10.1f} | {r[4]:9.1f} | {r[5]:10.1f} | {r[6]:10.1f} ({r[7]}) | {r[8]}{flag}")
(HERE / "z6_item53_vs_ledger_report_only.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
