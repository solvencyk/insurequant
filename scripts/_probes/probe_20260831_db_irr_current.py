# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

SCRATCH = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\scratch_master_20260831b.json")
rows = json.loads(SCRATCH.read_text(encoding="utf-8"))
recs = [r for r in rows if r["원보험사코드"]=="KR0082" and r["공시분기"]=="2026.2Q" and str(r["항목번호"]).isdigit() and 41<=int(r["항목번호"])<=46]
for r in sorted(recs, key=lambda r: r["항목번호"]):
    print(r["항목번호"], r["항목명"], r["값"])
