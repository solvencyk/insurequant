# s07: CSM independent re-read (prior-year table of the later filing) + single-quarter rule + chain + FY boundary + opening drift;
#      PL single-quarter rule for ALL 32 items x 4 quarters; PL identities cumulative and single-quarter.
import sys, json, re
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded')
from xlib import *
V = ROOT + 'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)
PL = load(ROOT + 'PL_breakdown.json'); CS = load(ROOT + 'CSM_waterfall.json')
PLH = load(V + 'head/PL_breakdown.json'); CSH = load(V + 'head/CSM_waterfall.json')
def sel(rows, fld):
    return {(r['공시분기'], r['항목번호']): r.get(fld) for r in rows if r['원보험사코드'] == 'KR0072'}
def names(rows):
    return {r['항목번호']: r['항목명'] for r in rows if r['원보험사코드'] == 'KR0072'}
PLv, PLd, PLhv, PLhd = sel(PL, '값'), sel(PL, '값_당분기'), sel(PLH, '값'), sel(PLH, '값_당분기')
CSv, CSd, CShv, CShd = sel(CS, '값'), sel(CS, '값_당분기'), sel(CSH, '값'), sel(CSH, '값_당분기')
gold = load(ROOT + 'data/_gold/user_pl_cells.json')
sd = {(c[1], c[2]): c[3] for c in gold['set_dangi']['cells'] if c[0] == 'KR0072'}
nd = {(c[1], c[2]) for c in gold['null_dangi']['cells'] if c[0] == 'KR0072'}
Q = ['2023.1Q', '2023.2Q', '2023.3Q', '2023.4Q']
out = open(V + 's07_csm_chain.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
def nz(s):
    return re.sub(r'\s+', '', s)
W('PL item names', names(PL)); W('CSM item names', names(CS))
# ---------------- CSM re-read ----------------
LAB = {1: lambda l: l.startswith('1.기초'), 2: lambda l: l.startswith('(3)최초인식한계약'), 3: lambda l: l.startswith('6.보험금융손익'),
       4: lambda l: l.startswith('(1)보험계약마진을조정하는'), 5: lambda l: l.startswith('(1)서비스이전'), 6: lambda l: l.startswith('9.')}
CEXP = {}
W('\n=== CSM independent re-read')
for q, p in FILES.items():
    cand = []
    for ln, rows in tables(read(p)):
        hdr = ' '.join(' '.join(r) for r in rows[:3])
        if '보험계약마진' in hdr and any(nz(r[0]).startswith('1.기초') for r in rows):
            cand.append((ln, rows))
    # prior-year table = the one whose '9.' row label says 전분기말/전반기말/전기말
    pri = []
    for ln, rows in cand:
        r9s = [r for r in rows if nz(r[0]).startswith('9.')]
        if not r9s:
            W(q, 'candidate L%d has no 9. row; header=%r' % (ln, rows[:2])); continue
        r9 = r9s[0]
        W(q, 'CSM-table candidate L%d 9-row label=%r' % (ln, r9[0]))
        if nz(r9[0]).startswith('9.전'):
            pri.append((ln, rows))
    W(q, 'prior-year tables (insurance, reinsurance, [copy2...]):', [ln for ln, _ in pri], 'insurance copy1==copy2:', (pri[0][1] == pri[len(pri)//2][1]) if len(pri) >= 4 else 'single copy')
    rows = pri[0][1]   # first prior-year table = 보험계약 (원수); the second is the reinsurance table
    ci = 3   # 구분 | PVFCF | RA | CSM | total  -> CSM col index 3
    assert nz(rows[1][ci]) == '보험계약마진' or '보험계약마진' in rows[1][ci], rows[1]
    for it, fn in LAB.items():
        m = [r for r in rows if fn(nz(r[0]))]
        if len(m) != 1:
            W(q, it, 'LABEL MATCHES', len(m), [r[0] for r in m]); continue
        CEXP[(q, it)] = num(m[0][ci]) / 100.0
nbad = 0; nchg = 0; nchgok = 0
for q in Q:
    for it in range(1, 7):
        e = CEXP.get((q, it)); mv = CSv.get((q, it)); hv = CShv.get((q, it))
        tol = 0.0051 if q in ('2023.1Q', '2023.2Q') else 0.0501
        ok = e is not None and mv is not None and abs(mv - e) <= tol
        ch = mv != hv
        nbad += (not ok); nchg += ch; nchgok += (ch and ok)
        W('CSM cum', q, it, 'OK' if ok else 'MISMATCH', 'changed' if ch else 'same', 'printed(억)=%.4f' % e, 'master=', mv, 'head=', hv, 'diff=%.4f' % (mv - e))
W('CSM cumulative compared 24, mismatches', nbad, '| changed vs HEAD', nchg, 'of which equal own reread', nchgok)
# ---------------- CSM single-quarter rule + chain ----------------
def csm_dangi(q, i):
    qi = Q.index(q)
    if qi == 0:
        return CSv[(q, i)]
    if i == 1:
        return CSv[(Q[qi - 1], 6)]
    if i == 6:
        return CSv[(q, 6)]
    return CSv[(q, i)] - CSv[(Q[qi - 1], i)]
W('\n=== CSM single-quarter stored vs rule (opening = prior closing; flow = cum diff)')
bad = 0
for q in Q:
    for i in range(1, 7):
        e = csm_dangi(q, i); a = CSd[(q, i)]
        ok = abs(e - a) <= 0.0051 + (0.05 if q != '2023.1Q' and q != '2023.2Q' else 0)
        bad += (not ok)
        W('  ', q, i, 'stored', a, 'rule %.4f' % e, 'OK' if ok else 'DIFF', 'changed' if a != CShd[(q, i)] else 'same')
W('CSM single-quarter mismatches', bad)
W('\n=== CSM closure (cumulative): open + new + interest + assumptions + amort - close')
for q in Q:
    o, n, ii, a, am, cl = [CSv[(q, i)] for i in range(1, 7)]
    W('  ', q, 'resid %.3f' % (o + n + ii + a + am - cl))
W('=== CSM single-quarter closure')
for q in Q:
    ds = [CSd[(q, i)] for i in range(1, 7)]
    W('  ', q, 'resid %.3f' % (ds[0] + ds[1] + ds[2] + ds[3] + ds[4] - ds[5]))
W('=== opening drift: FY opening (item1 cum) per quarter; boundary to 2024.1Q')
W('  openings cum', [CSv[(q, 1)] for q in Q], 'max-min', max(CSv[(q, 1)] for q in Q) - min(CSv[(q, 1)] for q in Q))
W('  printed opening (억)', [CEXP[(q, 1)] for q in Q])
W('  2023.4Q close', CSv[('2023.4Q', 6)], '| 2024.1Q opening cum', CSv.get(('2024.1Q', 1)), '2024.1Q single opening', CSd.get(('2024.1Q', 1)))
for q in ('2024.1Q', '2024.2Q', '2024.3Q', '2024.4Q'):
    W('  ', q, [CSv.get((q, i)) for i in range(1, 7)])
W('  HEAD opening cum', [CShv[(q, 1)] for q in Q], 'HEAD 2023.4Q close', CShv[('2023.4Q', 6)])
W('  quarter-to-quarter: closing(q-1) vs single opening(q):', [(Q[k], CSv[(Q[k], 6)], CSd[(Q[k + 1], 1)]) for k in range(3)])
# ---------------- PL single-quarter rule, all items ----------------
def pl_dangi(q, i):
    if (q, i) in sd:
        return sd[(q, i)]
    if (q, i) in nd:
        return None
    cur = PLv.get((q, i))
    if cur is None:
        return None
    qi = Q.index(q)
    if qi == 0:
        return cur
    prev = PLv.get((Q[qi - 1], i))
    return None if prev is None else cur - prev
W('\n=== PL 값_당분기 vs rule (pin / cum - prior cum) for all items, 4 quarters')
nb = 0; n = 0; chg = 0
for q in Q:
    for i in sorted({k[1] for k in PLv if k[0] == q}):
        e = pl_dangi(q, i); a = PLd.get((q, i))
        n += 1
        if (e is None) != (a is None) or (e is not None and abs(e - a) > 0.0101):
            nb += 1; W('  DIFF', q, i, 'stored', a, 'rule', e, 'head', PLhd.get((q, i)))
        if a != PLhd.get((q, i)):
            chg += 1
W('PL single-quarter cells checked', n, 'rule mismatches', nb, 'changed vs HEAD', chg)
# ---------------- PL identities ----------------
def ident(get, tag):
    ids = {
        '2=3+8': (2, [3, 8]), '3=4+5+6+7': (3, [4, 5, 6, 7]), '8=9+10+11+12': (8, [9, 10, 11, 12]),
        '1=2+13+14+15-16': (1, [2, 13, 14, 15, -16]), '17=18+19': (17, [18, 19]), '20=1+17': (20, [1, 17]),
        '22=20+21': (22, [20, 21]), '31=24+25': (31, [24, 25]), '25=26..30+32': (25, [26, 27, 28, 29, 30, 32])}
    W('--- PL identities', tag, '(residual lhs-rhs, mn; |r|>0.02 flagged)')
    for q in Q:
        row = []
        for nme, (l, rs) in ids.items():
            lv = get(q, l)
            if lv is None:
                row.append((nme, 'LHS-none')); continue
            tot = 0; miss = 0
            for r in rs:
                v = get(q, abs(r))
                if v is None:
                    miss += 1; continue
                tot += v if r > 0 else -v
            row.append((nme, round(lv - tot, 4), ('miss%d' % miss) if miss else ''))
        W('  ', q, row)
    # tax identity
ident(lambda q, i: PLv.get((q, i)), 'cumulative')
ident(lambda q, i: PLd.get((q, i)), 'single-quarter')
W('item 23 tax: 22-24 vs 23 cum', [(q, round((PLv[(q, 22)] or 0) - (PLv[(q, 24)] or 0), 6), PLv.get((q, 23))) for q in Q])
W('\nPL items 4..14 cum (mn)')
for q in Q:
    W('  ', q, {i: PLv.get((q, i)) for i in range(3, 15)})
    W('   HEAD', q, {i: PLhv.get((q, i)) for i in range(3, 15)})
