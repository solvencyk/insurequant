import sys,re,json,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
MK=re.compile(r"전분기|전반기|전3분기|\(전\)|전기|당분기|당반기|당3분기|\(당\)|당기")
for f in ("data/dart/FY2025_Q1/raw/KR0079_미래에셋생명/20250515001717.xml",):
    d=xmlrd.get(R+f)
    for ti,t in enumerate(d.tables):
        labs=[ " ".join(c["t"] for c in r["cells"][:1]) for r in t["rows"]]
        hit=[r for r in t["rows"] if r["cells"] and re.search(r"보험계약마진.*상각|CSM.*상각|제공된 서비스|당기손익으로 인식",r["cells"][0]["t"])]
        if hit:
            seg=xmlrd.strip(d.text[max(0,t["pos"]-600):t["pos"]])
            ms=list(MK.finditer(seg)); mk=seg[max(0,ms[-1].start()-2):ms[-1].end()+3] if ms else None
            bt=None
            for pos,l,txt in reversed([x for x in d.titles if x[0]<t["pos"]]):
                if "재무제표" in txt and "요약" not in txt: bt=txt;break
            print("TABLE",t["start"],t["end"],"unit",d.unit_before(t),"| marker",mk,"|",bt)
            print("   hdr:",[c["t"][:14] for c in t["rows"][0]["cells"]][:12])
            for r in hit[:3]: print("   ",r["line"],[c["t"][:14] for c in r["cells"]][:14])
