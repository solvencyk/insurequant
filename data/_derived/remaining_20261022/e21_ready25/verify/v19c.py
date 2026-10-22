import sys,json,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
def load(p):
    d=collections.defaultdict(dict)
    for r in json.load(open(p,encoding="utf-8")): d[(r["원보험사코드"],r["공시분기"])][r["항목번호"]]=r["값"]
    return d
new=load(R+"CSM_waterfall.json"); old=load(HERE+"head/CSM_waterfall.json")
NINE=["KR0104","KR0083","KR0070","KR0079","KR0010","KR0099","KR0003","KR0001","KR0068"]
for c in NINE:
    for y in (2023,2024,2025):
        prev_o=old.get((c,f"{y-1}.4Q"),{}).get(6); prev_n=new.get((c,f"{y-1}.4Q"),{}).get(6)
        for q in (f"{y}.1Q",f"{y}.2Q",f"{y}.3Q",f"{y}.4Q"):
            o_o=old.get((c,q),{}).get(1); o_n=new.get((c,q),{}).get(1)
            if prev_n is None or o_n is None: continue
            dn=o_n-prev_n; do=None if (prev_o is None or o_o is None) else o_o-prev_o
            if abs(dn)>0.15 or (do is not None and abs(do)>0.15):
                print(c,q,"open",o_n,"prev4Q close",prev_n,"diff NEW",round(dn,1),"| HEAD diff",None if do is None else round(do,1))
