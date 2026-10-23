# s06: which basis (연결 vs 별도) is each statement table, per filing; every table containing a 보험손익 row.
import sys, re
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded')
from xlib import *
V = ROOT + 'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
out = open(V + 's06_basis.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
def nz(s):
    return re.sub(r'\s+', '', s)
for q, p in FILES.items():
    txt = read(p)
    lines = txt.split('\n')
    W('=====', q, p)
    for ln, rows in tables(txt):
        if any(nz(r[0]) == '보험손익' for r in rows):
            ctx = []
            i = ln - 2
            while i >= 0 and len(ctx) < 6:
                s = strip(lines[i])
                if s:
                    ctx.append(s[:80])
                i -= 1
            r0 = [r for r in rows if nz(r[0]) == '보험손익'][0]
            W('  table L%d rows=%d ctx(rev)=%s' % (ln, len(rows), ctx))
            W('      보험손익 row:', r0)
            ni = [r for r in rows if nz(r[0]).startswith('당기순이익')]
            W('      당기순이익 row:', ni[:1])
