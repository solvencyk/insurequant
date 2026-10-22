# -*- coding: utf-8 -*-
"""READ-ONLY: evaluate the _zero_other_expense closure criterion on the builder-source rows of KB손보 2024.1Q-2024.4Q."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
rows = json.load(open(f"{ROOT}/data/dart/viz/pl_breakdown_master.json", encoding="utf-8"))
COMP = (4, 5, 6, 7, 8, 13, 14, 15)
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"):
    it = {r["항목번호"]: r["값"] for r in rows if r["원보험사코드"] == "KR0010" and r["공시분기"] == q}
    i1, i16 = it.get(1), it.get(16)
    comp = sum((it.get(k) or 0) for k in COMP)
    tol = max(300, abs(i1) * 0.001) if i1 is not None else None
    nulled = (i1 is not None and bool(i16) and abs(i1 - comp) <= tol)
    print(q, "item1", i1, "sum comps", comp, "resid", None if i1 is None else round(i1 - comp, 3), "tol", tol, "item16", i16, "-> _zero_other_expense nulls item16:", nulled)
