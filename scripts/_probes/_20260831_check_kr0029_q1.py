# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
print(f"TOTAL_ROWS={len(data)}")

# confirm only KR0029 rows changed for this quarter, no other company/quarter touched
aig = [r for r in data if r.get("원보험사코드") == "KR0029" and r.get("공시분기") == "2023.1Q"]
print(f"KR0029 2023.1Q rows: {len(aig)}")
for r in sorted(aig, key=lambda x: x.get("항목번호", 0)):
    print(f"  item{r.get('항목번호')} {r.get('항목명')}: 값={r.get('값')} 값_적용후={r.get('값_적용후')}")
