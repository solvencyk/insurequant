# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

aig_rows = [r for r in data if r.get("원보험사코드") == "KR0029"]
for r in sorted(aig_rows, key=lambda x: (x.get("공시분기"), x.get("항목번호"))):
    has_after = "값_적용후" in r
    v = r.get("값")
    va = r.get("값_적용후") if has_after else None
    same = (v == va) if has_after else None
    print(f"{r.get('공시분기')} item{r.get('항목번호')} {r.get('항목명')}: 값={v} 값_적용후={va} same={same}")
