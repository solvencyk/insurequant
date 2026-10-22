import json, io
for f in ("00112882_2025_11011_OFS.json","00112882_2026_11013_OFS.json","00112882_2026_11012_OFS.json"):
    d=json.load(open("data/dart/_fs_api_cache/"+f,encoding="utf-8"))
    L=d["list"] if isinstance(d,dict) else d
    print(f,type(d).__name__,len(L),list(L[0].keys()))
    for r in L:
        if r.get("sj_div") in ("CIS","IS") and any(k in r.get("account_nm","") for k in ("기타포괄손익","총포괄손익","당기순")):
            print("  ",r["sj_div"],r["account_id"],r["account_nm"],r.get("thstrm_amount"),r.get("thstrm_add_amount"),r.get("frmtrm_amount"),r.get("frmtrm_add_amount"))
