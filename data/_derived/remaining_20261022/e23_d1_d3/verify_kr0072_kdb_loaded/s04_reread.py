# s04: own independent re-read of KDB (KR0072) FY2023 from the NEXT-YEAR filings (prior-year columns), label based, no use of the parser plan.
# Compares against the LIVE (post-load) master and tags whether each cell changed vs HEAD.
import sys, json, re, collections
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


PLv, PLd, PLhv, PLhd = sel(PL, '값'), sel(PL, '값_당분기'), sel(PLH, '값'), sel(PLH, '값_당분기')
gold = load(ROOT + 'data/_gold/user_pl_cells.json')
sd = {(c[1], c[2]): c[3] for c in gold['set_dangi']['cells'] if c[0] == 'KR0072'}
Q = ['2023.1Q', '2023.2Q', '2023.3Q', '2023.4Q']
out = open(V + 's04_reread.txt', 'w', encoding='utf-8')


def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')


def nz(s):
    return re.sub(r'\s+', '', s)


stm = {}
for q, p in FILES.items():
    T = [(ln, rows) for ln, rows in tables(read(p))
         if any(nz(r[0]) == '보험손익' for r in rows)
         and any(nz(r[0]).startswith('당기순이익') for r in rows)
         and any(nz(r[0]).startswith('당기총포괄') or nz(r[0]).startswith('총포괄') for r in rows)]
    W('==', q, ': statement tables found at lines', [ln for ln, _ in T], 'header', T[0][1][:2])
    W('   copies identical:', all(t[1] == T[0][1] for t in T))
    rows = T[-1][1]   # last table = 4-2 포괄손익계산서 (별도); the first copy in 1Q/2Q files is the 2-2 연결
    annual = (q == '2023.4Q')
    cum_i = 2 if annual else 4
    m3_i = None if annual else 3
    occ = collections.OrderedDict()
    for r in rows:
        if len(r) < 2:
            continue
        lab = nz(r[0])
        try:
            vc = num(r[cum_i]) / 1e6
            v3 = num(r[m3_i]) / 1e6 if m3_i else None
        except Exception:
            continue
        occ.setdefault(lab, []).append((vc, v3))
    stm[q] = occ


def first(occ, pref, exact=False, k=0):
    for lab, v in occ.items():
        if (lab == pref) if exact else lab.startswith(pref):
            return v[k] if len(v) > k else None
    return None


def getall(occ, pref, exact=False):
    r = []
    for lab, v in occ.items():
        if (lab == pref) if exact else lab.startswith(pref):
            r += v
    return r


def sub(a, b):
    return tuple((None if (x is None or y is None) else x - y) for x, y in zip(a, b))


def addp(a, b):
    return tuple((None if (x is None or y is None) else x + y) for x, y in zip(a, b))


EXP = {}
for q in Q:
    o = stm[q]
    for item, pref, ex in [(1, '보험손익', True), (16, '기타사업비용', True), (17, '투자손익', True), (20, '영업이익', False),
                           (21, '영업외손익', True), (22, '법인세차감전순이익', False), (24, '당기순이익', False),
                           (25, '당기기타포괄손익', True), (27, '보험계약자산(부채)순금융손익', True),
                           (28, '현금흐름위험회피파생상품평가손익', True), (30, '재보험계약자산(부채)순금융손익', True),
                           ]:
        EXP[(q, item)] = first(o, pref, ex)
    EXP[(q, 23)] = next((v[0] for lab, v in o.items() if lab.startswith('법인세') and not lab.startswith('법인세차감')), None)
    t31 = [v for lab, v in o.items() if lab.startswith('당기총포괄') or lab.startswith('총포괄')]
    EXP[(q, 31)] = t31[0][0] if t31 else None
    if EXP[(q, 31)] is not None:
        EXP[(q, 31)] = t31[0][0]
    fv = getall(o, '기타포괄손익-공정가치측정금융자산평가손익', True)
    EXP[(q, 26)] = fv[0] if len(fv) > 0 else None
    EXP[(q, 29)] = fv[1] if len(fv) > 1 else None
    W(q, 'FVOCI rows (cum,3m):', fv)
    ins = first(o, '보험수익', True); insx = first(o, '보험비용', True)
    re_i = first(o, '재보험수익', True); re_x = first(o, '재보험비용', True)
    i3 = sub(ins, insx); i8 = sub(re_i, re_x); i2 = addp(i3, i8)
    EXP[(q, 3)] = i3; EXP[(q, 8)] = i8; EXP[(q, 2)] = i2
    ff = first(o, '보험금융수익', True); rf = first(o, '재보험금융수익', True)
    fc = first(o, '보험금융비용', True); rc = first(o, '재보험금융비용', True)
    i19 = sub(addp(ff, rf), addp(fc, rc)); EXP[(q, 19)] = i19
    EXP[(q, 18)] = sub(EXP[(q, 17)], i19)
    oci = EXP[(q, 25)]
    s = [EXP[(q, k)] for k in (26, 27, 28, 29, 30)]
    EXP[(q, 32)] = tuple(None if (oci[j] is None or any(t[j] is None for t in s)) else oci[j] - sum(t[j] for t in s) for j in range(2))
    EXP[(q, 15)] = (0.0, 0.0)
    W(q, 'derived inputs ins,insx,re_i,re_x', ins, insx, re_i, re_x, '| ff,rf,fc,rc', ff, rf, fc, rc)

