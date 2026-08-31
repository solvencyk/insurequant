#!/usr/bin/env python3
"""Dump raw kics_rate_sensitivity.json + kics_disclosure.json rows for the RED buckets."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

rs = json.loads((ROOT / "kics_rate_sensitivity.json").read_text(encoding="utf-8"))
kd = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

TARGETS = [
    ("예별손해보험", "2024.4Q"),
    ("신한이지손해보험", "2024.4Q"),
    ("KB손해보험", "2026.2Q"),
]

for co, q in TARGETS:
    print("=" * 90)
    print(f"### {co} {q}  — kics_rate_sensitivity.json rows")
    print("=" * 90)
    rows = [r for r in rs if r["원수사명"] == co and r["공시분기"] == q]
    for r in rows:
        print(f"  경과조치={r['경과조치여부']:6s} measure={r['measure구분']:10s} "
              f"-100bp={r.get('-100bp')!s:>10} -50bp={r.get('-50bp')!s:>10} "
              f"base={r.get('base')!s:>10} +50bp={r.get('+50bp')!s:>10} +100bp={r.get('+100bp')!s:>10}")
    print()
    print(f"### {co} {q} — kics_disclosure.json items 1/2/3/14/27/28")
    drows = [r for r in kd if r["원수사명"] == co and r["공시분기"] == q and r.get("항목번호") in (1, 2, 3, 14, 27, 28)]
    for r in sorted(drows, key=lambda x: x["항목번호"]):
        print(f"  item{r['항목번호']:>3} {r.get('항목명','')!s:20s} 값={r.get('값')!s:>14} 값_적용후={r.get('값_적용후')!s:>14}")
    print()

# also dump full JSON blob for KB손해보험 2026.2Q rate sensitivity rows (all fields) for close inspection
print("=" * 90)
print("### RAW full-field dump — KB손해보험 2026.2Q rate sensitivity rows")
print("=" * 90)
for r in rs:
    if r["원수사명"] == "KB손해보험" and r["공시분기"] == "2026.2Q":
        print(json.dumps(r, ensure_ascii=False, indent=2))

print("=" * 90)
print("### RAW full-field dump — 신한이지손해보험 2024.4Q rate sensitivity rows")
print("=" * 90)
for r in rs:
    if r["원수사명"] == "신한이지손해보험" and r["공시분기"] == "2024.4Q":
        print(json.dumps(r, ensure_ascii=False, indent=2))
