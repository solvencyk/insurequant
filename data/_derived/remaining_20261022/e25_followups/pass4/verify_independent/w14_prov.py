import json,sys
sys.stdout.reconfigure(encoding="utf-8")
p=json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown_provenance.json",encoding="utf-8"))
def walk(o,path=""):
    if isinstance(o,dict):
        for k,v in o.items():
            if k in ("KR0032",) : print("KR0032 keys:",list(v.keys())[:12] if isinstance(v,dict) else type(v)); 
            walk(v,path+"/"+str(k))
print(type(p), list(p.keys())[:10] if isinstance(p,dict) else len(p))
q=p.get("KR0032") if isinstance(p,dict) else None
if q:
    x=q.get("2023.2Q") or q
    print(json.dumps(x,ensure_ascii=False)[:2500])
