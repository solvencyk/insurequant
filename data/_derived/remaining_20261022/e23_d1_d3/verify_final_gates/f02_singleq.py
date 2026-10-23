# -*- coding: utf-8 -*-
"""Recompute 값_당분기 from consecutive cumulative cells (live), classify vs stored; detect mixed-vintage pairs. Read-only."""
import json, subprocess, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_final_gates/"
def head(rel):
    b=subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout
    return json.loads(b.decode("utf-8"))
def live(rel): return json.load(open(R+"/"+rel,encoding="utf-8"))
FIVE=["KR0099","KR0003","KR0070","KR0009","KR0072"]
lines=[]
def P(*a):
    s=" ".join(str(x) for x in a); lines.append(s); print(s)
gold=live("data/_gold/user_pl_cells.json")
nul={tuple(c) for c in gold["null_dangi"]["cells"]}
setd={tuple(c[:3]) if isinstance(c,list) else (c["원보험사코드"],c["공시분기"],c["항목번호"]) for c in gold["set_dangi"]["cells"]}
P("null_dangi cells",len(nul),"set_dangi cells",len(setd), "sample set_dangi", list(setd)[:2])
QS=["1Q","2Q","3Q","4Q"]
TOL=0.0051
summary={}
for rel,kind in (("PL_breakdown.json","PL"),("CSM_waterfall.json","CSM")):
    h=head(rel); l=live(rel)
    hm={(r["원보험사코드"],r["항목번호"],r["공시분기"]):r for r in h}
    lm={(r["원보험사코드"],r["항목번호"],r["공시분기"]):r for r in l}
    P("=====",kind)
    for co in FIVE:
        items=sorted({k[1] for k in lm if k[0]==co},key=lambda x:(isinstance(x,str),str(x)))
        fys=sorted({k[2][:4] for k in lm if k[0]==co})
        stale=[];blank=[];pinned=[];xor=[];ok=0;chg_single=0
        for it in items:
            for fy in fys:
                cum={}
                for q in QS:
                    r=lm.get((co,it,f"{fy}.{q}"))
                    cum[q]=(r.get("값") if r else None, r.get("값_당분기") if r else None, r is not None)
                for i,q in enumerate(QS):
                    k=(co,it,f"{fy}.{q}")
                    if k not in lm: continue
                    v,sv,_=cum[q]
                    # expected
                    if kind=="PL":
                        if i==0: exp=v
                        else:
                            pv=cum[QS[i-1]][0]
                            exp=None if (v is None or pv is None) else v-pv
                    else:
                        nm=lm[k]["항목명"]
                        if "기초" in nm:
                            exp=cum["1Q"][0] if i==0 else (lm.get((co,6,f"{fy}.{QS[i-1]}")) or {}).get("값")
                        elif "기말" in nm: exp=v
                        else:
                            if i==0: exp=v
                            else:
                                pv=cum[QS[i-1]][0]; exp=None if (v is None or pv is None) else v-pv
                    # change flags
                    hk=hm.get(k); 
                    ch_now=(hk is not None and hk.get("값")!=v)
                    ch_sq=(hk is not None and hk.get("값_당분기")!=sv)
                    if ch_sq: chg_single+=1
                    # prev-cum changed?
                    prevch=False
                    if i>0:
                        pk=(co,it,f"{fy}.{QS[i-1]}"); hp=hm.get(pk); lp=lm.get(pk)
                        prevch=(hp is not None and lp is not None and hp.get("값")!=lp.get("값"))
                    if ch_now!=prevch and i>0 and kind=="PL" or (kind=="CSM" and i>0 and ch_now!=prevch and "기초" not in lm[k]["항목명"] and "기말" not in lm[k]["항목명"]):
                        xor.append((fy+"."+q,it,lm[k].get("항목명"),"cum_changed" if ch_now else "prev_cum_changed",v,sv))
                    if exp is None and sv is None: ok+=1; continue
                    if sv is None and exp is not None:
                        blank.append((fy+"."+q,it,lm[k].get("항목명"),exp,(co,f"{fy}.{q}",it) in nul)); continue
                    if exp is None: continue
                    if abs(sv-exp)<=TOL: ok+=1
                    else:
                        pin=(co,f"{fy}.{q}",it) in setd
                        (pinned if pin else stale).append((fy+"."+q,it,lm[k].get("项目名") if False else lm[k].get("항목명"),sv,exp,round(sv-exp,4)))
        P(f"-- {kind} {co}: ok={ok} stored-single changed vs HEAD={chg_single} | stored==None but derivable={len(blank)} (of which null_dangi={sum(1 for b in blank if b[4])}) | pinned(set_dangi)={len(pinned)} | MISMATCH stored vs recompute(not pinned)={len(stale)} | XOR-pairs={len(xor)}")
        for s in stale: P("   MISMATCH",s)
        for b in blank: P("   BLANK  ",b)
        for p in pinned: P("   PINNED ",p)
        summary[(kind,co)]={"stale":stale,"blank":blank,"pinned":pinned,"xor":xor}
        # xor details compact
        byq=collections.Counter((x[0],x[3]) for x in xor)
        P("   XOR by quarter",dict(sorted(byq.items())))
        json.dump({f"{k[0]}|{k[1]}":v for k,v in summary.items()},open(OUT+"f02_singleq.json","w",encoding="utf-8"),ensure_ascii=False,default=str)
open(OUT+"f02_singleq.txt","w",encoding="utf-8").write("\n".join(lines))
