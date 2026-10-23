import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pl = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"):
    g = lambda i: pl.get(("KR0099", q, str(i)))
    print(q, "20", g(20), "21", g(21), "22", g(22), "-> 22-(20+21) =", None if None in (g(20), g(21), g(22)) else round(g(22) - g(20) - g(21), 1), "| 1+15-16+17-20 =", None if None in (g(1), g(15), g(16), g(17), g(20)) else round(g(1) + g(15) - g(16) + g(17) - g(20), 1))
