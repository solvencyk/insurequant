import sys; sys.path.insert(0,'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent')
from vlib import *; from mlib import *
code='KR0070'
out=open(R+'data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/v11b_abl_cur.txt','w',encoding='utf-8')
def grp(rows):
    # header detection: does any row contain '3개월'
    for lr,c in rows[:5]:
        if '3개월' in c: return 'q'
    return 'c'
def find_tbl(T, must, anyof=()):
    res=[]
    for ln,rows in T:
        labels=[c[0] for _,c in rows if c]
        if all(any(m==l for l in labels) for m in must): res.append((ln,rows))
    return res
def row(rows,label,after=None):
    seen=after is None
    for lr,c in rows:
        if not seen:
            if c and c[0]==after: seen=True
            continue
        if c and c[0]==label: return lr,c
    return None
def prior(c,kind):
    v=[num(x) for x in c[1:]]
    # q: [cur3,curcum,pri3,pricum]; c: [cur,pri]
    if kind=='q': return v[0],v[1]
    return None,v[0]
tot=ok=bad=0
for y in (2025,2026):
  for qn in (1,2,3,4):
    q='%d.%dQ'%(y,qn)
    if q<'2025.3Q' or q>'2026.2Q': continue
    nq=q; p=path(nq,code)
    T=tables(p)
    rev=find_tbl(T,['예상보험금','위험조정변동','보험계약마진상각','재보험수익'])
    cost=find_tbl(T,['발생보험금','재보험비용','예상재보험금','위험조정변동'])
    if not rev or not cost: out.write('%s: tables not found rev=%d cost=%d\n'%(q,len(rev),len(cost))); continue
    lnR,rr=rev[0]; lnC,cr=cost[0]; kind=grp(rr)
    ra=row(rr,'위험조정변동'); csm=row(rr,'보험계약마진상각'); inc=row(rr,'발생재보험금',after='재보험수익')
    r_ra=row(cr,'위험조정변동',after='재보험비용'); r_csm=row(cr,'보험계약마진상각',after='재보험비용'); r_exp=row(cr,'예상재보험금',after='재보험비용')
    d={}
    d[4]=(csm,1)  # sign factor
    d[5]=(ra,1); d[9]=(r_csm,-1); d[10]=(r_ra,-1)
    res={}
    for it,(rw,s) in d.items():
        m3,cum=prior(rw[1],kind)
        res[it]=(s*cum if cum is not None else None, s*m3 if m3 is not None else None, rw[0])
    # item 11 = incurred reins claims - expected
    a3,ac=prior(inc[1],kind); b3,bc=prior(r_exp[1],kind)
    res[11]=(ac-bc, (a3-b3) if a3 is not None else None, inc[0])
    for it,(cum,m3,ln) in sorted(res.items()):
        mc=mv(code,q,it,'값'); ms=mv(code,q,it,'값_당분기')
        tot+=1
        okc = mc is not None and cum is not None and abs(mc-cum)<=1.01
        flag='OK ' if okc else 'BAD'
        if okc: ok+=1
        else: bad+=1
        sflag=''
        if m3 is not None:
            sflag='single raw3m=%s master=%s %s'%(m3,ms,'ok' if ms is not None and abs(ms-m3)<=1.01 else 'DIFF')
        out.write('%s %s item%-2d cum raw=%s master=%s (old=%s) | filing %s line %d | %s\n'%(flag,q,it,cum,mc,mv(code,q,it,'값',True),nq,ln,sflag))
out.write('TOTAL %d ok %d bad %d\n'%(tot,ok,bad))
out.close()
