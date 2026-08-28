# -*- coding: utf-8 -*-
"""Verify the tier1 flatten now carries the strict-basis note on every 소진율 row and
the over-100 clause on exactly the 13 rows expected."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from build_master_xlsx import FLATTEN  # noqa: E402

raw = json.loads((REPO / "kics_tier1_utilization.json").read_text(encoding="utf-8"))
rows = FLATTEN["kics_tier1_utilization.json"](raw)

pct_rows = [r for r in rows if r["항목명"] in ("기본자본 소진율", "기본자본 소진율(엄격)")]
print(f"소진율 rows total: {len(pct_rows)} (expect 78 = 39*2)")

empty_note = [r for r in pct_rows if not r["비고"]]
print(f"소진율 rows with EMPTY 비고: {len(empty_note)} (expect 0)")

over100 = [r for r in pct_rows if (r["값"] or 0) > 100.0]
print(f"소진율 rows with 값>100: {len(over100)} (expect 13)")
missing_over100_clause = [r for r in over100 if "100%초과는 파싱오류 아님" not in r["비고"]]
print(f"of those, missing the over-100 clause: {len(missing_over100_clause)} (expect 0)")

under100 = [r for r in pct_rows if (r["값"] or 0) <= 100.0]
wrongly_has_clause = [r for r in under100 if "100%초과는 파싱오류 아님" in r["비고"]]
print(f"rows <=100 that WRONGLY carry the over-100 clause: {len(wrongly_has_clause)} (expect 0)")

print("\nsample: NH농협손해보험 both rows")
for r in rows:
    if r["원수사명"] == "NH농협손해보험" and r["항목명"] in ("기본자본 소진율", "기본자본 소진율(엄격)"):
        print(f"  [{r['항목명']}] 값={r['값']}")
        print(f"    비고: {r['비고']}")

print("\nsample: 교보생명보험 (strict-only >100) both rows")
for r in rows:
    if r["원수사명"] == "교보생명보험" and r["항목명"] in ("기본자본 소진율", "기본자본 소진율(엄격)"):
        print(f"  [{r['항목명']}] 값={r['값']}")
        print(f"    비고: {r['비고']}")

print("\nsample: 흥국화재 (both <=100, plain basis note only) both rows")
for r in rows:
    if r["원수사명"] == "흥국화재" and r["항목명"] in ("기본자본 소진율", "기본자본 소진율(엄격)"):
        print(f"  [{r['항목명']}] 값={r['값']}")
        print(f"    비고: {r['비고']}")

print("\nsample: 동양생명 (issued_source=missing -> should concat 3 notes on 소진율 row)")
for r in rows:
    if r["원수사명"] == "동양생명" and r["항목명"] == "기본자본 소진율":
        print(f"  [{r['항목명']}] 값={r['값']}")
        print(f"    비고: {r['비고']}")

print("\ntotal rows:", len(rows), "(expect 390, unchanged)")
print("DONE")
