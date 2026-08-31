# -*- coding: utf-8 -*-
import json, io, sys, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
bucket = {r["항목번호"]: r for r in data if r.get("원보험사코드") == "KR0029" and r.get("공시분기") == "2024.2Q"}
item19 = float(bucket[19]["값"])
V = [130.99, 16.61, 0.0, 16.74, 280.55]
M = [
    [1.0, 0.25, 0.25, 0.25, 0.0],
    [0.25, 1.0, 0.25, -0.25, 0.0],
    [0.25, 0.25, 1.0, 0.25, 0.0],
    [0.25, -0.25, 0.25, 1.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 1.0],
]
s = sum(V[i]*M[i][j]*V[j] for i in range(5) for j in range(5))
computed = math.sqrt(s)
print(f"item19 stored={item19} computed={computed:.4f} diff={abs(item19-computed):.4f}")
