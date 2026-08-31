# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

rows = json.loads(Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\scratch_master_20260831.json").read_text(encoding="utf-8"))
for code in ["KR0070", "KR1011"]:
    recs = [r for r in rows if r["원보험사코드"]==code and r["공시분기"]=="2026.2Q" and r["항목번호"]==36]
    print(code, recs)
