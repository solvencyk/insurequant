# -*- coding: utf-8 -*-
"""Break down the SQ_PL_DERIV mismatches of s1_sim.json (값_당분기 None although 값(q) and 값(q-1) both exist).
Read-only. Pinned to the same commit through s1_sim.json + git show HEAD for the gold overlay / provenance."""
import json, subprocess, pathlib
from collections import Counter, defaultdict
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
def show(f):
    return json.loads(subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True, check=True, cwd=ROOT).stdout.decode("utf-8"))
res = json.loads((HERE / "s1_sim.json").read_text(encoding="utf-8"))
rows = res["pl_deriv_bad"]   # c, q, no, v, d, exp, src
out = []
P = out.append
P(f"total {len(rows)}; d None: {sum(1 for r in rows if r[4] is None)}; d not None (value mismatch): {sum(1 for r in rows if r[4] is not None)}")
P("by item: " + str(sorted(Counter(r[2] for r in rows).items(), key=lambda x: -x[1])))
P("by quarter: " + str(sorted(Counter(r[1] for r in rows).items())))
byco = Counter(r[0] for r in rows)
P("by company: " + str(sorted(byco.items(), key=lambda x: -x[1])))
# gold overlay 'set' keys
gold = show("data/_gold/user_pl_cells.json")
gset = {(s["원보험사코드"], str(s["항목번호"]), s["공시분기"]) for s in gold.get("set", [])}
pl = show("PL_breakdown.json")
val = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in pl}
def prevq(q):
    y, n = q.split("."); n = int(n[0]); return None if n == 1 else f"{y}.{n-1}Q"
tag = Counter(); bucket = defaultdict(list)
for c, q, no, v, d, exp, src in rows:
    p = prevq(q)
    t = []
    if (c, no, q) in gset: t.append("cur_in_gold_set")
    if (c, no, p) in gset: t.append("prev_in_gold_set")
    tg = "+".join(t) or "no_gold"
    tag[tg] += 1
    bucket[(c, q)].append(no)
P("gold-overlay tags: " + str(dict(tag)))
P("buckets (company quarter: items):")
for (c, q), its in sorted(bucket.items()):
    P(f"  {c} {q}: {','.join(sorted(its, key=lambda x: (len(x), x)))}")
# provenance sidecar: lineage of cur/prev buckets
try:
    prov = show("PL_breakdown_provenance.json")
    P(f"provenance top-level type={type(prov).__name__} keys={list(prov)[:8] if isinstance(prov, dict) else len(prov)}")
except Exception as e:
    P(f"provenance read failed: {e}")
(HERE / "s2_deriv_breakdown.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
