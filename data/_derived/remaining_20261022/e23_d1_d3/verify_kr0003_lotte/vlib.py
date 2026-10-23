# -*- coding: utf-8 -*-
"""Own minimal DART xml reader for KR0003 verification (stdlib only)."""
import re, html
R="C:/Users/sangwook.cho/Desktop/insurequant"
NEW=R+"/data/dart/FY2024_Q4/raw/KR0003_롯데손해보험_20250320001732/20250320001732.xml"
NEW_AUD=R+"/data/dart/FY2024_Q4/raw/KR0003_롯데손해보험_20250320001732/20250320001732_00760.xml"
ORIG=R+"/data/dart/FY2023_Q4/raw/KR0003_롯데손해보험_20240321001822/20240321001822.xml"
def load(p):
    for enc in ("utf-8","cp949"):
        try: return open(p,encoding=enc).read()
        except UnicodeDecodeError: pass
def ct(s):
    s=re.sub(r"<[^>]+>"," ",s); s=html.unescape(s); return re.sub(r"\s+"," ",s).strip()
def num(s):
    s=s.strip().replace(",","").replace(" ","")
    if s in ("","-","—"): return None
    neg=False
    if s.startswith("(") and s.endswith(")"): neg=True; s=s[1:-1]
    if s[:1] in "△▲": neg=True; s=s[1:]
    if s.startswith("-"): neg=True; s=s[1:]
    try: v=float(s)
    except ValueError: return "NaN"
    return -v if neg else v
def tables(txt):
    out=[]
    for m in re.finditer(r"<TABLE\b.*?</TABLE>",txt,re.S|re.I):
        body=m.group(0); rows=[]
        base=m.start()
        for rm in re.finditer(r"<TR\b.*?</TR>",body,re.S|re.I):
            cells=[]
            for cm in re.finditer(r"<(TD|TH|TE|TU)\b([^>]*)>(.*?)</\1>",rm.group(0),re.S|re.I):
                a=cm.group(2); ctx=re.search(r'ACONTEXT="([^"]*)"',a)
                cells.append({"t":ct(cm.group(3)),"ctx":ctx.group(1) if ctx else None,
                              "line":txt.count("\n",0,base+rm.start()+cm.start())+1})
            rows.append(cells)
        out.append({"line":txt.count("\n",0,m.start())+1,"rows":rows,"pre":ct(txt[max(0,m.start()-1500):m.start()])[-200:]})
    return out
