# s14: original-vintage FY2023 KDB filings (HEAD master source) and the FY2024_Q3/Q4 files: list every table with a 투자손익 row, with heading context and numbers.
import sys, re, glob, os
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded')
from xlib import *
V = ROOT + 'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
out = open(V + 's14_orig_basis.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
def nz(s):
    return re.sub(r'\s+', '', s)
for fy in ('FY2023_Q1', 'FY2023_Q2', 'FY2023_Q3', 'FY2023_Q4', 'FY2024_Q3', 'FY2024_Q4'):
    d = glob.glob(ROOT + 'data/dart/%s/raw/KR0072*' % fy)[0]
    xs = glob.glob(d + '/*.xml') or glob.glob(d + '/**/*.xml', recursive=True)
    p = xs[0]
    txt = open(p, encoding='utf-8', errors='replace').read()
    lines = txt.split('\n')
    W('=====', fy, os.path.basename(p), 'lines', len(lines), 'bytes', len(txt))
    n = 0
    for ln, rows in tables(txt):
        r = [x for x in rows if nz(x[0]) in ('투자손익',)]
        if r and any(nz(x[0]).startswith('당기순이익') for x in rows):
            ctx = []
            i = ln - 2
            while i >= 0 and len(ctx) < 5:
                s = strip(lines[i])
                if s:
                    ctx.append(s[:40])
                i -= 1
            ni = [x for x in rows if nz(x[0]).startswith('당기순이익')][0]
            W('  table L%d rows=%d ctx=%s' % (ln, len(rows), ctx))
            W('     투자손익', r[0][1:], '| 당기순이익', ni[1:])
            n += 1
    if n == 0:
        W('  no table with 투자손익+당기순이익 rows; tables:', len(tables(txt)))
        # fallback: any table with 투자손익
        for ln, rows in tables(txt):
            r = [x for x in rows if '투자손익' in nz(x[0])]
            if r:
                W('  L%d' % ln, r[0][:6])
                break
