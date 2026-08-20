# -*- coding: utf-8 -*-
"""독립 mmult 전수 감사 — 3개 축 × {적용전, 적용후}.

  A) 생명장기 하위 : item17 = sqrt(V'·R7·V),  V=[29..35]
  B) 시장 하위     : item19 = sqrt(V'·M·V),   V=[36..40]
  C) 기본요구자본  : item15 = sqrt(V'·R4·V) + item21,  V=[17,18,19,20]

행렬은 룰엔진에서 그대로 import(재타이핑 금지). 결측은 SKIP 으로 세되 **숨기지 않고 집계**한다.
"""
import json, sys, collections
import numpy as np
from pathlib import Path
ROOT = Path('.').resolve(); sys.path.insert(0, str(ROOT))
from src.solvency.validation.kics_json_rules import R4, R7, MARKET_M, _diversified_sqrt

def num(x):
    if x is None: return None
    if isinstance(x, (int, float)): return float(x)
    s = str(x).strip().replace(',', '').replace('△', '-').replace('−', '-')
    if s in ('', '-', 'None'): return None
    try: return float(s)
    except ValueError: return None

rows = json.load(open('kics_disclosure.json', encoding='utf-8'))
buckets = collections.defaultdict(dict)
names = {}
for r in rows:
    co, q, it = r.get('원보험사코드'), r.get('공시분기'), r.get('항목번호')
    names[co] = r.get('원수사명')
    buckets[(co, q)][it] = (num(r.get('값')), num(r.get('값_적용후')))

AXES = [
    ('A 생명장기(29-35)->17', list(range(29, 36)), 17, R7,   'life'),
    ('B 시장(36-40)->19',      list(range(36, 41)), 19, MARKET_M, 'mkt'),
    ('C 기본요구자본(17-20)+21->15', [17, 18, 19, 20], 15, R4, 'scr'),
]
POST = {'적용전': 0, '적용후': 1}
report = collections.defaultdict(lambda: collections.Counter())
fails = collections.defaultdict(list)

for (co, q), b in sorted(buckets.items()):
    for axis_name, subs, parent, M, kind in AXES:
        for pname, pi in POST.items():
            parent_v = b.get(parent, (None, None))[pi]
            vec = [b.get(s, (None, None))[pi] for s in subs]
            key = (axis_name, pname)
            if parent_v is None:
                report[key]['부모결측'] += 1; continue
            if any(v is None for v in vec):
                nmiss = sum(1 for v in vec if v is None)
                report[key][f'하위결측'] += 1
                continue
            expected = _diversified_sqrt(np.array(vec, dtype=float), M)
            if kind == 'scr':
                op = b.get(21, (None, None))[pi]
                if op is None:
                    report[key]['하위결측'] += 1; continue
                expected += op
            tol = max(2.0, 0.05 * abs(expected))
            diff = parent_v - expected
            if abs(diff) <= tol:
                report[key]['PASS'] += 1
            else:
                report[key]['FAIL'] += 1
                fails[key].append((co, names.get(co, ''), q, parent_v, expected, diff,
                                   abs(diff) / max(1e-9, abs(expected)) * 100))

L = []
for axis_name, subs, parent, M, kind in AXES:
    for pname in POST:
        k = (axis_name, pname)
        c = report[k]
        tot = sum(c.values())
        comp = c['PASS'] + c['FAIL']
        rate = (c['PASS'] / comp * 100) if comp else 0.0
        L.append(f"{axis_name:<30} {pname}  전체 {tot:4d} | 계산가능 {comp:4d} "
                 f"| PASS {c['PASS']:4d} FAIL {c['FAIL']:3d} ({rate:5.1f}%) "
                 f"| 부모결측 {c['부모결측']:4d} 하위결측 {c['하위결측']:4d}")
    L.append("")
L.append("=" * 100)
L.append("FAIL 상세 (오차율 큰 순, 축별 최대 12건)")
for k in sorted(fails, key=lambda z: (z[0], z[1])):
    fl = sorted(fails[k], key=lambda x: -x[6])
    L.append(f"\n--- {k[0]} / {k[1]}  FAIL {len(fl)}건")
    for co, nm, q, act, exp, diff, pct in fl[:12]:
        L.append(f"    {co} {nm:<14} {q:<9} 공시={act:>12,.2f} 계산={exp:>12,.2f} "
                 f"차={diff:>11,.2f} ({pct:5.1f}%)")
Path(sys.argv[1]).write_text("\n".join(L), encoding='utf-8')
print("done")
