import json, os
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
B = json.load(open(REPO + "/artifacts/kics_validation/report_20261012T153753Z.json", encoding="utf-8"))
out = open(os.path.dirname(os.path.abspath(__file__)) + "/i2_detail.txt", "w", encoding="utf-8")
for f in B["findings"]:
    if f["rule"] == "2_tier1_bridge" and f["status"] == "RED":
        out.write(f"{f['원보험사코드']} {f['공시분기']} diff={f['diff']} detail={f['detail']}\n")
