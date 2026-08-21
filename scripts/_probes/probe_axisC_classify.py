"""Classify the axis-C 적용후 failures: where does the stored item15후 come from?"""
import io, json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
from solvency.validation.kics_json_rules import R4

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
def num(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None
m = defaultdict(dict); name = {}
for r in rows:
    c, q = r.get("원보험사코드"), r.get("공시분기"); name[c] = r.get("원수사명", c)
    try: it = int(r["항목번호"])
    except (TypeError, ValueError, KeyError): continue
    m[(c, q)][it] = (num(r.get("값")), num(r.get("값_적용후")))
def g(d, it, post): return d.get(it, (None, None))[1 if post else 0]

print(f"{'회사':<14}{'분기':<9}{'15후저장':>11}{'R4(subs)':>11}{'차':>10} | "
      f"{'14후':>10}{'22후':>10}{'23후':>9}{'23전':>9} | R5(23후) R5(23전) 판정")
fam = defaultdict(list)
for (c, q), d in sorted(m.items()):
    p15 = g(d, 15, 1)
    vs = [g(d, i, 1) for i in (17, 18, 19, 20)]
    v21 = g(d, 21, 1)
    if p15 is None or any(v is None for v in vs) or v21 is None:
        continue
    exp = float(np.sqrt(np.array(vs, float) @ R4 @ np.array(vs, float))) + v21
    if abs(p15 - exp) <= 2.0:
        continue
    v14, v22, v23p, v23 = g(d, 14, 1), g(d, 22, 1), g(d, 23, 1), g(d, 23, 0)
    def close(a, b):
        return a is not None and b is not None and abs(a - b) <= max(2.0, 0.005 * abs(b))
    r5_post = close(v14, (p15 - (v22 or 0) + (v23p or 0)))
    r5_pre = close(v14, (p15 - (v22 or 0) + (v23 or 0)))
    tag = ("R5(23후)닫힘" if r5_post else "") + (" R5(23전)닫힘" if r5_pre and not r5_post else "")
    key = name.get(c, c)
    fam[key].append((q, p15, exp))
    print(f"{key:<14}{q:<9}{p15:>11,.2f}{exp:>11,.2f}{p15-exp:>10,.2f} | "
          f"{'' if v14 is None else f'{v14:,.2f}':>10}{'' if v22 is None else f'{v22:,.2f}':>10}"
          f"{'' if v23p is None else f'{v23p:,.2f}':>9}{'' if v23 is None else f'{v23:,.2f}':>9} | "
          f"{'Y' if r5_post else 'n':>7} {'Y' if r5_pre else 'n':>8}  {tag}")
print("\n회사별 건수:", {k: len(v) for k, v in sorted(fam.items(), key=lambda kv: -len(kv[1]))})
