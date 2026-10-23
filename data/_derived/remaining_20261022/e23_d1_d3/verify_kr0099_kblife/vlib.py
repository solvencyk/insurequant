# -*- coding: utf-8 -*-
"""Own minimal DART xml table reader (stdlib only)."""
import re, html, glob
R="C:/Users/sangwook.cho/Desktop/insurequant"
XML={
 "2023.1Q":glob.glob(R+"/data/dart/FY2023_Q1/raw/KR0099_*/*.xml")[0],
 "2023.2Q":glob.glob(R+"/data/dart/FY2023_Q2/raw/KR0099_*/*.xml")[0],
 "2023.3Q":glob.glob(R+"/data/dart/FY2023_Q3/raw/KR0099_*/*.xml")[0],
 "2023.4Q":R+"/data/dart/FY2023_Q4/raw/KR0099_케이비라이프생명보험_20240314000804/20240314000804.xml",
 "2024.1Q":R+"/data/dart/FY2024_Q1/raw/KR0099_케이비라이프생명보험/xml/20240516001445.xml",
 "2024.2Q":R+"/data/dart/FY2024_Q2/raw/KR0099_케이비라이프생명보험/xml/20240814002882.xml",
 "2024.3Q":R+"/data/dart/FY2024_Q3/raw/KR0099_케이비라이프생명보험/xml/20241114001333.xml",
 "2024.4Q":R+"/data/dart/FY2024_Q4/raw/KR0099_케이비라이프생명보험_20250314000905/xml/20250314000905.xml",
}
def load(path):
    for enc in ("utf-8","cp949"):
        try: return open(path,encoding=enc).read()
        except UnicodeDecodeError: continue
def cell_text(s):
    s=re.sub(r"<[^>]+>"," ",s); s=html.unescape(s); return re.sub(r"\s+"," ",s).strip()
def tables(txt):
    """yield dict(idx,line,pos,rows=[[cell,...]],head=text before)"""
    out=[]
    for m in re.finditer(r"<TABLE\b.*?</TABLE>",txt,re.S|re.I):
        body=m.group(0)
        rows=[]
        for rm in re.finditer(r"<TR\b.*?</TR>",body,re.S|re.I):
            cells=[]
            for cm in re.finditer(r"<(TD|TH|TE|TU)\b([^>]*)>(.*?)</\1>",rm.group(0),re.S|re.I):
                attrs=cm.group(2)
                cs=re.search(r'COLSPAN="?(\d+)',attrs,re.I)
                cells.append((cell_text(cm.group(3)),int(cs.group(1)) if cs else 1))
            rows.append(cells)
        line=txt.count("\n",0,m.start())+1
        pre=cell_text(txt[max(0,m.start()-1500):m.start()])[-200:]
        out.append({"line":line,"pos":m.start(),"rows":rows,"pre":pre})
    return out
def num(s):
    s=s.strip().replace(",","").replace(" ","")
    if s in ("","-","—"): return None
    neg=False
    if s.startswith("(") and s.endswith(")"): neg=True; s=s[1:-1]
    if s.startswith("△") or s.startswith("▲"): neg=True; s=s[1:]
    if s.startswith("-"): neg=True; s=s[1:]
    try: v=float(s)
    except ValueError: return "NaN"
    return -v if neg else v
