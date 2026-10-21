# -*- coding: utf-8 -*-
"""All-bucket simulation: tax22_src rule, same-quarter vintage only (OLD) vs also latest-comparative
vintage (NEW = same OR prior-column of the next-year same-period FS-API cache). Read-only."""
import copy, json, sys, subprocess
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
import validate_master_tables as V
import fetch_dart_fs as fdf

def prior_t1(cc, q):
    """cache of year+1, same reprt; map frmtrm_* onto thstrm_* and reuse fdf._parse"""
    reprt = fdf.REPRT.get(q[5:])
    annual = q[5:] == "4Q"
    y = str(int(q[:4]) + 1)
    for div in ("OFS", "CFS"):
        p = ROOT / V.TAX22_CACHE_DIR / f"{cc}_{y}_{reprt}_{div}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        d2 = copy.deepcopy(d)
        for a in d2.get("list", []):
            if annual:
                a["thstrm_amount"] = a.get("frmtrm_amount"); a["thstrm_add_amount"] = ""
            else:
                a["thstrm_amount"] = a.get("frmtrm_q_amount"); a["thstrm_add_amount"] = a.get("frmtrm_add_amount")
        try:
            t1 = fdf._parse(d2, annual)
        except Exception:
            t1 = None
        if t1:
            return t1
    return None

def evaluate(rows, label):
    master, code_of = defaultdict(dict), {}
    for r in rows:
        master[(r["원수사명"], r["공시분기"])][V.norm(r["항목명"])] = r["값"]; code_of[r["원수사명"]] = r["원보험사코드"]
    kr2cc = V._tax22_corp_codes()
    out = {}
    for (co, q) in sorted(master):
        m = master[(co, q)]; m22, m24 = m.get("세전이익"), m.get("당기순이익")
        if m22 is None or m24 is None: out[(co, q)] = ("SKIP", "master"); continue
        cc = kr2cc.get(code_of.get(co, ""))
        if not cc: out[(co, q)] = ("SKIP", "corp"); continue
        t1 = V._tax22_tier1(fdf, cc, q)
        if not t1: out[(co, q)] = ("SKIP", "cache"); continue
        if t1.get(23) is None: out[(co, q)] = ("SKIP", "taxabsent"); continue
        lhs = abs(m22 - m24); tol = max(V.TAX22_REL * max(abs(m22), lhs), V.TAX22_FLOOR)
        same = abs(abs(t1[23]) - lhs) <= tol
        p = prior_t1(cc, q); pt = p.get(23) if p else None
        prior = None if pt is None else (abs(abs(pt) - lhs) <= tol)
        old = "PASS" if same else "FAIL"
        new = "PASS" if (same or prior) else "FAIL"
        out[(co, q)] = (old, new, same, prior, lhs, abs(t1[23]), None if pt is None else abs(pt), tol)
    return out

def summarize(res, label, f):
    c = defaultdict(int); closed = []; broken = []; both = []; rest = []
    for k, v in res.items():
        if v[0] == "SKIP": c["SKIP_" + v[1]] += 1; continue
        c[f"old_{v[0]}"] += 1; c[f"new_{v[1]}"] += 1
        if v[0] == "FAIL" and v[1] == "PASS": closed.append(k)
        if v[0] == "PASS" and v[1] == "FAIL": broken.append(k)
        if v[0] == "FAIL" and v[1] == "FAIL": rest.append(k)
        if v[2] and v[3]: both.append(k)
        if (not v[2]) and v[3]: pass
    f.write(f"== {label}: buckets={len(res)} {dict(c)}\n")
    f.write(f"   closed(old FAIL->new PASS)={len(closed)}  newly_broken(old PASS->new FAIL)={len(broken)}  still_FAIL={len(rest)}\n")
    for k in closed: v = res[k]; f.write(f"   CLOSED {k} |22-24|={v[4]:,.1f} same-vintage tax={v[5]:,.1f} prior-vintage tax={v[6]:,.1f} tol={v[7]:,.1f}\n")
    for k in broken: f.write(f"   BROKEN {k} {res[k]}\n")
    for k in rest: f.write(f"   STILL_FAIL {k} {res[k]}\n")
    # info: buckets where the next-year cache exists and its prior column differs from same-quarter vintage
    nprior = sum(1 for v in res.values() if v[0] != "SKIP" and v[3] is not None)
    diff_vintage = [k for k, v in res.items() if v[0] != "SKIP" and v[3] is not None and v[6] is not None and abs(v[6] - v[5]) > v[7]]
    f.write(f"   buckets with next-year prior column available={nprior}; prior!=same-vintage beyond tol={len(diff_vintage)} -> {diff_vintage}\n")
    f.write(f"   buckets matching BOTH vintages (ambiguous-by-construction, not harmful)={len(both)}\n")

def perturb(v): return v + max(10000.0, 0.30 * abs(v))

def mutation(rows, f):
    # inject item22 error in every bucket (same as probe_20260829_tax22_rule_mutation naive mode); count detected
    import io, contextlib
    mut = copy.deepcopy(rows)
    n = 0
    for r in mut:
        if V.norm(r["항목명"]) == "세전이익" and r["값"] is not None:
            r["값"] = perturb(r["값"]); n += 1
    res = evaluate(mut, "mut")
    old_f = sum(1 for v in res.values() if v[0] == "FAIL"); new_f = sum(1 for v in res.values() if v[0] != "SKIP" and v[1] == "FAIL")
    tot = sum(1 for v in res.values() if v[0] != "SKIP")
    f.write(f"== MUTATION item22 +max(10000,30%) in all buckets: injected_cells={n} testable={tot}  old-rule detected={old_f}  new-rule detected={new_f}\n")
    miss = [k for k, v in res.items() if v[0] != "SKIP" and v[1] == "PASS"]
    f.write(f"   new-rule undetected buckets={miss}\n")

def main():
    out = ROOT / "data/_derived/kyobo_validation_20261022/sim_tax22_vintage.txt"
    with out.open("w", encoding="utf-8") as f:
        rows = json.loads((ROOT / V.PL_PATH).read_text(encoding="utf-8"))
        summarize(evaluate(rows, "HEAD"), "master = HEAD (3e53aef8)", f)
        prev = subprocess.run(["git", "show", "3e53aef8~1:PL_breakdown.json"], capture_output=True, cwd=ROOT, check=True).stdout
        rows0 = json.loads(prev.decode("utf-8"))
        summarize(evaluate(rows0, "HEAD~1"), "master = HEAD~1 (c99e8ce9)", f)
        mutation(rows, f)
    print(out.read_text(encoding="utf-8"))
main()
