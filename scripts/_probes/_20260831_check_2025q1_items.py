# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
rows = [r for r in data if r.get("원보험사코드") == "KR0029" and r.get("공시분기") == "2025.1Q"]
for r in sorted(rows, key=lambda x: x["항목번호"]):
    print(f"item{r['항목번호']} {r['항목명']}: 값={r.get('값')}")
