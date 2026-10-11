# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
bs = json.loads(open("IFRS17_BS.json", encoding="utf-8").read())
code = sys.argv[1]
items = [int(x) for x in sys.argv[2].split(",")]
mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
qs = sorted({r["공시분기"] for r in bs if r["원보험사코드"] == code}, key=lambda s: (s[:4], s[5]))
allq = [f"{y}.{n}Q" for y in range(2023, 2027) for n in (1, 2, 3, 4) if not (y == 2026 and n > 2)]
print("quarters present:", qs)
print("item  " + " ".join(f"{q:>12}" for q in allq))
for it in items:
    print(f"{it:>4}  " + " ".join((f"{mv[(code,it,q)]:>12,.1f}" if (code, it, q) in mv else f"{'.':>12}") for q in allq))
