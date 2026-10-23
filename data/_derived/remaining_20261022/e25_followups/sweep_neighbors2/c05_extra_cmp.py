import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
csm = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r.get("값") for r in json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8"))}
d = json.load(open("c03_csm_extra.json", encoding="utf-8"))
for k, r in d.items():
    if r["status"] != "OK": continue
    c, q = k.split("|")
    diffs = {i: (csm.get((c, q, i)), r["prior"][i], round((r["prior"][i] - csm.get((c, q, i))) * 100, 1)) for i in "123456" if csm.get((c, q, i)) is not None and abs(r["prior"][i] - csm.get((c, q, i))) > 0.06}
    print(k, "closure", r["closure_eok"], "non-rounding diffs (master, latest, mn):", diffs)
