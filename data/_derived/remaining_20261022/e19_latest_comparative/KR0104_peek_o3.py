# -*- coding: utf-8 -*-
import re
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
O3 = "data/dart/FY2023_Q3/raw/KR0104_농협생명보험/20231114001637.xml"
ls = (ROOT/O3).read_text(encoding="utf-8").split("\n")
st = [i for i,l in enumerate(ls) if "<TITLE" in l and "포괄손익계산서" in l]
print(st, [ls[i][:100] for i in st])
a = st[1]
out=[]
for i in range(a, a+900):
    m = re.match(r"<P>(.*)</P>", ls[i])
    if m and m.group(1).strip():
        out.append("%d %s" % (i+1, m.group(1)))
Path("KR0104_peek_o3.txt").write_text("\n".join(out), encoding="utf-8")
