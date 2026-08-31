# -*- coding: utf-8 -*-
import json, io, sys, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "src")
from solvency.validation.kics_json_rules import R4, MARKET_M

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# pull company metadata + label conventions from KR0010's own existing rows
kr0010_rows = [r for r in data if r["원보험사코드"] == "KR0010"]
meta_row = next(r for r in kr0010_rows if r["공시분기"] == "2026.1Q" and r["항목번호"] == 1)
NAME, TICKER, LS = meta_row["원수사명"], meta_row["티커"], meta_row["생손보여부"]
print("meta:", NAME, TICKER, LS)

label_by_item = {}
for r in kr0010_rows:
    label_by_item.setdefault(r["항목번호"], r["항목명"])
# fill labels not present on KR0010 itself, from convention (KR0008 2026.2Q, already-loaded this round)
kr0008_2q = {r["항목번호"]: r["항목명"] for r in data if r["원보험사코드"] == "KR0008" and r["공시분기"] == "2026.2Q"}
for it in list(range(36, 47)) + [53, 54]:
    if it not in label_by_item:
        label_by_item[it] = kr0008_2q[it]

for it in sorted(label_by_item):
    print(it, repr(label_by_item[it]))
