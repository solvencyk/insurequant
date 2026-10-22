# -*- coding: utf-8 -*-
"""Tolerance margins of the proposed SQ_CSM_ROLL and SQ_AMORT rules (read-only, pinned HEAD): distribution of |gap| among
passing buckets vs the smallest failing gap, and the effect of a propagated tolerance tol(q)+tol(q-1) on SQ_AMORT."""
import json, subprocess, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_master_tables as V
def show(f):
    return json.loads(subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True, check=True, cwd=ROOT).stdout.decode("utf-8"))
wf = show("CSM_waterfall.json"); pl = show("PL_breakdown.json")
cd, cv = {}, {}
for r in wf:
    k = (r["원보험사코드"], r["공시분기"]); cd.setdefault(k, {})[int(r["항목번호"])] = r.get("값_당분기"); cv.setdefault(k, {})[int(r["항목번호"])] = r.get("값")
def prevq(q):
    y, n = q.split("."); n = int(n[0]); return None if n == 1 else f"{y}.{n-1}Q"
gaps = []
for k, d in cd.items():
    if any(d.get(i) is None for i in range(1, 7)): continue
    g = sum(d[i] for i in range(1, 6)) - d[6]
    gaps.append((abs(g), abs(g) / max(abs(d[6]), 1e-9), k))
gaps.sort()
out = []; P = out.append
fails = [x for x in gaps if x[0] > max(0.001 * abs(cd[x[2]][6]), 2.0)]
passes = [x for x in gaps if x not in fails]
P(f"SQ_CSM_ROLL n={len(gaps)} pass={len(passes)} fail={len(fails)}")
P(f"   passing |gap| max={passes[-1][0]:.3f}억 at {passes[-1][2]}; p99={passes[int(0.99*len(passes))-1][0]:.3f}; count>0.5억: {sum(1 for x in passes if x[0] > 0.5)}")
P(f"   failing |gap| min={fails[0][0]:.2f}억 ({fails[0][1]*100:.3f}% of close) at {fails[0][2]}")
P("   top passing gaps: " + ", ".join(f"{k[0]} {k[1]} {g:.2f}" for g, _, k in passes[-6:]))
# SQ_AMORT with propagated tolerance
pd = {}
for r in pl:
    pd.setdefault((r["원보험사코드"], r["공시분기"]), {})[str(r["항목번호"])] = (r.get("값"), r.get("값_당분기"))
n = 0; f1 = []; f2 = []
for k, d in cd.items():
    a = d.get(5); m = pd.get(k)
    if m is None or a is None or abs(a) < V.CSM_AMORT_MIN_EOK: continue
    dv = m.get("4", (None, None))[1]
    if dv is None: continue
    tot = abs(dv) + abs(m.get("4-1", (None, None))[1] or 0.0)
    if tot == 0: continue
    n += 1
    res = tot / 100 - abs(a)
    t1 = V.csm_amort_tol(abs(a))
    p = prevq(k[1])
    t2 = t1 if p is None else V.csm_amort_tol(abs(cv[k][5])) + V.csm_amort_tol(abs(cv.get((k[0], p), {}).get(5) or 0.0))
    if abs(res) > t1 + 1e-9: f1.append((k, round(res, 2)))
    if abs(res) > t2 + 1e-9: f2.append((k, round(res, 2)))
P(f"SQ_AMORT n={n}  fail@tol(single)={len(f1)} {f1}  fail@tol(q)+tol(q-1)={len(f2)} {f2}")
(HERE / "s8_margins.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
