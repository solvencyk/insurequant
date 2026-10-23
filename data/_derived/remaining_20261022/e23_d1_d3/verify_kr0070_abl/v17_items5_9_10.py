import json
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
W = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0070"}
out = []
for it in (5, 6, 7, 9, 10, 11, 12):
    out.append("item %d: " % it + " | ".join("%s 값=%s 당분기=%s" % (q, W.get((q, it), {}).get("값"), W.get((q, it), {}).get("값_당분기")) for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q")))
open(ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/v17_items5_9_10.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
