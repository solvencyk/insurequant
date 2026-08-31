# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    rep = json.load(f)

findings = rep["findings"]
target_rules = {"2_tier1_bridge", "3_tier2_composition", "47_tier2_census", "48_tier2_limit",
                 "50_tfi_tier_split", "51_tfi_tier2_composition", "53_tfi_memo_rows"}
for q in ["2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"]:
    rows = [f for f in findings if f.get("원보험사코드") == "KR0049" and f.get("공시분기") == q
            and f["rule"] in target_rules]
    print(f"=== {q} ===")
    for f in sorted(rows, key=lambda x: x["rule"]):
        print(f"  [{f['status']:6s}] {f['rule']:28s} expected={f.get('expected')!r} actual={f.get('actual')!r} diff={f.get('diff')!r}")
