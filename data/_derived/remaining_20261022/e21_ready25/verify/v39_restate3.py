import sys,re; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
for nm,p in (("Hanwha FY2024_Q1","data/dart/FY2024_Q1/raw/KR0068_한화생명/20240514000837.xml"),("Meritz FY2024_Q1","data/dart/FY2024_Q1/raw/KR0001_메리츠화재해상보험/20240516001162.xml"),("Lotte FY2024_Q1","data/dart/FY2024_Q1/raw/KR0003_롯데손해보험/20240516001888.xml")):
    d=xmlrd.get(R+p); 
    # restrict to the 별도 notes section
    pos0=[t[0] for t in d.titles if re.search(r"^5\. 재무제표 주석",t[2])]
    txt=xmlrd.strip(d.text[pos0[0]:]) if pos0 else xmlrd.strip(d.text)
    print("==",nm,"notes chars",len(txt))
    for m in re.finditer(r"재작성|재표시|소급적용|오류",txt):
        print("   ...",txt[max(0,m.start()-90):m.end()+140].replace("\n"," "))
        break
    hits=[m.start() for m in re.finditer(r"재작성|재표시|소급적용|전기오류|오류수정",txt)]
    print("   total hits in notes:",len(hits))
    for h in hits[:6]:
        print("   -",txt[max(0,h-60):h+110].replace("\n"," "))
