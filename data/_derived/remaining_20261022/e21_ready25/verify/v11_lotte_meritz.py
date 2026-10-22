# -*- coding: utf-8 -*-
import sys, json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd, v10_note_engine as E
R = E.ROOT
master, head = E.master, E.head

def cmp(code, q, out, items=(2,3,4,5,6,8,9,10,11,13,14)):
    bad = []
    for it in items:
        m, h, e = master.get((code,q,it)), head.get((code,q,it)), out.get(it)
        d = "" if (e is not None and m is not None and abs(e-m) < 0.51) else "  <== DIFF"
        if d: bad.append(it)
        print(f"  item{it}: expected={e} master={m} head={h}{d}")
    return bad

allbad = {}
# Meritz
MER = {("KR0001","2023.1Q"): ("data/dart/FY2024_Q1/raw/KR0001_메리츠화재해상보험/20240516001162.xml", 48018),
       ("KR0001","2023.2Q"): ("data/dart/FY2024_Q2/raw/KR0001_메리츠화재해상보험/20240814003013.xml", 51801)}
for (c,q),(f,ln) in MER.items():
    d = xmlrd.get(R+f); ti,t = d.table_at_line(ln)
    out, raw = E.styleB(d, t, "MERITZ")
    print("==", c, q, "table", t["start"], raw)
    allbad[(c,q)] = cmp(c,q,out)
# Lotte single table
LOT = {("KR0003","2023.1Q"): ("data/dart/FY2024_Q1/raw/KR0003_롯데손해보험/20240516001888.xml", 20526),
       ("KR0003","2023.2Q"): ("data/dart/FY2024_Q2/raw/KR0003_롯데손해보험/20240814002875.xml", 22710),
       ("KR0003","2024.1Q"): ("data/dart/FY2025_Q1/raw/KR0003_롯데손해보험/20250515002628.xml", 20090)}
for (c,q),(f,ln) in LOT.items():
    d = xmlrd.get(R+f); ti,t = d.table_at_line(ln)
    out, raw = E.styleB(d, t, "LOTTE")
    print("==", c, q, "table", t["start"], raw)
    allbad[(c,q)] = cmp(c,q,out)
json.dump({f"{k[0]}|{k[1]}": v for k,v in allbad.items()}, open("v11_bad.json","w"))
