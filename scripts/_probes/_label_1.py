# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print("--- KR0010 item1/2/3 label across quarters ---")
seen = {}
for r in sorted([r for r in data if r["원보험사코드"]=="KR0010" and r["항목번호"] in (1,2,3,14)], key=lambda r:(r["항목번호"], r["공시분기"])):
    key=(r["항목번호"], r["항목명"])
    seen.setdefault(key, []).append(r["공시분기"])
for (it,label), qs in seen.items():
    print(it, repr(label), "->", qs)
