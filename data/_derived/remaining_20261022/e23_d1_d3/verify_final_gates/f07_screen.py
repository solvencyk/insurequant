# -*- coding: utf-8 -*-
import json,subprocess,sys,collections
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_final_gates/"
def head(rel):
    return json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
def idx(d): return {(r["원보험사코드"],r["항목번호"],r["공시분기"]):r for r in d}
PLl=idx(json.load(open(R+"/PL_breakdown.json",encoding="utf-8")));PLh=idx(head("PL_breakdown.json"))
CSl=idx(json.load(open(R+"/CSM_waterfall.json",encoding="utf-8")));CSh=idx(head("CSM_waterfall.json"))
FIVE=["KR0099","KR0003","KR0070","KR0009","KR0072"]
lines=[]
def P(s): lines.append(s); print(s)
# compare.html: PL items 1,17,24 (값, 14 quarters) ; CSM item 6 (값), item 2 (NB)
cmp_pl=collections.Counter(); cmp_csm=collections.Counter(); cmp_nb=collections.Counter()
p1=collections.defaultdict(list)
for k,r in PLl.items():
    if k[0] in FIVE and k[1] in (1,17,24) and PLh[k].get("값")!=r.get("값"): cmp_pl[k[0]]+=1
for k,r in CSl.items():
    if k[0] not in FIVE: continue
    h=CSh[k]
    if k[1]==6 and h.get("값")!=r.get("값"): cmp_csm[k[0]]+=1
    if k[1]==2 and h.get("값")!=r.get("값"): cmp_nb[k[0]]+=1
    if k[2]=="2023.4Q" and (h.get("값")!=r.get("값")): p1[k[0]].append((k[1],h.get("값"),r.get("값")))
P("compare.html (14-quarter trend, all quarters): changed 값 cells  PL items 1/17/24 (보험손익/투자손익/당기순이익 연누계, ROE 분자): %s"%dict(cmp_pl))
P("compare.html: changed CSM 기말(item 6) cells: %s ; changed NB CSM (item 2, feeds nb_csm/nb_multiple after resync): %s"%(dict(cmp_csm),dict(cmp_nb)))
P("IFRS17.html Panel1 year-mode (latest 2026.2Q + year-ends 2025/2024/2023) -> 2023.4Q bucket + opening bar visible. Changed 2023.4Q CSM cells:")
for c in FIVE: P("   %s %s"%(c,p1.get(c,"none")))
cnt=collections.Counter()
for c in FIVE:
    for q in ("2023.1Q","2023.2Q","2023.3Q"):
        pass
P("IFRS17.html Panel1 quarter-mode (last 5 quarters 2025.2Q-2026.2Q), Panel3 (latest only, 2026.2Q): changed cells in window = 0 (all changes are 2023.x)")
open(OUT+"f07_screen.txt","w",encoding="utf-8").write("\n".join(lines))
