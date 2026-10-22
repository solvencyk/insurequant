import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
cands=[("Meritz FY2024_Q1","data/dart/FY2024_Q1/raw/KR0001_메리츠화재해상보험/20240516001162.xml"),("Meritz FY2023_Q4","data/dart/FY2023_Q4/raw/KR0001_메리츠화재해상보험/*.xml")]
for nm,p in cands:
    fs=[f for f in glob.glob(R+p) if not f.endswith("_00760.xml")]
    if not fs: print(nm,"none"); continue
    d=xmlrd.get(fs[0]); txt=xmlrd.strip(d.text)
    print("==",nm,fs[0].split("/")[-1],len(txt))
    n=0
    for m in re.finditer(r"(변경효과|계리적 ?가정|가정의 ?변경|회계정책의 ?변경|추정의 ?변경|비교표시|수정 ?재작성|보험계약마진.{0,20}(조정|수정))",txt):
        ctx=txt[max(0,m.start()-80):m.end()+160]
        if re.search(r"2023|전분기|제102|제103",ctx) and re.search(r"소급|재작성|수정|변경",ctx):
            print("   -",ctx.replace("\n"," ")); n+=1
            if n>=4: break