for q, p in FILES.items():
    vals = []
    for ln, rows in tables(read(p)):
        for r in rows:
            if '제공된서비스의보험계약마진' in nz(r[0]):
                vals.append((ln, r))
    W(q, 'CSM amort rows', vals)
    r = vals[0][1]
    ci = 2 if q in ('2023.1Q', '2023.4Q') else 4
    mi = None if q in ('2023.1Q', '2023.4Q') else 3
    EXP[(q, 4)] = (num(r[ci]), num(r[mi]) if mi else None)
    W('   copies identical:', all(v[1] == vals[0][1] for v in vals))

W('\n=== PL cumulative: independent expectation vs LIVE master 값 (tol 0.0061 mn)')
nbad = 0; ncmp = 0; nchg_ok = 0; nchg = 0
for q in Q:
    for item in sorted({k[1] for k in EXP if k[0] == q}):
        e = EXP[(q, item)]
        ev = e[0] if isinstance(e, tuple) else e
        mv = PLv.get((q, item)); hv = PLhv.get((q, item))
        if ev is None:
            W(q, item, 'EXP-NONE', 'master=', mv, 'head=', hv); continue
        ok = mv is not None and (abs(mv - ev) <= 0.0061 or (item == 23 and abs(mv + ev) <= 0.0061))
        changed = (mv != hv)
        ncmp += 1; nbad += (not ok)
        if changed:
            nchg += 1; nchg_ok += ok
        W(q, item, 'OK' if ok else 'MISMATCH', 'changed' if changed else 'same', 'exp=%.6f' % ev, 'master=', mv, 'head=', hv)
W('compared=%d mismatches=%d | changed-vs-HEAD cells among compared: %d, of which match own reread: %d' % (ncmp, nbad, nchg, nchg_ok))
chg_pl = [k for k in PLv if k[0] in Q and PLv[k] != PLhv.get(k)]
W('changed PL cum cells total', len(chg_pl), 'not covered by own reread:', [k for k in chg_pl if k not in EXP or EXP[k] is None or (isinstance(EXP[k], tuple) and EXP[k][0] is None)])

W('\n=== PL single-quarter: master 값_당분기 vs 3-month column printed in same later filing (interim quarters only)')
n3 = 0; b3 = 0
for q in Q[:3]:
    for item in sorted({k[1] for k in EXP if k[0] == q}):
        e = EXP[(q, item)]
        if not isinstance(e, tuple) or e[1] is None:
            continue
        d = PLd.get((q, item)); hd = PLhd.get((q, item)); pin = sd.get((q, item))
        ok = d is not None and (abs(d - e[1]) <= 0.0061 or (item == 23 and abs(d + e[1]) <= 0.0061))
        n3 += 1; b3 += (not ok)
        W(q, item, '3m_printed=%.6f' % e[1], 'master_dangi=', d, 'pin=', pin, 'OK' if ok else 'DIFF', 'changed' if d != hd else 'same')
W('3m compared', n3, 'diff', b3)
json.dump({'%s|%d' % (k[0], k[1]): v for k, v in EXP.items()}, open(V + 's04_exp.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('done')
