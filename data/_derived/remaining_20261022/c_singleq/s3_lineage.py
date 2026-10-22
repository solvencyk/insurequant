# -*- coding: utf-8 -*-
"""Are the 430 unregistered null 값_당분기 cells (s1/s2) explained by a lineage switch between q-1 and q
(DISCLOSURE §2-1 vs DART), using the gate's own resolver pl_cell_source_ids()? Read-only."""
import json, sys, pathlib
from collections import Counter, defaultdict
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_master_tables as V
src = V.pl_cell_source_ids()
res = json.loads((HERE / "s1_sim.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / V.PL_PATH).read_text(encoding="utf-8"))
name = {r["원보험사코드"]: r["원수사명"] for r in pl}
def prevq(q):
    y, n = q.split("."); n = int(n[0]); return None if n == 1 else f"{y}.{n-1}Q"
out = []; P = out.append
P("source_id values overall: " + str(Counter(src.values())))
cls = Counter(); rows_by = defaultdict(list)
for c, q, no, v, d, exp, s in res["pl_deriv_bad"]:
    p = prevq(q)
    a, b = src.get((name[c], p)), src.get((name[c], q))
    if a is None or b is None:
        k = f"lineage_unknown(prev={a},cur={b})"
    elif a != b:
        k = f"LINEAGE_SWITCH {a}->{b}"
    else:
        k = f"SAME_LINEAGE {a}"
    cls[k] += 1; rows_by[k].append((c, q, no))
for k, n in cls.most_common():
    P(f"{n:>4d}  {k}")
    if not k.startswith("LINEAGE_SWITCH"):
        P("       " + ", ".join(f"{c} {q} i{no}" for c, q, no in rows_by[k])[:1500])
# also: of the PASSING derived dangi cells, how many already mix lineages (diff computed across a switch)?
val = defaultdict(dict); dg = defaultdict(dict)
for r in pl:
    val[(r["원보험사코드"], r["공시분기"])][str(r["항목번호"])] = r.get("값")
    dg[(r["원보험사코드"], r["공시분기"])][str(r["항목번호"])] = r.get("값_당분기")
mix = Counter(); mix_rows = []
for (c, q), m in val.items():
    p = prevq(q)
    if not p or (c, p) not in val: continue
    a, b = src.get((name[c], p)), src.get((name[c], q))
    if a and b and a != b:
        n = sum(1 for no, d in dg[(c, q)].items() if d is not None and m.get(no) is not None)
        if n:
            mix[f"{a}->{b}"] += n; mix_rows.append((c, q, n))
P(f"\nexisting NON-null 값_당분기 cells derived across a lineage switch: {dict(mix)}")
P("   " + ", ".join(f"{c} {q}({n})" for c, q, n in sorted(mix_rows))[:2500])
(HERE / "s3_lineage.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
