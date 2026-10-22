# -*- coding: utf-8 -*-
import re
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
F2 = "data/dart/FY2024_Q2/raw/KR0104_농협생명보험/20240814002115.xml"
ls = (ROOT/F2).read_text(encoding="utf-8").split("\n")
st = [i for i,l in enumerate(ls) if "<TITLE" in l and "4-2. 포괄손익계산서" in l]
a = st[0]
en = next(i for i in range(a+1, len(ls)) if "<TITLE" in ls[i])
out = ["range %d-%d" % (a+1, en)]
cur=None
for i in range(a, en):
    l = ls[i]
    if l.startswith("<TR"): cur=[]
    elif l.startswith("</TR>"):
        if cur: out.append(" | ".join(cur))
        cur=None
    elif cur is not None:
        m = re.match(r"<P[^>]*>(.*)</P>", l)
        if m: cur.append("%d:%s" % (i+1, m.group(1).strip()))
Path("KR0104_peek_f2.txt").write_text("\n".join(out), encoding="utf-8")
