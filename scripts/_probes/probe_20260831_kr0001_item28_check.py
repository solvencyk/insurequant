# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

rows = json.loads(Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json").read_text(encoding="utf-8"))
recs = [r for r in rows if r["원보험사코드"]=="KR0001" and r["공시분기"]=="2026.2Q" and r["항목번호"]==28]
print(recs)
print("expected (52538/63107*100):", 52538/63107*100)
