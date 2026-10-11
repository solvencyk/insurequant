# -*- coding: utf-8 -*-
import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
bs = json.loads(open("IFRS17_BS.json", encoding="utf-8").read())
mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
names = {r["원보험사코드"]: r["원수사명"] for r in bs}
quarters = [f"{y}.{n}Q" for y in range(2023, 2027) for n in (1, 2, 3, 4) if not (y == 2026 and n > 2)]
KEY = [10, 11, 12, 13, 14, 15, 20, 21, 24]
holds = json.loads(open("data/_derived/bspl_followup_20261011/hold_reasons_5c.json", encoding="utf-8").read())
held = defaultdict(set)
for g in holds:
    kr, item = g["key"].split("|")
    for q in g["quarters"]:
        held[(kr, int(item), q)] = g["category"]
census = json.loads(open("data/disclosure/_meta/attachments_20261011/census_result.json", encoding="utf-8").read())
cens = {(c["kr"], c["period"]): c["category"] for c in census}
codes = sorted({r["원보험사코드"] for r in bs})
tot = 0
for kr in codes:
    qs_present = sorted({r["공시분기"] for r in bs if r["원보험사코드"] == kr}, key=lambda s: (s[:4], s[5]))
    miss = {}
    for q in qs_present:
        if q not in quarters:
            continue
        b = [i for i in KEY if (kr, i, q) not in mv]
        if b:
            miss[q] = b
    if not miss:
        continue
    print(f"== {kr} {names.get(kr, '')}")
    for q, b in miss.items():
        tags = []
        for i in b:
            h = held.get((kr, i, q))
            tags.append(f"{i}{'(H:' + h[:6] + ')' if h else ''}")
        c = cens.get((kr, q))
        print(f"   {q}: " + " ".join(tags) + (f"   [census {c}]" if c else ""))
        tot += len(b)
print("total key-item blanks:", tot)
