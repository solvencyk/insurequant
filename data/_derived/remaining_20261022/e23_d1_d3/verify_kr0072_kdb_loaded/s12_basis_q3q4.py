# s12: is the statement table the plan used in the FY2024_Q3 / FY2024_Q4 filings 연결 or 별도? headings, BS totals, and where the other basis sits.
import sys, re
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded')
from xlib import *
V = ROOT + 'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
out = open(V + 's12_basis_q3q4.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
def nz(s):
    return re.sub(r'\s+', '', s)
for q, p in FILES.items():
    txt = read(p)
    lines = txt.split('\n')
    W('=====', q, p, 'lines', len(lines))
    # headings that mention 연결 / 별도 / 재무제표 section numbers
    hits = []
    for i, l in enumerate(lines):
        s = strip(l)
        if 3 < len(s) < 60 and re.search(r'(연결|별도)', s) and re.search(r'(재무상태표|포괄손익계산서|자본변동표|현금흐름표|재무제표)', s):
            hits.append((i + 1, s))
    W('  headings (first 40):', hits[:40])
    # BS totals: '부채및자본총계' rows -> values
    for ln, rows in tables(txt):
        for r in rows:
            if nz(r[0]) == '부채및자본총계':
                W('  L%d 부채및자본총계 %s' % (ln, r))
