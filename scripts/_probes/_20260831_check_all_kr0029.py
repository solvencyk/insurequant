# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

aig = [r for r in data if r.get("원보험사코드") == "KR0029"]
print(f"ALL KR0029 rows: {len(aig)}")
by_q = {}
for r in aig:
    by_q.setdefault(r.get("공시분기"), []).append(r)
for q in sorted(by_q):
    print(f"  {q}: {len(by_q[q])} rows -> items {sorted(r.get('항목번호') for r in by_q[q])}")
