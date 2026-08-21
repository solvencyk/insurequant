"""For each axis-C 적용후 FAIL: is 17후/19후 actually transitioned, or still = 적용전?"""
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
def g(d, it, p): return d.get(it, (None, None))[1 if p else 0]
def same(a, b): return a is not None and b is not None and abs(a - b) < 0.5

print(f"{'회사':<13}{'분기':<9}{'차':>10}  17전/후(감소?)          19전/후(감소?)         36-40후=전?")
for (c, q), d in sorted(m.items()):
    p15 = g(d, 15, 1); vs = [g(d, i, 1) for i in (17, 18, 19, 20)]; v21 = g(d, 21, 1)
    if p15 is None or any(v is None for v in vs) or v21 is None: continue
    exp = float(np.sqrt(np.array(vs, float) @ R4 @ np.array(vs, float))) + v21
    if abs(p15 - exp) <= 2.0: continue
    a17, b17 = g(d, 17, 0), g(d, 17, 1)
    a19, b19 = g(d, 19, 0), g(d, 19, 1)
    subs_same = [i for i in range(36, 41)
                 if g(d, i, 0) is not None and g(d, i, 1) is not None and same(g(d, i, 0), g(d, i, 1))]
    subs_have = [i for i in range(36, 41) if g(d, i, 1) is not None]
    tag17 = "동일" if same(a17, b17) else "감소"
    tag19 = "동일" if same(a19, b19) else "감소"
    mk = f"{len(subs_same)}/{len(subs_have)} 동일"
    print(f"{name.get(c,c):<13}{q:<9}{p15-exp:>10,.2f}  "
          f"{a17!s:>9}/{b17!s:<9}({tag17})  {a19!s:>9}/{b19!s:<9}({tag19})  {mk}")
