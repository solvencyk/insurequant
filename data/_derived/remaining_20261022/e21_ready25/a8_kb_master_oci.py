import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(R + "PL_breakdown.json", encoding="utf-8").read())}
for q in ("2023.4Q", "2024.1Q", "2023.1Q"):
    print(q, {i: pl.get(("KR0010", i, q)) for i in (25, 26, 27, 28, 29, 30, 31, 32)})
