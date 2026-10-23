# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_seam_adjudication/"
with open(OUT+"s03_vfa_note.txt","w",encoding="utf-8") as f:
  for q in ("2023.4Q","2024.1Q","2024.3Q","2024.4Q"):
    plain=cell_text(load(XML[q]))
    ms=[m.start() for m in re.finditer(r"회계정책의 변경으로 인한 소급효과|변동수수료접근법'을 최초|소급 재작성|소급하여 재작성|비교 ?표시된? .{0,20}재작성",plain)]
    f.write("===== %s n=%d\n"%(q,len(ms)))
    last=-9999
    for s in ms:
        if s-last<1500: continue
        last=s
        f.write(plain[max(0,s-200):s+2200]+"\n-----\n")
print("ok")
