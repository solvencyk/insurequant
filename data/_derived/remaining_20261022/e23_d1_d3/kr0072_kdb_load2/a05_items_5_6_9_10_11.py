# -*- coding: utf-8 -*-
"""read-only: names and live values of the PL items that this load leaves at the old vintage (validation ticket 20261023T1255Z: items 5, 6, 9, 10, 11) and the identity residuals they feed."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
by = {(r["항목번호"], r["공시분기"]): r for r in rows if r["원보험사코드"] == "KR0072"}
names = {i: r["항목명"] for (i, q), r in by.items()}
for i in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
    print(f"item {i:>2} {names.get(i)}")
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        r = by.get((i, q))
        print(f"    {q}: 값 {None if r is None else r['값']}  값_당분기 {None if r is None else r.get('값_당분기')}")
print()
print("identity 3 = 4+5+6+7 and 8 = 9+10+11+12 (백만원) on the loaded master")
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    v = {i: (by.get((i, q)) or {}).get("값") for i in range(1, 13)}
    f = lambda keys: None if any(v.get(k) is None for k in keys) else sum(v[k] for k in keys)  # noqa: E731
    a = f((4, 5, 6, 7))
    b = f((9, 10, 11, 12))
    print(f"  {q}: item3 {v[3]} vs 4+5+6+7 {a} (resid {None if a is None or v[3] is None else round(v[3] - a, 6)}); item8 {v[8]} vs 9+10+11+12 {b} (resid {None if b is None or v[8] is None else round(v[8] - b, 6)})")
