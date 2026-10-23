# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_seam_adjudication/"
plain=cell_text(load(XML["2023.4Q"]))
ms=[m.start() for m in re.finditer(r"③ 2023년 9월 30일 기준",plain)]
print(len(ms))
with open(OUT+"s04_note_restated_9m.txt","w",encoding="utf-8") as f:
    for s in ms:
        f.write("-----pos %d\n"%s)
        f.write(plain[s-100:s+3500]+"\n")
        # who is the subject: look back for 연결실체 vs 회사
        f.write("[prefix 1200] "+plain[s-1500:s-1200]+"\n")
