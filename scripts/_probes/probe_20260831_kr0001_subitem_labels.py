# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

rows = json.loads(Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json").read_text(encoding="utf-8"))
for it in range(29, 36):
    recs = [r for r in rows if r["원보험사코드"]=="KR0001" and r["항목번호"]==it]
    if recs:
        print(f"item{it}: {recs[0]['항목명']!r}  (last seen {recs[-1]['공시분기']})")
    else:
        print(f"item{it}: NEVER SEEN for KR0001")
