#!/usr/bin/env python3
"""Full item dump of kics_disclosure.json for KR0010 2026.2Q (all 항목번호, not filtered)."""
from __future__ import annotations
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
kd = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
rows = [r for r in kd if r["원수사명"] == "KB손해보험" and r["공시분기"] == "2026.2Q"]
print(f"total rows for KB손해보험 2026.2Q: {len(rows)}")
for r in sorted(rows, key=lambda x: (x.get("항목번호") is None, x.get("항목번호"))):
    print(f"  item{str(r.get('항목번호')):>4} {r.get('항목명','')!s:28s} 값={str(r.get('값')):>14} 값_적용후={str(r.get('값_적용후')):>14}")

# also KR0010 previous quarter (2026.1Q) items 1/14/27/28 for comparison (trend sanity)
print()
print("--- KR0010 2026.1Q items 1/14/27/28 (prior quarter, sanity trend) ---")
rows2 = [r for r in kd if r["원수사명"] == "KB손해보험" and r["공시분기"] == "2026.1Q" and r.get("항목번호") in (1,2,3,14,27,28)]
for r in sorted(rows2, key=lambda x: x["항목번호"]):
    print(f"  item{r['항목번호']:>3} {r.get('항목명','')!s:20s} 값={r.get('값')!s:>14} 값_적용후={r.get('값_적용후')!s:>14}")
