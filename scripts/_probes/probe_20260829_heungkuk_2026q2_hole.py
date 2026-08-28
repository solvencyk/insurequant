#!/usr/bin/env python3
"""Diagnose the newly-visible HOLE-PL 흥국화재 2026.2Q (부분) and the
코리안리 2026.2Q 이자부리 +494% qoq outlier. Read-only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
KEYS = ["보험손익", "생명장기손익", "당기순이익"]

print("=" * 78)
print("A. 흥국화재 PL 핵심 3항목 — 분기별")
print("=" * 78)
rows = [r for r in pl if r["원수사명"] == "흥국화재"]
byq: dict = {}
for r in rows:
    byq.setdefault(r["공시분기"], {})[r["항목명"].replace(" ", "")] = r
for q in sorted(byq):
    line = []
    for k in KEYS:
        r = byq[q].get(k)
        v = r.get("값") if r else "(행없음)"
        line.append(f"{k}={v}")
    print(f"  {q}  " + "  ".join(str(x) for x in line))

print()
print("=" * 78)
print("B. 흥국화재 2026.2Q 전체 행 (항목번호 순)")
print("=" * 78)
q2 = sorted([r for r in rows if r["공시분기"] == "2026.2Q"], key=lambda r: r["항목번호"])
print(f"  총 {len(q2)}행")
for r in q2:
    print(f"   {r['항목번호']:>3}  {r['항목명'][:34]:34s} 값={r.get('값')}  당분기={r.get('값_당분기')}")

print()
print("=" * 78)
print("C. 2026.2Q 에 '당기순이익' 행이 있는 회사 수 vs 없는 회사")
print("=" * 78)
q2all = [r for r in pl if r["공시분기"] == "2026.2Q"]
cos = sorted({r["원수사명"] for r in q2all})
missing = []
for co in cos:
    names = {r["항목명"].replace(" ", "") for r in q2all
             if r["원수사명"] == co and r.get("값") is not None}
    lack = [k for k in KEYS if k not in names]
    if lack:
        missing.append((co, lack))
print(f"  2026.2Q 회사수={len(cos)}, 핵심3항목 중 결측 있는 회사={len(missing)}")
for co, lack in missing:
    print(f"    {co:20s} 결측: {lack}")

print()
print("=" * 78)
print("D. 코리안리 이자부리 (CSM_waterfall)")
print("=" * 78)
wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
kr = [r for r in wf if r["원수사명"] == "코리안리재보험" and r["항목명"].replace(" ", "") == "이자부리"]
for r in sorted(kr, key=lambda r: r["공시분기"]):
    print(f"   {r['공시분기']}  이자부리={r.get('값')}")
