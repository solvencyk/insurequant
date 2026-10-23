# s15: sum of the four single quarters vs the annual cumulative (4Q 값), live vs HEAD, PL + CSM flows; and basis-gap evidence numbers.
import json, sys
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded')
from xlib import *
V = ROOT + 'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)
out = open(V + 's15_sigma.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
Q = ['2023.1Q', '2023.2Q', '2023.3Q', '2023.4Q']
def sel(rows, fld):
    return {(r['공시분기'], r['항목번호']): r.get(fld) for r in rows if r['원보험사코드'] == 'KR0072'}
for lab, path in (('LIVE', ROOT), ('HEAD', V + 'head/')):
    d = sel(load(path + 'PL_breakdown.json'), '값_당분기'); c = sel(load(path + 'PL_breakdown.json'), '값')
    W('== PL', lab, ': sum of 4 single quarters minus annual cum (mn); only |diff|>0.01 listed')
    for i in range(1, 33):
        vals = [d.get((q, i)) for q in Q]
        ann = c.get(('2023.4Q', i))
        if ann is None or any(v is None for v in vals):
            W('   item', i, 'incomplete singles/annual', vals, ann); continue
        s = sum(vals)
        if abs(s - ann) > 0.01:
            W('   item', i, 'sum=%.6f annual=%.6f diff=%.6f' % (s, ann, s - ann))
    W('   (all other complete items: diff <= 0.01)')
for lab, path in (('LIVE', ROOT), ('HEAD', V + 'head/')):
    d = sel(load(path + 'CSM_waterfall.json'), '값_당분기'); c = sel(load(path + 'CSM_waterfall.json'), '값')
    W('== CSM', lab, ': sum of single-quarter flows (items 2..5) minus annual (억)')
    for i in (2, 3, 4, 5):
        s = sum(d[(q, i)] for q in Q); ann = c[('2023.4Q', i)]
        W('   item', i, 'sum=%.3f annual=%.3f diff=%.3f' % (s, ann, s - ann))
# basis-gap evidence (hard numbers from the filings): H1 report 연결 vs 별도, Q3-implied 6M
W('\nbasis evidence (won): H1 report 투자손익 6M: 별도 45,706,602,817 ; 연결 44,979,679,823 ; diff', 45706602817 - 44979679823)
W('Q3 report: 9M cum -13,718,605,641 minus 3m (-58,698,285,464) = implied 6M', -13718605641 - (-58698285464), '(== H1 연결 44,979,679,823 ?)', -13718605641 + 58698285464 == 44979679823)
W('Q3 report: 9M NI -13,527,197,644 minus 3m (-75,424,704,649) = implied 6M NI', -13527197644 + 75424704649, '(== H1 연결 NI 61,897,507,005 ?)', -13527197644 + 75424704649 == 61897507005, '; H1 별도 NI 62,624,429,999')
W('FY2023 annual: original filing 별도 NI 24,019,133,498 ; 연결 NI 23,949,587,393 ; diff', 24019133498 - 23949587393, '| 투자손익 별도 -18,358,723,814 ; 연결 -18,428,269,919 ; diff', -18358723814 + 18428269919)
