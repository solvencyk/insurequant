# -*- coding: utf-8 -*-
"""Group the 430 unregistered null 값_당분기 cells (s1 SQ_PL_DERIV) into (company, quarter) buckets per lineage class
(same resolver as the gate: validate_master_tables.pl_cell_source_ids). Read-only; writes s9_deriv_groups.txt/json."""
import json, sys, pathlib
from collections import defaultdict
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
g = defaultdict(lambda: defaultdict(list))
for c, q, no, v, d, exp, s in res["pl_deriv_bad"]:
    a, b = src.get((name[c], prevq(q))), src.get((name[c], q))
    k = f"{a}->{b}"
    g[k][(c, q)].append(no)
out = []; dump = {}
for k, bk in sorted(g.items(), key=lambda x: -sum(len(v) for v in x[1].values())):
    cells = sum(len(v) for v in bk.values())
    out.append(f"{k}: buckets={len(bk)} cells={cells}")
    out.append("   " + "; ".join(f"{c} {q} [{','.join(v)}]" for (c, q), v in sorted(bk.items())))
    dump[k] = {f"{c}|{q}": v for (c, q), v in sorted(bk.items())}
out.append(f"TOTAL buckets={sum(len(b) for b in g.values())} cells={sum(len(v) for b in g.values() for v in b.values())}")
(HERE / "s9_deriv_groups.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
(HERE / "s9_deriv_groups.json").write_text(json.dumps(dump, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n".join(out))
