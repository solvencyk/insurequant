import sys,re,glob,os; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
FILES={"Meritz 2023.1Q (FY2024_Q1)":"data/dart/FY2024_Q1/raw/KR0001_메리츠화재해상보험/20240516001162.xml",
"Hanwha 2023.1Q (FY2024_Q1)":"data/dart/FY2024_Q1/raw/KR0068_한화생명/20240514000837.xml",
"Lotte 2023.1Q (FY2024_Q1)":"data/dart/FY2024_Q1/raw/KR0003_롯데손해보험/20240516001888.xml",
"KB손보 2023.4Q (FY2024_Q4)":"data/dart/FY2024_Q4/raw/KR0010_KB손해보험_20250314001697/20250314001697.xml",
"Mirae 2024.1Q (FY2025_Q1)":"data/dart/FY2025_Q1/raw/KR0079_미래에셋생명/20250515001717.xml",
"Fubon 2024.4Q (FY2025_Q4)":"data/dart/FY2025_Q4/raw/KR0083_푸본현대생명보험_20260331002089/20260331002089.xml",
"농협생명 2023.1Q (FY2024_Q1)":"data/dart/FY2024_Q1/raw/KR0104_농협생명보험/20240514001371.xml"}
PAT=re.compile(r"재작성|재표시|오류수정|전기오류|소급재작성|비교표시")
for nm,p in FILES.items():
    d=xmlrd.get(R+p)
    txt=xmlrd.strip(d.text)
    hits=[m for m in PAT.finditer(txt)]
    print("==",nm,"hits:",len(hits))
    shown=0
    for m in hits:
        ctx=txt[max(0,m.start()-110):m.end()+130]
        if re.search(r"전기|비교|2023|전분기|수정",ctx):
            print("   ...",ctx.replace("\n"," "))
            shown+=1
            if shown>=2: break
