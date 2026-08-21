"""R1/R2/R5/R6/R7/R8 항등식을 전사 × 전후 전수 검산 (게이트는 적용후를 18사만 본다)."""
import io, json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
APPLIERS = frozenset({"KR0070","KR0071","KR0072","KR0073","KR0076","KR0082","KR0083",
                      "KR0097","KR0100","KR1010","KR1011","KR0104","KR0049","KR0002",
                      "KR0003","KR0004","KR0005","KR0032"})
def num(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None
d = defaultdict(dict); name = {}
for r in rows:
    c, q = r["원보험사코드"], r["공시분기"]; name[c] = r.get("원수사명", c)
    try: d[(c, q)][int(r["항목번호"])] = (num(r.get("값")), num(r.get("값_적용후")))
    except (TypeError, ValueError, KeyError): pass
RULES = [
    ("R1 item1=2+3", 1, (2, 3), lambda v: v[2] + v[3], False),
    ("R2 item4=Σ5-11", 4, (5, 6, 7, 8, 9, 10, 11), lambda v: sum(v[i] for i in (5,6,7,8,9,10,11)), False),
    ("R5 item14=15-22+23", 14, (15, 22, 23), lambda v: v[15] - v[22] + v[23], False),
    ("R6 item16=Σ17-21-15", 16, (17,18,19,20,21,15), lambda v: sum(v[i] for i in (17,18,19,20,21)) - v[15], False),
    ("R7 item27=1/14x100", 27, (1, 14), lambda v: v[1]/v[14]*100 if v[14] else None, True),
    ("R8 item28=2/14x100", 28, (2, 14), lambda v: v[2]/v[14]*100 if v[14] else None, True),
]
for label, tgt, ins, fn, is_ratio in RULES:
    out = {}
    for post in (0, 1):
        fails = []
        n = 0
        for (c, q), m in sorted(d.items()):
            vals = {i: m.get(i, (None, None))[post] for i in set(ins) | {tgt}}
            if any(vals[i] is None for i in ins) or vals[tgt] is None:
                continue
            n += 1
            exp = fn(vals)
            if exp is None:
                continue
            tol = 2.0 if is_ratio else max(2.0, 0.005 * abs(exp))
            if abs(exp - vals[tgt]) > tol:
                fails.append((c, name.get(c,c), q, round(vals[tgt],2), round(exp,2), round(vals[tgt]-exp,2)))
        out[post] = (n, fails)
    print(f"\n## {label}: 전 {out[0][0]}건중 FAIL {len(out[0][1])} | 후 {out[1][0]}건중 FAIL {len(out[1][1])}")
    pre_keys = {(c, q) for c, _n, q, *_ in out[0][1]}
    for c, nm, q, got, exp, diff in out[1][1]:
        tag = "  (적용전도 FAIL)" if (c, q) in pre_keys else "  <<< 적용후 고유"
        star = "*" if c in APPLIERS else " "
        print(f"   후{star}{c} {nm:<12} {q} 저장={got:>12,.2f} 계산={exp:>12,.2f} 차={diff:>10,.2f}{tag}")
    for c, nm, q, got, exp, diff in out[0][1]:
        if (c, q) not in {(x[0], x[2]) for x in out[1][1]}:
            print(f"   전 {c} {nm:<12} {q} 저장={got:>12,.2f} 계산={exp:>12,.2f} 차={diff:>10,.2f}  (적용전만)")
