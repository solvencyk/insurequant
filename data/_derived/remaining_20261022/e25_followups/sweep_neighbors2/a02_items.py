import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
for fn in ("PL_breakdown.json","CSM_waterfall.json"):
    d = json.load(open(f"{ROOT}/{fn}", encoding="utf-8"))
    names = collections.OrderedDict()
    for r in d: names.setdefault(str(r["항목번호"]), r.get("항목명"))
    print(fn, len(d)); print(sorted(d[0].keys()))
    for k,v in sorted(names.items(), key=lambda x:(len(x[0]),x[0])): print(k, v)
