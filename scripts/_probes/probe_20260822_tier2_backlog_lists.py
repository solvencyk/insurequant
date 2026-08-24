# -*- coding: utf-8 -*-
"""read-only: dump exact (company,quarter) lists for the two 2026-08-22 backlogs
   1) TIER2_TABLE_ABSENT_INTERMITTENT (47_tier2_census / _post) -> RED, 38-39 buckets
   2) TFI_TIER_ROWS_ABSENT_BACKLOG (50_tfi_tier_split / _post) -> SKIP, ~430 buckets
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from solvency.validation.kics_json_rules import run_validation

data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
report = run_validation(data, tolerance=2.0)
findings = report["findings"]

print(f"summary: {report['summary']['by_status']}")

# --- 1) TIER2_TABLE_ABSENT_INTERMITTENT --------------------------------
intermittent = [f for f in findings
                if f["rule"] in ("47_tier2_census", "47_tier2_census_post")
                and "TIER2_TABLE_ABSENT_INTERMITTENT" in f.get("detail", "")]
buckets1 = sorted({(f["원보험사코드"], f["공시분기"]) for f in intermittent})
print(f"\n=== TIER2_TABLE_ABSENT_INTERMITTENT: {len(intermittent)} findings, "
      f"{len(buckets1)} distinct (code,quarter) buckets ===")
by_company1: dict[str, list[str]] = {}
for c, q in buckets1:
    by_company1.setdefault(c, []).append(q)
for c in sorted(by_company1):
    print(f"  {c}: {sorted(by_company1[c])}")

# --- 2) TFI_TIER_ROWS_ABSENT_BACKLOG ------------------------------------
backlog = [f for f in findings
           if f["rule"] in ("50_tfi_tier_split", "50_tfi_tier_split_post")
           and "TFI_TIER_ROWS_ABSENT_BACKLOG" in f.get("detail", "")]
buckets2 = sorted({(f["원보험사코드"], f["공시분기"]) for f in backlog})
print(f"\n=== TFI_TIER_ROWS_ABSENT_BACKLOG: {len(backlog)} findings, "
      f"{len(buckets2)} distinct (code,quarter) buckets ===")
by_company2: dict[str, list[str]] = {}
for c, q in buckets2:
    by_company2.setdefault(c, []).append(q)
for c in sorted(by_company2):
    print(f"  {c}: {len(by_company2[c])}q {sorted(by_company2[c])}")

# --- also: NO_TABLE flavor (50/51 missing AND 47/48/49 also missing) for contrast
no_table = [f for f in findings
            if f["rule"] in ("50_tfi_tier_split", "50_tfi_tier_split_post")
            and "TFI_TIER_ROWS_ABSENT_NO_TABLE" in f.get("detail", "")]
buckets3 = sorted({(f["원보험사코드"], f["공시분기"]) for f in no_table})
print(f"\n=== TFI_TIER_ROWS_ABSENT_NO_TABLE (no 47/48/49 either, not our task): "
      f"{len(no_table)} findings, {len(buckets3)} distinct buckets ===")

# dump machine-readable too
out = {
    "intermittent_38": [{"code": c, "quarter": q} for c, q in buckets1],
    "backlog_430": [{"code": c, "quarter": q} for c, q in buckets2],
    "no_table": [{"code": c, "quarter": q} for c, q in buckets3],
}
outp = REPO / "scripts" / "_probes" / "_tier2_backlog_lists.json"
outp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n-> {outp}")

# companywide (SKIP, not our task) for cross-check
companywide = [f for f in findings
               if f["rule"] in ("47_tier2_census", "47_tier2_census_post")
               and "TIER2_TABLE_ABSENT_COMPANYWIDE" in f.get("detail", "")]
buckets_cw = sorted({(f["원보험사코드"], f["공시분기"]) for f in companywide})
print(f"\n=== TIER2_TABLE_ABSENT_COMPANYWIDE (do not touch): {len(companywide)} findings, "
      f"{len(buckets_cw)} distinct buckets, companies={sorted({c for c,_ in buckets_cw})} ===")
