# -*- coding: utf-8 -*-
"""Probe: reconcile item15 (R4 diversified sqrt) for KR0005 across quarters,
both 값 (pre) and 값_적용후 (post), to isolate the 2026.2Q item15후 79.1 gap."""
import io
import json
import sys
import math
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

with open(ROOT / "kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR0005"]


def num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


by_q = {}
for r in rows:
    q = r.get("공시분기")
    it = r.get("항목번호")
    by_q.setdefault(q, {})[it] = (num(r.get("값")), num(r.get("값_적용후")))

R4 = [
    [1.0, 0.0, 0.25, 0.25],
    [0.0, 1.0, 0.25, 0.25],
    [0.25, 0.25, 1.0, 0.25],
    [0.25, 0.25, 0.25, 1.0],
]


def diversified_sqrt(v):
    total = 0.0
    for i in range(4):
        for j in range(4):
            total += v[i] * R4[i][j] * v[j]
    return math.sqrt(max(total, 0.0))


for q in sorted(by_q.keys()):
    m = by_q[q]
    for col, idx in (("PRE(값)", 0), ("POST(적용후)", 1)):
        v17 = m.get(17, (None, None))[idx]
        v18 = m.get(18, (None, None))[idx]
        v19 = m.get(19, (None, None))[idx]
        v20 = m.get(20, (None, None))[idx]
        v21 = m.get(21, (None, None))[idx]
        v15 = m.get(15, (None, None))[idx]
        if None in (v17, v18, v19, v20, v21, v15):
            print(f"{q} {col}: MISSING inputs (17={v17},18={v18},19={v19},20={v20},21={v21},15={v15})")
            continue
        exp = diversified_sqrt([v17, v18, v19, v20]) + v21
        diff = v15 - exp
        flag = "  <-- MISMATCH" if abs(diff) > 2.0 else ""
        print(f"{q} {col}: 17={v17} 18={v18} 19={v19} 20={v20} 21={v21} | "
              f"item15 공시={v15} 계산={exp:.4f} diff={diff:+.4f}{flag}")
