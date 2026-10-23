# -*- coding: utf-8 -*-
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
def head(rel): return json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
def live(rel): return json.load(open(R+"/"+rel,encoding="utf-8"))
for rel in ["data/_gold/user_pl_cells.json","data/_gold/user_csm_cells.json"]:
    h,l=head(rel),live(rel)
    for sect in l:
        if sect=="_doc": continue
        for lab,d in (("HEAD",h),("LIVE",l)):
            v=d.get(sect)
            if isinstance(v,list):
                ks=[e for e in v if isinstance(e,dict) and e.get("원보험사코드")=="KR0099"]
                print(rel,sect,lab,"KR0099 entries",len(ks),sorted(set((e["공시분기"]) for e in ks)))
            elif isinstance(v,dict):
                print(rel,sect,lab,"dict len",len(v),[k for k in v if "KR0099" in k][:20])
            else: print(rel,sect,lab,type(v))
h=head("data/_gold/user_pl_cells.json"); l=live("data/_gold/user_pl_cells.json")
for s in ("null_dangi","set_dangi"):
    print(s, "head sample", json.dumps(h[s][:2] if isinstance(h[s],list) else list(h[s].items())[:2],ensure_ascii=False)[:300])
    print(s, "KR0099 in live:", [e for e in l[s] if isinstance(e,dict) and e.get("원보험사코드")=="KR0099"] if isinstance(l[s],list) else None)
