import sys,re; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
FILES={"Meritz":"data/dart/FY2024_Q1/raw/KR0001_메리츠화재해상보험/20240516001162.xml","Hanwha":"data/dart/FY2024_Q1/raw/KR0068_한화생명/20240514000837.xml",
"Lotte":"data/dart/FY2024_Q1/raw/KR0003_롯데손해보험/20240516001888.xml","농협":"data/dart/FY2024_Q1/raw/KR0104_농협생명보험/20240514001371.xml"}
for nm,p in FILES.items():
    d=xmlrd.get(R+p); txt=xmlrd.strip(d.text)
    print("==",nm)
    seen=0
    for m in re.finditer(r"(회계정책의? ?변경|체계적 ?배분|전기오류|오류의 수정|회계추정의 변경|재작성)",txt):
        ctx=txt[max(0,m.start()-120):m.end()+200]
        if re.search(r"2023|전기|전분기|제79|제75|제12|제1[0-9]기",ctx) and re.search(r"소급|재작성|수정",ctx):
            print("   ...",ctx.replace("\n"," ")); seen+=1
            if seen>=2: break
