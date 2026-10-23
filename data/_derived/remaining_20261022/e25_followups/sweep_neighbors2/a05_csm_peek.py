import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
csm = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r.get("값") for r in json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8"))}
c = sys.argv[1]
qs = sorted({q for (cc, q, i) in csm if cc == c})
for q in qs:
    print(c, q, [csm.get((c, q, str(i))) for i in range(1, 7)])
