import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("c03_csm_extra.json", encoding="utf-8"))
for k, r in d.items():
    print(k, r["status"], r.get("err"), r.get("ngroups"))
    if r["status"] == "OK": print("   prior", r["prior"], "\n   curchk", r["cur_check"], "\n   mcur", r["master_cur"], r["tables"])
    if r["status"] == "UNCAL": print("   sums", r.get("cur_sums"), "\n   mcur", r.get("master_cur"))
