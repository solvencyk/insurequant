import json, sys, os
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
code = sys.argv[1]; qs = sys.argv[2].split(","); items = [int(x) for x in sys.argv[3].split(",")]
m = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    m[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open(os.path.dirname(os.path.abspath(__file__)) + "/b2_master_peek.txt", "w", encoding="utf-8")
for i in items:
    out.write(f"item{i}: " + " | ".join(f"{q}={m.get((code,q,i),{}).get('값')}" for q in qs) + "\n")
