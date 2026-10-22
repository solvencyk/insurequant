import json
d=json.load(open("PL_breakdown_provenance.json",encoding="utf-8"))
print(list(d.keys()))
for k,v in d.items():
    if isinstance(v,(list,dict)):
        print(k,type(v).__name__,len(v))
        if isinstance(v,list): print(json.dumps(v[0],ensure_ascii=False)[:600])
        else:
            kk=list(v.keys())[:3]; print(kk)
    else: print(k, str(v)[:200])
