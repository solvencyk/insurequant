# -*- coding: utf-8 -*-
"""Probe: dump KR0005 2026.2Q rows from kics_disclosure.json (read-only)."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

with open(ROOT / "kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0005" and r.get("공시분기") == "2026.2Q"]
rows.sort(key=lambda r: (r.get("항목번호") if r.get("항목번호") is not None else -1))

print(f"n_rows={len(rows)}")
for r in rows:
    print(
        f"item={r.get('항목번호')!r:>5} label={r.get('항목명')!r:<45} "
        f"값={r.get('값')!r:>12} 적용후={r.get('값_적용후')!r:>12}"
    )

# also dump prior quarter (2026.1Q) items 14,15,21,22,23 for comparison
print("\n--- 2026.1Q comparison (14,15,21,22,23,36-46,47-54) ---")
prior = [r for r in data if r.get("원보험사코드") == "KR0005" and r.get("공시분기") == "2026.1Q"]
prior.sort(key=lambda r: (r.get("항목번호") if r.get("항목번호") is not None else -1))
for r in prior:
    if r.get("항목번호") in list(range(14, 24)) + list(range(36, 55)):
        print(
            f"item={r.get('항목번호')!r:>5} label={r.get('항목명')!r:<45} "
            f"값={r.get('값')!r:>12} 적용후={r.get('값_적용후')!r:>12}"
        )

# also dump 2025.4Q for the same items (last full-form quarter before 2026.1Q)
print("\n--- 2025.4Q comparison (14,15,21,22,23) ---")
prior2 = [r for r in data if r.get("원보험사코드") == "KR0005" and r.get("공시분기") == "2025.4Q"]
prior2.sort(key=lambda r: (r.get("항목번호") if r.get("항목번호") is not None else -1))
for r in prior2:
    if r.get("항목번호") in list(range(14, 24)):
        print(
            f"item={r.get('항목번호')!r:>5} label={r.get('항목명')!r:<45} "
            f"값={r.get('값')!r:>12} 적용후={r.get('값_적용후')!r:>12}"
        )
