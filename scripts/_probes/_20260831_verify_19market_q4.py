# -*- coding: utf-8 -*-
import json, io, sys, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
bucket = {r["항목번호"]: r for r in data if r.get("원보험사코드") == "KR0029" and r.get("공시분기") == "2023.4Q"}
item19 = float(bucket[19]["값"])
V = [101.83, 18.93, 0.0, 31.01, 287.49]  # 36,37,38,39,40 (item37-40 are my derived override candidates)
# MARKET_M: diag 1.0; FX-equity(37,39)=-0.25; 자산집중(40) with all=0; else 0.25
M = [
    [1.0, 0.25, 0.25, 0.25, 0.0],
    [0.25, 1.0, 0.25, -0.25, 0.0],
    [0.25, 0.25, 1.0, 0.25, 0.0],
    [0.25, -0.25, 0.25, 1.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 1.0],
]
s = 0.0
for i in range(5):
    for j in range(5):
        s += V[i] * M[i][j] * V[j]
computed = math.sqrt(s)
print(f"item19 stored = {item19}")
print(f"computed from V={V} = {computed:.4f}")
print(f"diff = {abs(item19 - computed):.4f}")
