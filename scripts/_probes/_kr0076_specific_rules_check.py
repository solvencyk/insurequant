# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ra = json.load(open("artifacts/kics_validation/report_20260831T073539Z.json", encoding="utf-8"))
kr76 = [f for f in ra.get("findings", []) if f.get("원보험사코드")=="KR0076" and f.get("공시분기")=="2026.2Q"]
for rule in ("36_irr", "47_tier2_census", "47_tier2_census_post", "48_tier2_limit", "48_tier2_limit_post",
             "50_tfi_tier_split", "50_tfi_tier_split_post", "53_tfi_memo_rows", "53_tfi_memo_rows_post",
             "51_tfi_tier2_composition", "3_tier2_composition"):
    for f in kr76:
        if f.get("rule") == rule:
            print(f"{rule:30s} status={f.get('status'):6s} expected={f.get('expected')!r} actual={f.get('actual')!r} diff={f.get('diff')!r}")
