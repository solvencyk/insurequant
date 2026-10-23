# own XML table reader (stdlib only) for DART atoc xml
import re
ROOT='C:/Users/sangwook.cho/Desktop/insurequant/'
CELL=re.compile(r'<(TD|TE|TH|TU)\b[^>]*>(.*?)</\1>',re.S)
def strip(s): return re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',s)).replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').strip()
FILES={'2023.1Q':'data/dart/FY2024_Q1/raw/KR0072_케이디비생명보험/20240516000597.xml',
       '2023.2Q':'data/dart/FY2024_Q2/raw/KR0072_케이디비생명보험/20240814000801.xml',
       '2023.3Q':'data/dart/FY2024_Q3/raw/KR0072_케이디비생명보험/20241114000809.xml',
       '2023.4Q':'data/dart/FY2024_Q4/raw/KR0072_케이디비생명보험_20250331002302/20250331002302.xml'}
def read(path):
    with open(ROOT+path,encoding='utf-8',errors='replace') as f: return f.read()
def tables(txt):
    """yield (start_line, rows) ; rows=list of list of cell texts. nested tables are not expected."""
    out=[]
    for m in re.finditer(r'<TABLE\b.*?</TABLE>',txt,re.S|re.I):
        ln=txt.count('\n',0,m.start())+1
        rows=[]
        for tr in re.findall(r'<TR\b.*?</TR>',m.group(0),re.S|re.I):
            c=[strip(x.group(2)) for x in CELL.finditer(tr)]
            if c: rows.append(c)
        out.append((ln,rows))
    return out
def num(s):
    s=s.replace(',','').strip()
    if s in ('','-'): return 0.0
    neg=(s.startswith('(') and s.endswith(')')) or s.startswith('△') or s.startswith('-')
    s=re.sub(r'[()△\-\s]','',s)
    return -float(s) if neg else float(s)
