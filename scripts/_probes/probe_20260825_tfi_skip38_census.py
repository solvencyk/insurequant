# -*- coding: utf-8 -*-
"""읽기전용: 50_tfi_tier_split 축의 SKIP 38버킷을 NO_TABLE/BACKLOG로 나눠 (회사,분기) 나열.
item52 backfill 여지가 있는지(=BACKLOG, 47/48/49는 있는데 50/51이 없는 버킷) 눈으로 확인용."""
from __future__ import annotations
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from solvency.validation.kics_json_rules import run_validation
from validate_kics_disclosure import _load_tfi_applicability

rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
tfi = _load_tfi_applicability()
findings = run_validation(rows, tfi_applicability=tfi)["findings"]

no_table, backlog = [], []
for f in findings:
    if f["rule"] != "50_tfi_tier_split" or f["status"] != "SKIP":
        continue
    tag = f.get("detail", "")
    key = (f["원보험사코드"], f["공시분기"])
    if "TFI_TIER_ROWS_ABSENT_BACKLOG" in tag:
        backlog.append(key)
    elif "TFI_TIER_ROWS_ABSENT_NO_TABLE" in tag:
        no_table.append(key)

name = {r.get("원보험사코드"): r.get("원수사명") for r in rows}
print(f"BACKLOG ({len(backlog)}) -- 47/48/49 있는데 50/51 없음 (같은 표 부모행 미추출):")
for c, q in sorted(backlog):
    print(f"  {c} {name.get(c,c)} {q}")
print(f"\nNO_TABLE ({len(no_table)}) -- TFI 표 자체가 [값] 에 없음:")
for c, q in sorted(no_table):
    print(f"  {c} {name.get(c,c)} {q}")
