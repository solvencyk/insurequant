# -*- coding: utf-8 -*-
import sys, json, subprocess
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
L=[]
def Pp(*a):
    s=" ".join(str(x) for x in a); L.append(s); print(s)
def head(rel): return json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
def live(rel): return json.load(open(R+"/"+rel,encoding="utf-8"))
M={"PL":("PL_breakdown.json","data/_gold/user_pl_cells.json"),"CSM":("CSM_waterfall.json","data/_gold/user_csm_cells.json")}
for sh,(mrel,grel) in M.items():
    lm=live(mrel); hm=head(mrel); lg=live(grel); hg=head(grel)
    ml={(r["항목번호"],r["공시분기"]):r for r in lm if r["원보험사코드"]=="KR0003"}
    mh={(r["항목번호"],r["공시분기"]):r for r in hm if r["원보험사코드"]=="KR0003"}
    hk={(e["원보험사코드"],e["항목번호"],e["공시분기"]) for e in hg["set"]}
    new=[e for e in lg["set"] if e["원보험사코드"]=="KR0003" and (e["원보험사코드"],e["항목번호"],e["공시분기"]) not in hk]
    Pp(sh,"new KR0003 gold entries:",len(new),"quarters",sorted({e["공시분기"] for e in new}))
    for e in sorted(new,key=lambda e:e["항목번호"]):
        k=(e["항목번호"],e["공시분기"])
        ok_live=abs(ml[k]["값"]-e["값"])<1e-9; ok_was=abs(mh[k]["값"]-e["was"])<1e-9
        Pp("  item",e["항목번호"],"gold",e["값"],"was",e["was"],"| live master==gold",ok_live,"| was==HEAD master",ok_was)
    # entries for KR0003 in other quarters unchanged
    ch=[(e["항목번호"],e["공시분기"]) for e in lg["set"] if e["원보험사코드"]=="KR0003" and (e["원보험사코드"],e["항목번호"],e["공시분기"]) in hk and e not in hg["set"]]
    Pp("  changed/replaced KR0003 pre-existing gold entries:",ch)
    # masked/live-master equality for ALL KR0003 gold entries
    miss=[(e["항목번호"],e["공시분기"],e["값"],ml[(e["항목번호"],e["공시분기"])]["값"]) for e in lg["set"] if e["원보험사코드"]=="KR0003" and abs(ml[(e["항목번호"],e["공시분기"])]["값"]-e["값"])>1e-9]
    Pp("  KR0003 gold entries whose value != live master:",miss)
# null_dangi == blanked singles
lg=live("data/_gold/user_pl_cells.json"); 
nd={tuple(c) for c in lg["null_dangi"]["cells"] if c[0]=="KR0003"}
lm=live("PL_breakdown.json"); hm=head("PL_breakdown.json")
blank={("KR0003","2023.4Q",r["항목번호"]) for r in lm if r["원보험사코드"]=="KR0003" and r["공시분기"]=="2023.4Q" and r["값_당분기"] is None and r["값"] is not None}
Pp("null_dangi KR0003 cells:",sorted(nd))
Pp("2023.4Q blank-single with non-null cum (live):",sorted(blank))
newblank={("KR0003","2023.4Q",r["항목번호"]) for r in hm if r["원보험사코드"]=="KR0003" and r["공시분기"]=="2023.4Q" and r["값_당분기"] is not None} & blank
Pp("blank now, populated in HEAD:",sorted(newblank),"== null_dangi (excluding pre-existing 15?)",newblank<=nd)
# identities (live vs HEAD) 2023.4Q
def ident(rows,tag):
    v={r["항목번호"]:r["값"] for r in rows if r["원보험사코드"]=="KR0003" and r["공시분기"]=="2023.4Q"}
    chk=[("3=4+5+6+7",v[3]-(v[4]+v[5]+v[6]+v[7])),("2=3+8",v[2]-(v[3]+v[8])),("8=9+10+11+12",v[8]-(v[9]+v[10]+v[11]+v[12])),
         ("17=18+19",v[17]-(v[18]+v[19])),("20=1+17",v[20]-(v[1]+v[17])),("22=20+21",v[22]-(v[20]+v[21])),("24=22-23",v[24]-(v[22]-v[23])),
         ("25=26+27+28+29+30+32",v[25]-(v[26]+v[27]+v[28]+v[29]+v[30]+v[32])),("31=24+25",v[31]-(v[24]+v[25])),
         ("bridge 1=2+13+14+15-16",v[1]-(v[2]+v[13]+v[14]+v[15]-v[16]))]
    Pp(tag,{k:round(x,6) for k,x in chk})
ident(lm,"LIVE identities residual:"); ident(hm,"HEAD identities residual:")
open(R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte/v12_gold_identity.txt","w",encoding="utf-8").write("\n".join(L))
