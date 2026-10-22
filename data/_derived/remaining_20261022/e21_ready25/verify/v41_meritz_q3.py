import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
fs=[f for f in glob.glob(R+"data/dart/FY2023_Q3/raw/KR0001*/*.xml")+glob.glob(R+"data/dart/FY2023_Q3/raw/KR0001*/xml/*.xml") if not f.endswith("_00760.xml")]
print(fs)
d=xmlrd.get(fs[0]); txt=xmlrd.strip(d.text)
n=0
for m in re.finditer(r"재작성|재표시|오류|소급",txt):
    ctx=txt[max(0,m.start()-120):m.end()+200]
    if re.search(r"전분기|전반기|분기|CSM|보험계약마진|제103",ctx) and not re.search(r"비교표시 되는 2022년 12월 31일로 종료",ctx):
        print("-",ctx.replace("\n"," ")); n+=1
        if n>=5: break
