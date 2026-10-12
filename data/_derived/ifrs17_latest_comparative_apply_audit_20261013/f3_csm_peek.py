import json, sys, os
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
code = sys.argv[1]; qs = sys.argv[2].split(",")
m = {}
for r in json.load(open(REPO + "/CSM_waterfall.json", encoding="utf-8")):
    m[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open(os.path.dirname(os.path.abspath(__file__)) + "/f3_csm_peek.txt", "w", encoding="utf-8")
for i in range(1, 7):
    out.write(f"item{i}: " + " | ".join(f"{q}={m.get((code,q,i),{}).get('값')}" for q in qs) + "\n")
