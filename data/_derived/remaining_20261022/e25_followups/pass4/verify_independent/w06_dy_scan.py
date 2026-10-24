# -*- coding: utf-8 -*-
import sys,re
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent")
from w02_lib import *
sys.stdout.reconfigure(encoding="utf-8")
fq=sys.argv[1]
p=raw_path(fq,"KR0087"); print(p)
# section markers
mk=[]
with open(p,encoding="utf-8",errors="replace") as f:
    for i,l in enumerate(f,1):
        m=re.search(r"(연결 ?재무제표|별도 ?재무제표|재무제표 ?주석)",l)
        if m and len(l)<400 and "<TITLE" in l.upper() or (m and re.search(r"<(TITLE|P)[^>]*>\s*[^<]{0,40}(연결|별도)",l)):
            mk.append((i,re.sub(r"<[^>]+>","",l).strip()[:60]))
print("markers",mk[:40])
for t in read_tables(p):
    labs=[r["cells"][0] if r["cells"] else "" for r in t["rows"]]
    flat=" ".join(" ".join(r["cells"]) for r in t["rows"])
    if "보험계약마진 금액" in flat and ("출재" in flat) :
        print("=== table",t["line"],len(t["rows"]))
        for r in t["rows"]:
            c=r["cells"]; j="|".join(c)
            if re.search(r"^(기초|기말|순자산|구분)|보험계약마진 금액|위험조정 상각액|경험조정|^\(단위|^[가-힣 ]*기 ",j) or "서비스를 반영" in j:
                print(" ",r["line"],j[:230])
