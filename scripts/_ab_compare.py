# -*- coding: utf-8 -*-
"""A/B compare MIN vs MAX full-book combined-agn fallback. Shows every (company,
quarter) where item-1 (기초 CSM) differs, with the src path (cov), so we can tell
whether the MIN change (needed for 한화생명 2024 별도) regressed any non-gold company."""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

def load(p):
    rows = json.loads(Path(p).read_text(encoding="utf-8"))
    d = {}
    for r in rows:
        if r["항목번호"] == 1:
            d[(r["원수사명"], r["공시분기"])] = r["값"]
    return d

AB = Path("data/dart/viz/_ab")
mn = load(AB / "diag_min.json")
mx = load(AB / "diag_max.json")
cov = json.loads((AB / "cov_min.json").read_text(encoding="utf-8"))
covd = {tuple(k.split("|", 1)): v for k, v in cov.items()}

keys = sorted(set(mn) | set(mx))
print("=== (company, quarter) where MIN != MAX 기초 CSM ===")
ndiff = 0
for k in keys:
    a, b = mn.get(k), mx.get(k)
    if a is None and b is None:
        continue
    if a is None or b is None or abs((a or 0) - (b or 0)) > max(1.0, abs(b or a or 1) * 0.005):
        ndiff += 1
        src = "?"
        # cov key uses kr code, not name; map via the diag is awkward — just show name
        print(f"  {k[0]:14s} {k[1]}: MIN={a}  MAX={b}")
print(f"\n{ndiff} differing company-quarters (MIN vs MAX).")
print("Interpretation: gold is always 별도 (smaller). MIN=별도 is correct where both")
print("별도 and 연결 are present. MAX where it differs may have been picking 연결 (too high)")
print("or MIN may now pick a garbage/negative partial (regression). Check signs/magnitudes.")
