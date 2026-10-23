# s13: what basis (연결/별도) does each statement table in each KDB filing have, and which basis do the master values (HEAD FY2023 originals, live FY2023, 2024) follow?
import sys, re, json, glob, os
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded')
from xlib import *
V = ROOT + 'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
out = open(V + 's13_basis_master.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
def nz(s):
    return re.sub(r'\s+', '', s)
def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)
live = {(r['공시분기'], r['항목번호']): r['값'] for r in load(ROOT + 'PL_breakdown.json') if r['원보험사코드'] == 'KR0072'}
head = {(r['공시분기'], r['항목번호']): r['값'] for r in load(V + 'head/PL_breakdown.json') if r['원보험사코드'] == 'KR0072'}
fmap = {'FY2023_Q1': '2023.1Q', 'FY2023_Q2': '2023.2Q', 'FY2023_Q3': '2023.3Q', 'FY2023_Q4': '2023.4Q',
        'FY2024_Q1': '2024.1Q', 'FY2024_Q2': '2024.2Q', 'FY2024_Q3': '2024.3Q', 'FY2024_Q4': '2024.4Q'}
for fy, q in fmap.items():
    d = glob.glob(ROOT + 'data/dart/%s/raw/KR0072*' % fy)[0]
    xs = glob.glob(d + '/*.xml')
    if not xs:
        xs = glob.glob(d + '/**/*.xml', recursive=True)
    p = xs[0]
    txt = open(p, encoding='utf-8', errors='replace').read()
    lines = txt.split('\n')
    W('=====', fy, '->', q, os.path.basename(p))
    annual = fy.endswith('Q4')
    for ln, rows in tables(txt):
        if any(nz(r[0]) == '보험손익' for r in rows) and any(nz(r[0]).startswith('당기순이익') for r in rows) and any(nz(r[0]).startswith('당기총포괄') for r in rows):
            ctx = []
            i = ln - 2
            while i >= 0 and len(ctx) < 4:
                s = strip(lines[i])
                if s:
                    ctx.append(s[:40])
                i -= 1
            inv = [r for r in rows if nz(r[0]) == '투자손익'][0]
            ni = [r for r in rows if nz(r[0]).startswith('당기순이익')][0]
            W('  table L%d ctx=%s' % (ln, ctx))
            W('     투자손익', inv[1:], '| 당기순이익', ni[1:])
    if q.startswith('2023'):
        W('  master', q, 'HEAD 17=%s 24=%s | LIVE 17=%s 24=%s (mn)' % (head.get((q, 17)), head.get((q, 24)), live.get((q, 17)), live.get((q, 24))))
    else:
        W('  master', q, 'LIVE 17=%s 24=%s (mn)' % (live.get((q, 17)), live.get((q, 24))))
