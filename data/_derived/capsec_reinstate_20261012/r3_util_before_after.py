# -*- coding: utf-8 -*-
"""47사 x tier1/tier2 소진율 전 -> 후 + 사유 (증빙). 읽기 전용, 이 폴더에만 쓴다."""
import csv, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
D = Path("data/_derived/capsec_reinstate_20261012")
REASON = {
    "KR0097": "하나생명 제1회 1,800억 tier1 -> tier2 (스텝업 구조, owner 확정)",
    "KR0083": "푸본 2023-02 600억 미확정 tier1 -> tier2 확정",
    "KR0104": "농협생명 제5회 2,500억 미확정 tier1 -> tier2 확정",
    "KR1000": "코리안리 제5/6회 4,800억 미확정 tier1 -> tier2 확정",
    "KR0073": "교보 2024-11 6,000억 type tier1 -> tier2(issuer_type=tier1 병기), 결속 쪽이 기발행 70.1 이라 숫자 불변",
}
def load(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return {r["code"]: r for r in d["results"]}
b1, b2 = load(D / "before/kics_tier1_utilization.json"), load("kics_tier1_utilization.json")
c1, c2 = load(D / "before/kics_tier2_utilization.json"), load("kics_tier2_utilization.json")
rows = []
for code in sorted(b2):
    r = {"code": code, "company": b2[code].get("company"),
         "tier1_before": b1[code].get("utilization_pct"), "tier1_after": b2[code].get("utilization_pct"),
         "tier2_before": c1[code].get("utilization_pct"), "tier2_after": c2[code].get("utilization_pct")}
    r["tier1_changed"] = r["tier1_before"] != r["tier1_after"]
    r["tier2_changed"] = r["tier2_before"] != r["tier2_after"]
    r["reason"] = REASON.get(code, "") if (r["tier1_changed"] or r["tier2_changed"] or code == "KR0073") else ""
    rows.append(r)
with (D / "utilization_before_after_47.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "rows; tier1 changed", [r["code"] for r in rows if r["tier1_changed"]], "tier2 changed", [r["code"] for r in rows if r["tier2_changed"]])
for r in rows:
    if r["tier1_changed"] or r["tier2_changed"] or r["code"] == "KR0073":
        print(r["code"], r["company"], r["tier1_before"], "->", r["tier1_after"], "|", r["tier2_before"], "->", r["tier2_after"], "|", r["reason"])
