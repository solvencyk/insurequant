# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)
for code in ["KR0008", "KR0002", "KR0049", "KR0074"]:
    rows = [r for r in data if r["원보험사코드"]==code and r["공시분기"]=="2026.2Q" and r["항목번호"] in (27,28)]
    for r in sorted(rows, key=lambda r:r["항목번호"]):
        print(code, r["항목번호"], repr(r["항목명"]))
# KR0010's own item27/28 label per-quarter history
print("--- KR0010 item27/28 across quarters ---")
for r in sorted([r for r in data if r["원보험사코드"]=="KR0010" and r["항목번호"] in (27,28)], key=lambda r:r["공시분기"]):
    print(r["공시분기"], r["항목번호"], repr(r["항목명"]))
