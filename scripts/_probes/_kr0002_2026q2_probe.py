# -*- coding: utf-8 -*-
"""Probe KR0002 (한화손해보험) 2026.2Q state: transition applicability + existing disclosure rows."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

# 1) transition applicability, recent quarters
ta = json.loads((ROOT / "data" / "_derived" / "kics_transition_applicability.json").read_text(encoding="utf-8"))
if isinstance(ta, dict):
    # try common shapes
    recs = ta.get("records") or ta.get("rows") or ta.get("data")
else:
    recs = ta

print("=== transition_applicability KR0002 recent ===")
for r in recs:
    if r.get("code") == "KR0002" and r.get("quarter") in ("2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"):
        print(r)

# 2) kics_disclosure.json rows for KR0002 recent quarters
disc = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
print(f"\ntotal rows in kics_disclosure.json: {len(disc)}")

for q in ("2025.4Q", "2026.1Q", "2026.2Q"):
    rows = [r for r in disc if r.get("원보험사코드") == "KR0002" and r.get("공시분기") == q]
    print(f"\n=== KR0002 {q}: {len(rows)} rows ===")
    rows_sorted = sorted(rows, key=lambda r: r.get("항목번호", -1))
    for r in rows_sorted:
        print(f"  item{r.get('항목번호'):>3}  {r.get('항목명'):30s}  값={r.get('값')!r}  값_적용후={r.get('값_적용후', '<absent>')!r}")
