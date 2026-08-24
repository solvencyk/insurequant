# -*- coding: utf-8 -*-
"""read-only: classify the two new blocking-RED axes (51_tfi_tier2_composition PRE,
50_tfi_tier_split_post) that appeared after the item50/51 backfill, to confirm/refute
the two hypotheses:
  H1 (51_tfi_tier2_composition PRE): rule doesn't have the CAPPED/UNCAPPED branch that
     3_tier2_composition already has -- fails whenever item51==item47 (UNCAPPED pattern).
  H2 (50_tfi_tier_split_post): TFI-table-own-scope vs headline-full-combined-scope
     mismatch for companies with additional selective transitional measures beyond TFI
     -- should coincide with PRE passing cleanly for the same bucket.
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

by_bq = {}
for r in data:
    key = (r["원보험사코드"], r["공시분기"], int(r["항목번호"]))
    by_bq.setdefault(key[:2], {})[key[2]] = (r.get("값"), r.get("값_적용후"))


def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


# --- H1: 51_tfi_tier2_composition RED (전) ---
h1_reds = [f for f in findings if f["rule"] == "51_tfi_tier2_composition" and f["status"] == "RED"]
print(f"=== H1: 51_tfi_tier2_composition RED (전) = {len(h1_reds)} ===")
uncapped_like = 0
other = []
for f in h1_reds:
    c, q = f["원보험사코드"], f["공시분기"]
    items = by_bq.get((c, q), {})
    i47 = fnum(items.get(47, (None, None))[0])
    i51 = fnum(items.get(51, (None, None))[0])
    i48 = fnum(items.get(48, (None, None))[0])
    if i47 is not None and i51 is not None and abs(i47 - i51) <= 2.0:
        uncapped_like += 1
    else:
        other.append((c, q, i47, i48, i51, f.get("diff")))
print(f"  item51==item47 (UNCAPPED 패턴) 로 설명됨: {uncapped_like} / {len(h1_reds)}")
print(f"  설명 안 되는 잔여: {len(other)}")
for c, q, i47, i48, i51, diff in other[:20]:
    print(f"    {c} {q}: item47={i47} item48={i48} item51={i51} rule_diff={diff}")

# --- H2: 50_tfi_tier_split_post RED ---
h2_reds = [f for f in findings if f["rule"] == "50_tfi_tier_split_post" and f["status"] == "RED"]
print(f"\n=== H2: 50_tfi_tier_split_post RED (후) = {len(h2_reds)} ===")
pre_clean = 0
pre_dirty = []
companies = set()
for f in h2_reds:
    c, q = f["원보험사코드"], f["공시분기"]
    companies.add(c)
    pre_finding = next((x for x in findings if x["rule"] == "50_tfi_tier_split"
                          and x["원보험사코드"] == c and x["공시분기"] == q), None)
    if pre_finding is not None and pre_finding["status"] == "GREEN":
        pre_clean += 1
    else:
        pre_dirty.append((c, q, pre_finding["status"] if pre_finding else "N/A"))
print(f"  같은 버킷의 PRE(50_tfi_tier_split)가 GREEN: {pre_clean} / {len(h2_reds)}")
print(f"  PRE 도 안 깨끗한 잔여: {len(pre_dirty)}")
for c, q, st in pre_dirty[:20]:
    print(f"    {c} {q}: PRE status={st}")
print(f"\n  영향받는 회사 수: {len(companies)} -> {sorted(companies)}")
