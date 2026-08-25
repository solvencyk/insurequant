# -*- coding: utf-8 -*-
"""`check_csm_continuity` 의 **검사범위 census** (validation iter4).

"룰이 0이라고 말한다" != "그 축이 깨끗하다". 이 룰이 어떤 (회사,분기)를 실제로 평가하고,
어떤 것을 `continue` 로 조용히 건너뛰는지 센다. 결측 SKIP 은 이 저장소의 명명된 안티패턴이라
그 규모를 먼저 재고 판단한다(룰 수정 전 전 버킷 시뮬레이션 원칙).

read-only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))
import validate_data_contract as gate  # noqa: E402

recs = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
recs = recs["records"] if isinstance(recs, dict) else recs
wf: dict = {}
for r in recs:
    co, q = r.get("원수사명"), r.get("공시분기")
    if co is None or q is None:
        continue
    wf.setdefault((co, q), {})[str(r.get("항목명") or "").replace(" ", "")] = r.get("값")

by_co: dict = {}
for (co, q), m in wf.items():
    by_co.setdefault(co, {})[q] = m

evaluated = skip_no_prev_fy = skip_missing_open = skip_missing_close = 0
missing_detail = []
breaks = []
for co, qmap in sorted(by_co.items()):
    for q in sorted(qmap):
        try:
            fy = int(str(q)[:4])
        except ValueError:
            continue
        prev = qmap.get(f"{fy - 1}.4Q")
        opening = (qmap.get(q) or {}).get("기초CSM")
        if prev is None:
            skip_no_prev_fy += 1
            continue
        prev_close = prev.get("기말CSM")
        if prev_close is None:
            skip_missing_close += 1
            missing_detail.append((co, q, "직전FY4Q 기말 결측"))
            continue
        if opening is None:
            skip_missing_open += 1
            missing_detail.append((co, q, "기초 결측"))
            continue
        evaluated += 1
        gap = opening - prev_close
        if abs(gap) > max(gate.CSM_CONT_TOL_REL * abs(prev_close), gate.CSM_CONT_TOL_ABS):
            breaks.append((co, q, prev_close, opening, gap))

print("=" * 96)
print("check_csm_continuity 검사범위 census")
print("=" * 96)
print(f"  마스터 (회사,분기) 버킷           : {len(wf)}")
print(f"  평가됨 (경계 실제 검산)           : {evaluated}")
print(f"  건너뜀 — 직전 FY 4Q 행 자체 없음  : {skip_no_prev_fy}   (구조적, 검사 대상 아님)")
print(f"  건너뜀 — 직전 FY 4Q '기말' 결측   : {skip_missing_close}  <-- 결측 SKIP")
print(f"  건너뜀 — 당해 '기초' 결측          : {skip_missing_open}  <-- 결측 SKIP")
print()
if missing_detail:
    print("  [결측으로 조용히 빠진 경계]")
    for co, q, why in missing_detail:
        print(f"     {co} {q} — {why}")
else:
    print("  결측으로 빠진 경계 없음")
print()
print(f"  경계 break (tol 밖) : {len(breaks)}")
for co, q, pc, op, gap in breaks:
    reg = "  [등재된 예외]" if (co, q) in gate._CSM_CONTINUITY_EXCEPTIONS else ""
    print(f"     {co} {q}: 직전기말 {pc:,.1f} -> 기초 {op:,.1f}  Δ{gap:+,.1f}{reg}")
