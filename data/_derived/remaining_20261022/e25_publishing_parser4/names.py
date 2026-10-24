# -*- coding: utf-8 -*-
import json
d = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown.json", encoding="utf-8"))
n = {r["원보험사코드"]: r["원수사명"] for r in d}
for c in ["KR0009","KR0010","KR0032","KR0068","KR0070","KR0082","KR0087","KR0099","KR0104","KR0003"]:
    print(c, n.get(c))
