import json,sys
sys.stdout.reconfigure(encoding="utf-8")
d=json.load(open("insurance_liability_portfolio_provenance.json",encoding="utf-8"))
print(type(d), list(d.keys())[:10] if isinstance(d,dict) else len(d))
def find(o,path=""):
    if isinstance(o,dict):
        for k,v in o.items():
            if "KR0073" in str(k) or "교보생명" in str(k):
                print(path+"/"+str(k), json.dumps(v,ensure_ascii=False)[:700])
            else: find(v,path+"/"+str(k))
    elif isinstance(o,list):
        for i,v in enumerate(o):
            if isinstance(v,dict) and ("KR0073"==v.get("원보험사코드") or "KR0073"==v.get("company_code")):
                print(path+f"[{i}]", json.dumps(v,ensure_ascii=False)[:700])
            else: find(v,path+f"[{i}]")
find(d)
