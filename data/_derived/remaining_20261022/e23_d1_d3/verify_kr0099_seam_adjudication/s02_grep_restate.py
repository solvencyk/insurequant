# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_seam_adjudication/"
pat=re.compile(r"재작성|재표시|오류\s*수정|전기오류|비교\s*표시|비교표시|회계정책의 변경|추정의 변경")
with open(OUT+"s02_restate_hits.txt","w",encoding="utf-8") as f:
  for q in ("2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"):
    txt=load(XML[q]); plain=cell_text(txt)
    hits=[m for m in pat.finditer(plain)]
    f.write("===== %s hits=%d\n"%(q,len(hits)))
    last=-9999
    n=0
    for m in hits:
        if m.start()-last<600: continue
        last=m.start(); n+=1
        if n>25: break
        f.write("  ..."+plain[max(0,m.start()-150):m.start()+350]+"...\n\n")
print("done")
