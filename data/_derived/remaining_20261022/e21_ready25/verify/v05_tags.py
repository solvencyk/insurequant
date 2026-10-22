import re,sys,collections,glob
sys.stdout.reconfigure(encoding="utf-8")
for f in ["data/dart/FY2024_Q1/raw/KR0104_농협생명보험/20240514001371.xml","data/dart/FY2025_Q1/raw/KR0003_롯데손해보험/20250515002628.xml","data/dart/FY2024_Q4/raw/KR0010_KB손해보험_20250314001697/20250314001697.xml"]:
    t=open(f,encoding="utf-8",errors="replace").read()
    c=collections.Counter(re.findall(r"<([A-Z][A-Z0-9\-]*)[ >]",t))
    print(f,len(t),c.most_common(25))
    m=re.findall(r"<TITLE[^>]*>[^<]*",t)
    print(len(m),m[:3])
