# -*- coding: utf-8 -*-
"""Independent re-read (regex table parser of vlib, no p2lib / no pass3 reader) of the 동양생명 2024.2Q reinsurance cells and the NH농협손해보험 FY2023 1Q/2Q statement cells against the LIVE master after the pass3 apply."""
import sys
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent')
from vlib import *
from mlib import *
sys.stdout.reconfigure(encoding='utf-8')
R3 = 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/'
out = open(R3 + 'v20_dy_nh.txt', 'w', encoding='utf-8')
def W(s):
    print(s); out.write(s + '\n')
bad = 0; tot = 0
def chk(name, raw, master, tol=0.5e-3):
    global bad, tot
    tot += 1
    ok = master is not None and abs(raw - master) <= tol
    if not ok: bad += 1
    W('%s %-52s raw=%s master=%s' % ('OK ' if ok else 'BAD', name, raw, master))
# ---------------- 동양생명 KR0087 2024.2Q <- FY2025_Q2 prior-period (second) analysis tables
p = path('2025.2Q', 'KR0087'); W('동양 file ' + p)
T = tables(p)
def label_rows(T, label_sub):
    res = []
    for ln, rows in T:
        for lr, c in rows:
            if any(label_sub in x for x in c if x):
                res.append((ln, lr, c))
    return res
def nums_of(c):
    return [num(x) for x in c if num(x) is not None]
csm = label_rows(T, '재보험비용, 서비스의 이전으로 당기손익에 인식한 보험계약마진')
ra = label_rows(T, '재보험비용, 비금융위험에 대한 위험조정의 변동분')
exp = label_rows(T, '재보험비용, 예상 보험금')
act = label_rows(T, '재보험수익, 발생한 보험금')
W('counts csm=%d ra=%d exp=%d act=%d' % (len(csm), len(ra), len(exp), len(act)))
# the separate pair sits in the second half of the file: take the last two of each (document order [당반기, 전반기])
cur_csm, pri_csm = nums_of(csm[-2][2])[-1], nums_of(csm[-1][2])[-1]
cur_ra, pri_ra = nums_of(ra[-2][2])[-1], nums_of(ra[-1][2])[-1]
cur_exp, pri_exp = nums_of(exp[-2][2])[-1], nums_of(exp[-1][2])[-1]
cur_act, pri_act = nums_of(act[-2][2])[-1], nums_of(act[-1][2])[-1]
W('current pair (cum): csm %s ra %s exp %s act %s ; prior pair: csm %s ra %s exp %s act %s' % (cur_csm, cur_ra, cur_exp, cur_act, pri_csm, pri_ra, pri_exp, pri_act))
chk('sanity 2025.2Q item9 = -|csm cur|', -abs(cur_csm), mv('KR0087', '2025.2Q', 9))
chk('sanity 2025.2Q item10 = -|ra cur|', -abs(cur_ra), mv('KR0087', '2025.2Q', 10))
chk('sanity 2025.2Q item11 = |act|-|exp| cur', abs(cur_act) - abs(cur_exp), mv('KR0087', '2025.2Q', 11))
chk('2024.2Q item9 = -|csm prior|', -abs(pri_csm), mv('KR0087', '2024.2Q', 9))
chk('2024.2Q item10 = -|ra prior|', -abs(pri_ra), mv('KR0087', '2024.2Q', 10))
chk('2024.2Q item11 = |act|-|exp| prior', abs(pri_act) - abs(pri_exp), mv('KR0087', '2024.2Q', 11))
i8 = mv('KR0087', '2024.2Q', 8)
chk('2024.2Q item12 = 8-(9+10+11)', i8 - (-abs(pri_csm) - abs(pri_ra) + abs(pri_act) - abs(pri_exp)), mv('KR0087', '2024.2Q', 12))
# ---------------- NH농협손해보험 KR0032: prior cumulative column (4th numeric) of FY2024_Q1 / Q2 / Q3 separate statements
for q, fq in (('2023.1Q', '2024.1Q'), ('2023.2Q', '2024.2Q'), ('2023.3Q', '2024.3Q')):
    p = path(fq, 'KR0032'); W('NH file ' + p)
    T = tables(p)
    stmt = [(ln, rows) for ln, rows in T if any(c and c[0].replace(' ', '').startswith('VI.법인세차감전순이익') for _, c in rows)]
    assert len(stmt) == 1, len(stmt)
    rows = stmt[0][1]
    def r(prefix):
        for lr, c in rows:
            if c and c[0].replace(' ', '').startswith(prefix):
                v = [num(x) for x in c[1:] if num(x) is not None]
                return v
        raise KeyError(prefix)
    pc = lambda prefix: r(prefix)[3] / 1e6
    W('%s statement table@L%d' % (q, stmt[0][0]))
    items = {22: pc('VI.법인세차감전순이익'), 23: pc('VII.법인세비용'), 25: pc('IX.기타포괄손익'), 31: pc('X.총포괄손익')}
    for pre in ('VIII.당기순이익', 'VIII.반기순이익', 'VIII.분기순이익'):
        try:
            items[24] = pc(pre); break
        except KeyError:
            pass
    items[20] = pc('III.영업이익'); items[21] = pc('IV.영업외수익') - pc('V.영업외비용')
    for it, v in sorted(items.items()):
        if q == '2023.2Q' and it in (20, 21):
            continue
        if q == '2023.3Q' and it in (20, 21):
            continue
        if q == '2023.1Q' and it in (25, 31):
            pass
        chk('%s item%d prior cum' % (q, it), v, mv('KR0032', q, it, '값'))
    if q == '2023.2Q':
        # OCI leaves by label under the OCI block
        lab = {26: '기타포괄손익-공정가치측정금융자산관련손익', 28: '현금흐름위험회피파생상품평가손익', 27: '보험금융순손익', 30: '재보험금융순손익', 29: '기타포괄손익-공정가치측정유가증권평가손익'}
        for it, l in lab.items():
            chk('%s item%d prior cum' % (q, it), pc(l), mv('KR0032', q, it, '값'))
        chk('%s item32 prior cum (확정급여제도의 재측정요소)' % q, pc('확정급여제도의재측정요소'), mv('KR0032', q, 32, '값'))
W('TOTAL %d bad %d' % (tot, bad))
out.close()
