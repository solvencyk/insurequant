"""3-axis mmult audit over kics_disclosure.json, both 적용전 and 적용후.

A: item17 = sqrt(S' R7 S),  S = items 29-35
B: item19 = sqrt(V' M V),   V = items 36-40
C: item15 = sqrt(W' R4 W) + item21,  W = items 17,18,19,20
"""
import io, json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
from solvency.validation.kics_json_rules import R4, R7, MARKET_M

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
APPLIERS = frozenset({"KR0070","KR0071","KR0072","KR0073","KR0076","KR0082","KR0083",
                      "KR0097","KR0100","KR1010","KR1011","KR0104","KR0049","KR0002",
                      "KR0003","KR0004","KR0005","KR0032"})

def num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None

m = defaultdict(dict); name = {}
for r in rows:
    c, q = r.get("원보험사코드"), r.get("공시분기"); name[c] = r.get("원수사명", c)
    try: it = int(r["항목번호"])
    except (TypeError, ValueError, KeyError): continue
    m[(c, q)][it] = (num(r.get("값")), num(r.get("값_적용후")))

def get(d, it, post):
    return d.get(it, (None, None))[1 if post else 0]

AXES = {
    "A": ("item17 = R7(29-35)", 17, list(range(29, 36)), R7, None),
    "B": ("item19 = M(36-40)", 19, list(range(36, 41)), MARKET_M, None),
    "C": ("item15 = R4(17-20)+21", 15, [17, 18, 19, 20], R4, 21),
}

out = {}
for ax, (label, parent, subs, mat, addend) in AXES.items():
    for post in (False, True):
        ok = fail = nocalc = 0
        fails = []
        for (c, q), d in sorted(m.items()):
            p = get(d, parent, post)
            vs = [get(d, s, post) for s in subs]
            add = get(d, addend, post) if addend else 0.0
            if p is None or any(v is None for v in vs) or (addend and add is None):
                nocalc += 1
                continue
            v = np.array(vs, dtype=float)
            exp = float(np.sqrt(v @ mat @ v)) + (add or 0.0)
            diff = p - exp
            if abs(diff) > 2.0:
                fail += 1
                pct = abs(diff) / exp * 100 if exp else float("inf")
                fails.append((c, name.get(c, c), q, round(p, 2), round(exp, 2), round(diff, 2), round(pct, 2)))
            else:
                ok += 1
        out[(ax, post)] = (ok, fail, nocalc, fails)

print("| 축 | 컬럼 | 계산가능 | PASS | FAIL(tol2.0) | FAIL(>5%) | 계산불가 |")
print("|---|---|---|---|---|---|---|")
for ax in "ABC":
    for post in (False, True):
        ok, fail, nocalc, fails = out[(ax, post)]
        big = sum(1 for f in fails if f[6] > 5.0)
        print(f"| {ax} {AXES[ax][0]} | {'적용후' if post else '적용전'} | {ok+fail} | {ok} | {fail} | {big} | {nocalc} |")

for ax in "ABC":
    for post in (False, True):
        ok, fail, nocalc, fails = out[(ax, post)]
        if not fails:
            continue
        print(f"\n### {ax} {'적용후' if post else '적용전'} FAIL {len(fails)}  (applier=* 표시)")
        for c, nm, q, p, exp, diff, pct in sorted(fails, key=lambda x: -x[6]):
            star = "*" if c in APPLIERS else " "
            print(f"  {star}{c} {nm:<12s} {q}  공시={p:>12,.2f} 계산={exp:>12,.2f} 차={diff:>10,.2f} ({pct:.2f}%)")
