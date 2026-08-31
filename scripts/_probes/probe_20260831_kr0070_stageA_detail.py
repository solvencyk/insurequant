# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\src")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
from pathlib import Path
import fill_period_to_disclosure as fp

MASTER = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json")
rows = json.loads(MASTER.read_text(encoding="utf-8"))
F = fp._fields()
fp._process(rows, ["FY2026_Q2"], False, F, target_quarter=None)

for code in ["KR0070", "KR0082"]:
    items = sorted(set(int(r["항목번호"]) for r in rows if r["원보험사코드"]==code and r["공시분기"]=="2026.2Q" and str(r["항목번호"]).isdigit()))
    print(f"{code} 2026.2Q items after stage A:", items)
    for it in [17, 19]:
        v = [r["값"] for r in rows if r["원보험사코드"]==code and r["공시분기"]=="2026.2Q" and r["항목번호"]==it]
        print(f"  item{it}:", v)

print()
head = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\md_inbox\FY2026_Q2\KR0070_에이비엘생명보험.md").read_text(encoding="utf-8").split("\n")
for l in head[:20]:
    print(l)
