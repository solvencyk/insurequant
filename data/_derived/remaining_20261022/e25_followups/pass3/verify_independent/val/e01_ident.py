# -*- coding: utf-8 -*-
import json, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant"
def head():
    return json.loads(subprocess.run(["git","-C",R,"show","HEAD:PL_breakdown.json"],capture_output=True).stdout.decode("utf-8"))
wt = json.load(open(R+"/PL_breakdown.json", encoding="utf-8"))
def mk(rows):
    d = {}
    for r in rows: d[(r["원보험사코드"], r["공시분기"], str(r["항목번호"]))] = (r.get("값"), r.get("값_당분기"))
    return d
H, W = mk(head()), mk(wt)
IDS = {
 "3=4+5+6+7": ("3", ["4","5","6","7"]),
 "8=9+10+11+12": ("8", ["9","10","11","12"]),
 "2=3+8": ("2", ["3","8"]),
 "20=1+17": ("20", ["1","17"]),
 "22=20+21": ("22", ["20","21"]),
 "24=22-23": ("24", ["22","-23"]),
 "31=24+25": ("31", ["24","25"]),
 "25=26+27+28+29+30+32": ("25", ["26","27","28","29","30","32"]),
}
targets = {"KR0070": ["2025.3Q","2025.4Q","2026.1Q","2026.2Q"], "KR0087": ["2024.2Q","2024.3Q"], "KR0032": ["2023.1Q","2023.2Q","2023.3Q"]}
def chk(D, c, q, name, fld):
    lhs, rhs = IDS[name]
    a = D.get((c,q,lhs)); 
    if a is None or a[fld] is None: return None
    s = 0.0
    for t in rhs:
        sign = -1 if t.startswith("-") else 1
        v = D.get((c,q,t.lstrip("-")))
        if v is None or v[fld] is None: return None
        s += sign*v[fld]
    return a[fld]-s
for c, qs in targets.items():
    for q in qs:
        for fld, fn in ((0,"값"),(1,"당분기")):
            line=[]
            for name in IDS:
                rw, rh = chk(W,c,q,name,fld), chk(H,c,q,name,fld)
                if rw is None: line.append(f"{name}:skip(blank)" if rh is None else f"{name}:skip(blank now; HEAD {rh:+.3f})")
                else:
                    line.append(f"{name}:{rw:+.3f}" + ("" if rh is not None and abs(rh-rw)<1e-6 else f"(HEAD {None if rh is None else round(rh,3)})"))
            print(c,q,fn," ; ".join(line))
