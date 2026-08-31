# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

MASTER = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json")
rows = json.loads(MASTER.read_text(encoding="utf-8"))

# raw-PDF-verified 2026.2Q values (from my page dumps)
verified = {
    "KR0069": {1: 1295525, 2: 1102592, 3: 192933, 14: 622351, 27: 208.2},
    "KR0001": {1: 145432, 2: 52538, 3: 92894, 14: 63107, 27: 230.45},
}
for code, items in verified.items():
    print(f"=== {code} (LIVE master, before any of my session's writes) ===")
    for it, expect in items.items():
        recs = [r for r in rows if r["원보험사코드"]==code and r["공시분기"]=="2026.2Q" and r["항목번호"]==it]
        for r in recs:
            got = r["값"]
            try:
                match = abs(float(got) - expect) < 0.5
            except ValueError:
                match = False
            flag = "OK" if match else "MISMATCH !!"
            print(f"  item{it}: stored={got!r}  raw-verified={expect}  [{flag}]")
        if not recs:
            print(f"  item{it}: NOT PRESENT")
