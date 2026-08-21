"""B축(item19=M(36-40)) 적용후 계산불가 178건의 내역: 무엇이 결측인가."""
import io, json, sys
from collections import defaultdict, Counter
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
def num(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None
d = defaultdict(dict); name = {}
for r in rows:
    c, q = r["원보험사코드"], r["공시분기"]; name[c] = r.get("원수사명", c)
    try: d[(c, q)][int(r["항목번호"])] = (num(r.get("값")), num(r.get("값_적용후")))
    except (TypeError, ValueError, KeyError): pass
kinds = Counter(); rowmiss = Counter(); detail = defaultdict(list)
for (c, q), m in sorted(d.items()):
    p = m.get(19, (None, None))[1]
    subs = {i: m.get(i, (None, None)) for i in range(36, 41)}
    have_post = [i for i in subs if subs[i][1] is not None]
    have_row = [i for i in subs if i in m]
    if p is not None and len(have_post) == 5:
        continue
    if p is None and not have_post:
        kinds["부모후·세부후 둘 다 없음(간이공시/미공시)"] += 1
    elif p is None:
        kinds["부모후 없음·세부후 일부 있음"] += 1
        detail["부모후없음"].append((c, name.get(c,c), q))
    else:
        miss = [i for i in range(36, 41) if subs[i][1] is None]
        norow = [i for i in miss if i not in m]
        kinds["부모후 있음·세부후 결측"] += 1
        rowmiss[tuple(miss)] += 1
        detail["세부결측"].append((c, name.get(c,c), q, miss, norow))
for k, v in kinds.most_common():
    print(f"  {k}: {v}")
print("\n-- 부모후 있음·세부후 결측 상세 --")
for c, nm, q, miss, norow in detail["세부결측"]:
    print(f"   {c} {nm:<12} {q} 결측item={miss} (행자체없음={norow})")
print("\n-- 부모후 없음·세부후 일부 있음 --")
for c, nm, q in detail["부모후없음"][:20]:
    print(f"   {c} {nm:<12} {q}")
