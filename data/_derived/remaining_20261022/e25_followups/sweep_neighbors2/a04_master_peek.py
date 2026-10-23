import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pl = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
c = sys.argv[1]
for q in sys.argv[2:]:
    print(c, q, {i: pl.get((c, q, str(i))) for i in range(1, 15)})
