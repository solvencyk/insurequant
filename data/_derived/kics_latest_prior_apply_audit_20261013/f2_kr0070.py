import json, sys, copy, os
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
import recalc_kics_derived as R
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
recs = json.load(open(REPO + "/kics_disclosure.json", encoding="utf-8"))
b = [copy.deepcopy(r) for r in recs if r["원보험사코드"] == "KR0070" and r["공시분기"] == "2024.3Q"]
out = open(os.path.dirname(os.path.abspath(__file__)) + "/f2_kr0070.txt", "w", encoding="utf-8")
by = {r["항목번호"]: r for r in b}
out.write(f"master KR0070 2024.3Q: item14={by[14]['값']} item15={by[15]['값']} item22={by[22]['값']} item23={by.get(23,{}).get('값')} item1={by[1]['값']}\n")
by[22]["값"] = "1"
stats = R.recalc(b)
by2 = {r["항목번호"]: r for r in b}
out.write(f"after recalc with item22=1 (in-memory copy only): item22={by2[22]['값']} stats22 zeroed={stats['item22_zeroed']}\n")
