# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"
with open(ROOT + r"\artifacts\kics_validation\report_20260831T202722Z.json", "r", encoding="utf-8") as f:
    report = json.load(f)
findings = report.get("findings") or report.get("results") or report
for f in findings:
    if f.get("원보험사코드")=="KR0029" and f.get("공시분기") in ("2025.2Q","2025.3Q") and f.get("rule") in (
        "2_tier1_bridge","2_tier1_bridge_post","3_tier2_composition","3_tier2_composition_post",
        "51_tfi_tier2_composition","51_tfi_tier2_composition_post","50_tfi_tier_split","50_tfi_tier_split_post"):
        print(f"{f.get('공시분기')} {f.get('rule')}: {f.get('status')}")
        print(f"    {f.get('detail')}")
