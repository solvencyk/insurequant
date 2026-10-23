# s11: headline effects in 억원 (HEAD -> live), cumulative and single-quarter, KR0072 FY2023; also HEAD internal-consistency of 2Q item 1.
import json
R = 'C:/Users/sangwook.cho/Desktop/insurequant/'
V = R + 'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)
out = open(V + 's11_headline.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
def sel(rows, fld):
    return {(r['공시분기'], r['항목번호']): r.get(fld) for r in rows if r['원보험사코드'] == 'KR0072'}
PLn, PLo = load(R + 'PL_breakdown.json'), load(V + 'head/PL_breakdown.json')
CSn, CSo = load(R + 'CSM_waterfall.json'), load(V + 'head/CSM_waterfall.json')
Q = ['2023.1Q', '2023.2Q', '2023.3Q', '2023.4Q']
def f(x):
    return 'blank' if x is None else '%.2f' % (x / 100.0)
for fld, lab in (('값', '누계(cumulative)'), ('값_당분기', '단일분기(single quarter)')):
    n, o = sel(PLn, fld), sel(PLo, fld)
    W('== PL', lab, '억원 old -> new (delta)')
    for it, nm in ((1, '보험손익'), (17, '투자손익'), (24, '당기순이익'), (25, '기타포괄손익'), (31, '총포괄손익'), (20, '영업이익'), (16, '기타사업비용'), (4, '원수 CSM상각(PL)')):
        row = []
        for q in Q:
            a, b = o.get((q, it)), n.get((q, it))
            d = '' if (a is None or b is None) else ' (%+.2f)' % ((b - a) / 100.0)
            row.append('%s: %s -> %s%s' % (q, f(a), f(b), d))
        W('  ', it, nm, ' | '.join(row))
for fld, lab in (('값', '누계'), ('값_당분기', '단일분기')):
    n, o = sel(CSn, fld), sel(CSo, fld)
    W('== CSM', lab, '억원 old -> new (delta)')
    for it, nm in ((1, '기초 CSM'), (2, '신계약 CSM'), (3, '이자 부리'), (4, '가정 및 경험 조정'), (5, 'CSM 상각'), (6, '기말 CSM')):
        row = []
        for q in Q:
            a, b = o.get((q, it)), n.get((q, it))
            d = '' if (a is None or b is None) else ' (%+.2f)' % (b - a)
            row.append('%s: %s -> %s%s' % (q, '%.2f' % a, '%.2f' % b, d))
        W('  ', it, nm, ' | '.join(row))
o = sel(PLo, '값'); n = sel(PLn, '값')
W('HEAD 2Q: item1 %.2f ; item2 %.2f ; item16 %.2f ; item2+13+14+15-16 = %.2f ; residual (1 - that) = %.2f mn' % (
    o[('2023.2Q', 1)], o[('2023.2Q', 2)], o[('2023.2Q', 16)], o[('2023.2Q', 2)] - o[('2023.2Q', 16)], o[('2023.2Q', 1)] - (o[('2023.2Q', 2)] - o[('2023.2Q', 16)])))
W('LIVE 2Q: item1 %.4f ; item2-item16 = %.4f' % (n[('2023.2Q', 1)], n[('2023.2Q', 2)] - n[('2023.2Q', 16)]))
W('2Q item 1 change (억): %.2f ; of which restatement of item 2: %.2f ; item16 effect: %.2f' % (
    (n[('2023.2Q', 1)] - o[('2023.2Q', 1)]) / 100, (n[('2023.2Q', 2)] - o[('2023.2Q', 2)]) / 100, -(n[('2023.2Q', 16)] - o[('2023.2Q', 16)]) / 100))
# 2024 quarters untouched check
for fld in ('값', '값_당분기'):
    a = {k: v for k, v in sel(PLo, fld).items() if not k[0].startswith('2023.')}
    b = {k: v for k, v in sel(PLn, fld).items() if not k[0].startswith('2023.')}
    W('PL non-2023 cells identical:', fld, a == b, len(a))
    a = {k: v for k, v in sel(CSo, fld).items() if not k[0].startswith('2023.')}
    b = {k: v for k, v in sel(CSn, fld).items() if not k[0].startswith('2023.')}
    W('CSM non-2023 cells identical:', fld, a == b, len(a))
