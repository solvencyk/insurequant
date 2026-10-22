import json, glob, sys
sys.stdout.reconfigure(encoding="utf-8")
cc="00112882"
BSIDS=("자산총계","부채총계","자본총계")
for f in sorted(glob.glob(f"data/dart/_fs_api_cache/{cc}_*.json")):
    d=json.load(open(f,encoding="utf-8"))
    lst=d.get("list") or []
    print("==",f.split("/")[-1],len(lst))
    for r in lst:
        if r.get("sj_div")=="BS" and r.get("account_nm","").replace(" ","") in BSIDS+("보험계약부채","재보험계약부채","투자계약부채","이익잉여금","기타포괄손익누계액"):
            print("  ",r["account_nm"],r.get("thstrm_amount"),r.get("frmtrm_amount"),r.get("bfefrmtrm_amount"),r.get("thstrm_dt") if "thstrm_dt" in r else "", r.get("rcept_no"))
