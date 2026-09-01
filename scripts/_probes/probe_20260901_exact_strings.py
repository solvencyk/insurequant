# -*- coding: utf-8 -*-
"""Exact raw string values (as stored in JSON) for every cell touched by the A/B/C fix,
plus a precision-preserving recomputation of ABL's item16 residual. Read-only."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
with (ROOT / "kics_disclosure.json").open("r", encoding="utf-8") as f:
    records = json.load(f)

by = {}
for r in records:
    c, q = r.get("원보험사코드"), r.get("공시분기")
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    by[(c, q, it)] = r

print("=== AIG 2025.2Q 값 (source for mirroring) ===")
for it in [1, 2, 3, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28, 36, 37, 38, 39, 40]:
    r = by.get(("KR0029", "2025.2Q", it))
    print(f"  item{it}: 값={r.get('값')!r}  값_적용후={r.get('값_적용후', '<NOKEY>')!r}")

print("\n=== AIG 2025.3Q 값 (source for mirroring) ===")
for it in [1, 2, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28]:
    r = by.get(("KR0029", "2025.3Q", it))
    print(f"  item{it}: 값={r.get('값')!r}  값_적용후={r.get('값_적용후', '<NOKEY>')!r}")

print("\n=== ABL 2025.3Q items 15,17-21 값_적용후 (exact strings) ===")
vals = {}
for it in [15, 17, 18, 19, 20, 21]:
    r = by.get(("KR0070", "2025.3Q", it))
    s = r.get("값_적용후")
    vals[it] = float(str(s).replace(",", ""))
    print(f"  item{it}_적용후 raw={s!r}  parsed={vals[it]}")
r6_exact = sum(vals[i] for i in (17, 18, 19, 20, 21)) - vals[15]
print(f"\n  exact R6 residual (sum17-21 - 15) = {r6_exact!r}  rounded2={round(r6_exact,2)}")
r16 = by.get(("KR0070", "2025.3Q", 16))
print(f"  current item16_적용후 raw={r16.get('값_적용후')!r}")

print("\n=== Heungkuk KR0071 2023.4Q items 22-26 (values + sibling zero format) ===")
for it in [22, 23, 24, 25, 26]:
    r = by.get(("KR0071", "2023.4Q", it))
    print(f"  item{it}: 값={r.get('값')!r}  항목명={r.get('항목명')!r}")
print("  -- sibling quarter 2023.3Q item25 (already-correct zero) for format reference --")
r25_sib = by.get(("KR0071", "2023.3Q", 25))
print(f"  2023.3Q item25: 값={r25_sib.get('값')!r}")
