# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

rows = json.loads(Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json").read_text(encoding="utf-8"))
recs = [r for r in rows if r["원보험사코드"]=="KR0001" and r["항목번호"]==25]
for r in sorted(recs, key=lambda r: r["공시분기"]):
    print(f"{r['공시분기']}: name={r['항목명']!r} val={r['값']!r}")
