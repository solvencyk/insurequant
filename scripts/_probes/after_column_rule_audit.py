# -*- coding: utf-8 -*-
"""K-ICS '적용전에 도는 룰을 적용후에도 전부 도는가' 전수 감사 (validation, 2026-08-21).

owner 지시(2026-07-07 "모든 룰은 적용전·적용후 동일 적용")가 실제로 지켜지는지 확인한다.

**측정 원칙 — 결측과 결함을 절대 섞지 않는다.**
룰엔진은 입력이 없으면 RED 를 내는 관례(커버리지 census)라, 적용후 컬럼에 그대로 돌리면
'적용후가 원래 없는 항목'(item4~13·41~46 은 적용후 커버리지 47~52%)이 전부 결함으로 잡힌다.
그래서 여기서는 **입력이 전부 존재하는 버킷만** 판정하고, 나머지는 `계산불가` 로 따로 센다.

상관행렬·IRR 공식은 룰엔진에서 import/전사한다(자체 재해석 금지 — 모듈 docstring 참조).
"""
import json, sys, collections
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.solvency.validation.kics_json_rules import R4, R7, MARKET_M, _diversified_sqrt

def num(x):
    if x is None: return None
    if isinstance(x, (int, float)): return float(x)
    s = str(x).strip().replace(',', '').replace('△', '-').replace('−', '-')
    if s in ('', '-', 'None'): return None
    try: return float(s)
    except ValueError: return None

def load(path):
    rows = json.loads(Path(path).read_text(encoding='utf-8'))
    b = collections.defaultdict(dict); names = {}
    for r in rows:
        names[r.get('원보험사코드')] = r.get('원수사명')
        b[(r.get('원보험사코드'), r.get('공시분기'))][r.get('항목번호')] = (
            num(r.get('값')), num(r.get('값_적용후')))
    return b, names

SUM_TOL   = lambda e: max(2.0, 0.005 * abs(e))
RATIO_TOL = lambda e: 2.0
MM_TOL    = lambda e: max(2.0, 0.05 * abs(e))

def rules():
    def r1(g):  return g(2) + g(3),                                   SUM_TOL, 1
    def r2(g):  return sum(g(i) for i in range(5, 12)),               SUM_TOL, 4
    def r4(g):  return _diversified_sqrt(np.array([g(17), g(18), g(19), g(20)]), R4) + g(21), MM_TOL, 15
    def r5(g):  return g(15) - g(22) + g(23),                         SUM_TOL, 14
    def r6(g):  return sum(g(i) for i in (17, 18, 19, 20, 21)) - g(15), SUM_TOL, 16
    def r7(g):  return (g(1) / g(14) * 100) if g(14) else None,       RATIO_TOL, 27
    def r8(g):  return (g(2) / g(14) * 100) if g(14) else None,       RATIO_TOL, 28
    def life(g):return _diversified_sqrt(np.array([g(i) for i in range(29, 36)]), R7), MM_TOL, 17
    def mkt(g): return _diversified_sqrt(np.array([g(i) for i in range(36, 41)]), MARKET_M), MM_TOL, 19
    def irr(g):
        base = g(41)
        r_up, r_dn = max(base - g(43), 0.0), max(base - g(44), 0.0)
        r_fl, r_st = max(base - g(45), 0.0), max(base - g(46), 0.0)
        return float(np.sqrt(max(r_up, r_dn) ** 2 + max(r_fl, r_st) ** 2)) + (base - g(42)), MM_TOL, 36
    return [
        ("R1  가용자본=기본+보완",      r1,   [2, 3]),
        ("R2  순자산합(5-11)",          r2,   list(range(5, 12))),
        ("R4  기본요구자본 mmult",       r4,   [17, 18, 19, 20, 21]),
        ("R5  기준금액=15-22+23",        r5,   [15, 22, 23]),
        ("R6  분산효과",                 r6,   [17, 18, 19, 20, 21, 15]),
        ("R7  지급여력비율",             r7,   [1, 14]),
        ("R8  기본자본비율",             r8,   [2, 14]),
        ("8_life 생명장기 mmult",        life, list(range(29, 36))),
        ("19_market 시장 mmult",         mkt,  list(range(36, 41))),
        ("36_irr 금리위험",              irr,  [41, 42, 43, 44, 45, 46]),
    ]

def audit(path):
    b, names = load(path)
    out = []
    for label, fn, ins in rules():
        for col, idx in (('적용전', 0), ('적용후', 1)):
            ok = fail = skip = 0; worst = []
            for (co, q), m in b.items():
                g = lambda i: m.get(i, (None, None))[idx]
                tgt_needed = fn.__code__  # noqa
                vals = [g(i) for i in ins]
                if any(v is None for v in vals): skip += 1; continue
                try:
                    exp, tolf, tgt_item = fn(g)
                except Exception:
                    skip += 1; continue
                act = g(tgt_item)
                if exp is None or act is None: skip += 1; continue
                d = abs(act - exp)
                if d <= tolf(exp): ok += 1
                else:
                    fail += 1
                    worst.append((abs(d / max(1e-9, abs(exp))) * 100, co, names.get(co, ''), q, act, exp, act - exp))
            out.append((label, col, ok, fail, skip, sorted(worst, reverse=True)))
    return out

if __name__ == "__main__":
    res = audit(sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "kics_disclosure.json"))
    L = [f"{'룰':<26}{'컬럼':<7}{'PASS':>6}{'FAIL':>6}{'계산불가':>9}"]
    for label, col, ok, fail, skip, worst in res:
        L.append(f"{label:<26}{col:<7}{ok:>6}{fail:>6}{skip:>9}")
        if col == '적용후': L.append("")
    L += ["=" * 96, "적용후 FAIL 상세 (오차율 큰 순, 룰별 8건)"]
    for label, col, ok, fail, skip, worst in res:
        if col != '적용후' or not worst: continue
        L.append(f"\n--- {label}: {fail}건")
        for pct, co, nm, q, act, exp, diff in worst[:8]:
            L.append(f"    {co} {nm:<13} {q:<9} 공시={act:>13,.2f} 계산={exp:>13,.2f} 차={diff:>12,.2f} ({pct:5.1f}%)")
    Path(sys.argv[1]).write_text("\n".join(L), encoding='utf-8')
    print("done")
