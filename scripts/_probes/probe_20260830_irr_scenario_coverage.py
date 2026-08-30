import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')
rows = json.load(open('kics_disclosure.json', encoding='utf-8'))
LBL = {41:'충격전 순자산', 42:'평균회귀', 43:'금리상승', 44:'금리하락', 45:'평탄', 46:'경사'}
idx = defaultdict(dict); names = {}
for r in rows:
    idx[(r['원보험사코드'], r['공시분기'])][r['항목번호']] = r.get('값')
    names[r['원보험사코드']] = r['원수사명']
qs = sorted({r['공시분기'] for r in rows})
even = [q for q in qs if q.endswith(('2Q','4Q'))]
print(f"전체 {len(names)}사 x {len(qs)}분기 · 짝수분기 {len(even)}개 (시나리오표는 반기·연차만 공시)\n")
print(f"{'회사':<20}" + "".join(f"{q[2:]:>8}" for q in even))
full = part = none = 0
for c in sorted(names):
    line = f"{names[c]:<20}"
    for q in even:
        m = idx.get((c,q), {})
        n = sum(1 for i in LBL if m.get(i) is not None)
        line += f"{(str(n)+'/6' if n else '  -'):>8}"
        if n == 6: full += 1
        elif n: part += 1
        else: none += 1
    print(line)
print(f"\n짝수분기 셀 {len(names)*len(even)}개 중  완비(6/6)={full}  부분={part}  없음={none}")
print(f"  -> 유도 가능 비율 {full/(len(names)*len(even)):.1%}")
by_q = {}
for q in even:
    by_q[q] = sum(1 for c in names if sum(1 for i in LBL if idx.get((c,q),{}).get(i) is not None) == 6)
print("\n분기별 완비 회사수:", {q: by_q[q] for q in even})
