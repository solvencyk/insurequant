# -*- coding: utf-8 -*-
"""READ-ONLY simulation of proposed single-quarter (값_당분기) rules over the masters pinned at a commit.

Inputs are read with `git show <sha>:` (default HEAD) so parallel edits to the working tree cannot move the
measurement. Equations / tolerances are IMPORTED from scripts/validate_master_tables.py (no retyping).
Writes only s1_sim.txt + s1_sim.json next to this file.

Rules simulated
  CSM (억원)
    SQ_CSM_DERIV : 값_당분기 must equal the builder derivation from 값 (stock: 기말=값, 기초=prev 기말 / Q1 기초;
                   flow: 값(q)-값(q-1), Q1 = 값).  tol 1e-4.
    SQ_CSM_ROLL  : 기초_q + 신계약_q + 이자_q + 가정_q + 상각_q = 기말_q on 값_당분기.  tol max(0.1%|기말|, 2억)
                   (= CLOSING_IDENTITY tol).  Decomposed into  YTD-residual(q) - YTD-residual(q-1) + WFY drift.
    census       : bucket with all six 값 but a missing 값_당분기 -> classified (CHAIN_BREAK = q-1 bucket absent).
  PL (백만원)
    SQ_PL_DERIV  : 값_당분기 == 값(q)-값(q-1) (Q1 = 값) unless the cell is registered in user_pl_cells.json
                   set_dangi (== registered value) / null_dangi (== None).  tol 1e-4.
    SQ_PL_EQS    : PL_EQS + 보험손익 dual/leg-coverage on 값_당분기, same tolerance as the YTD bridge.
                   Each failure is split into "YTD also fails at q or q-1" (already seen) vs "dangi-only" (new).
    SQ_PL_FYSUM  : Σ 값_당분기(Q1..Q4) == 값(Q4) (telescoping; informative only where set/null_dangi exist).
  Cross
    SQ_AMORT     : CSM 상각 값_당분기 vs PL (원수+수재) CSM상각 값_당분기 /100, CSM_AMORT_IDENTITY tol + ledger pins.
Excluded: KR0073 items 25/26/29/31/32 (parallel job) -> the two OCI equations are not evaluated for KR0073.
"""
import json, subprocess, sys, pathlib, io, contextlib
from collections import defaultdict, Counter

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHA = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
sys.path.insert(0, str(ROOT / "scripts"))
if True:
    import validate_master_tables as V  # constants only; main() is never called

def show(f):
    return json.loads(subprocess.run(["git", "show", f"{SHA}:{f}"], capture_output=True, check=True,
                                     cwd=ROOT).stdout.decode("utf-8"))

def qkey(q):
    y, n = q.split("."); return int(y), int(n[0])

def prevq(q):
    y, n = qkey(q); return None if n == 1 else f"{y}.{n-1}Q"

out = []
P = out.append
res = {}
KYOBO_EXCL = {25, 26, 29, 31, 32}
OCI_LABELS = {lab for lab, lhs, _ in V.PL_EQS if lhs in ("총포괄손익", "기타포괄손익")}

# ---------------------------------------------------------------- CSM
wf = show("CSM_waterfall.json")
cv = defaultdict(dict); cd = defaultdict(dict); cname = {}
for r in wf:
    k = (r["원보험사코드"], r["공시분기"]); it = int(r["항목번호"])
    cv[k][it] = r.get("값"); cd[k][it] = r.get("값_당분기"); cname[r["원보험사코드"]] = r["원수사명"]
TOL_D = 1e-4
deriv_bad = []
for (c, q), m in sorted(cv.items()):
    p = prevq(q); pm = cv.get((c, p), {}) if p else {}
    for it in range(1, 7):
        v = m.get(it); d = cd[(c, q)].get(it)
        if v is None:
            exp = None
        elif it == 6:
            exp = v
        elif it == 1:
            exp = v if p is None else pm.get(6)
        else:
            exp = v if p is None else (None if pm.get(it) is None else v - pm[it])
        if (exp is None) != (d is None) or (exp is not None and abs(exp - d) > TOL_D):
            deriv_bad.append((c, q, it, v, d, exp))
P(f"== SQ_CSM_DERIV (pinned {SHA})  cells={sum(len(m) for m in cv.values())}  mismatch={len(deriv_bad)}")
for x in deriv_bad[:30]:
    P(f"   DERIV {x[0]} {cname[x[0]]} {x[1]} item{x[2]} 값={x[3]} 당분기={x[4]} expected={x[5]}")

def roll(tolrel):
    rows, n, skip = [], 0, []
    for (c, q), d in sorted(cd.items()):
        if any(cv[(c, q)].get(i) is None for i in range(1, 7)):
            skip.append((c, q, "VAL_MISSING")); continue
        if any(d.get(i) is None for i in range(1, 7)):
            p = prevq(q)
            kind = "CHAIN_BREAK(q-1 bucket absent)" if p and (c, p) not in cv else "DANGI_NULL_WITH_PRIOR"
            skip.append((c, q, kind)); continue
        n += 1
        gap = sum(d[i] for i in range(1, 6)) - d[6]
        if abs(gap) > max(tolrel * abs(d[6]), 2.0):
            rows.append((c, q, gap))
    return n, rows, skip

for tolrel in (0.001, 0.002):
    n, rows, skip = roll(tolrel)
    P(f"== SQ_CSM_ROLL tol=max({tolrel*100:g}%,2억)  evaluated={n} fail={len(rows)} skip={len(skip)} "
      f"({dict(Counter(k for _, _, k in skip))})")
n, rows, skip = roll(0.001)
res["csm_roll"] = {"evaluated": n, "fail": [], "skip": [list(s) for s in skip]}
for c, q, gap in rows:
    y, qn = qkey(q); p = prevq(q)
    m, pm = cv[(c, q)], cv[(c, p)]
    r_q = sum(m[i] for i in range(1, 6)) - m[6]
    r_p = sum(pm[i] for i in range(1, 6)) - pm[6]
    drift = pm[1] - m[1]           # FY opening as printed in q-1 vs in q
    opens = {f"{y}.{k}Q": cv.get((c, f"{y}.{k}Q"), {}).get(1) for k in range(1, 5)}
    closes = {f"{y}.{k}Q": cv.get((c, f"{y}.{k}Q"), {}).get(6) for k in range(1, 5)}
    prevfy4 = cv.get((c, f"{y-1}.4Q"), {}).get(6)
    P(f"   FAIL {c} {cname[c]} {q} gap={gap:+.2f}억 = YTDresid(q){r_q:+.2f} - YTDresid(q-1){r_p:+.2f} + "
      f"FYopen drift(q-1 minus q){drift:+.2f}  | FY opens by quarter {opens} | prior FY 4Q close {prevfy4} | closes {closes}")
    res["csm_roll"]["fail"].append({"code": c, "name": cname[c], "quarter": q, "gap_eok": round(gap, 2),
                                    "ytd_resid_q": round(r_q, 2), "ytd_resid_prev": round(r_p, 2),
                                    "fy_open_drift": round(drift, 2), "fy_opens": opens, "prev_fy_4q_close": prevfy4,
                                    "wfy_exception": (cname[c], str(y)) in V.WFY_EXCEPTIONS})
P("   skip detail: " + "; ".join(f"{c} {cname[c]} {q} {k}" for c, q, k in skip if k != "VAL_MISSING")[:3000])
P("   VAL_MISSING buckets: " + ", ".join(f"{c} {q}" for c, q, k in skip if k == "VAL_MISSING"))

# ---------------------------------------------------------------- PL
pl = show("PL_breakdown.json")
gold = show("data/_gold/user_pl_cells.json")
setd = {(c[0], c[1], int(c[2])): float(c[3]) for c in (gold.get("set_dangi") or {}).get("cells", [])}
nulld = {(c, q, int(i)) for c, q, i in (gold.get("null_dangi") or {}).get("cells", [])}
pv = defaultdict(dict); pdg = defaultdict(dict); pname = {}
by_name_v = defaultdict(dict); by_name_d = defaultdict(dict)
for r in pl:
    c, q, no = r["원보험사코드"], r["공시분기"], str(r["항목번호"])
    pname[c] = r["원수사명"]
    pv[(c, q)][no] = r.get("값"); pdg[(c, q)][no] = r.get("값_당분기")
    if c == "KR0073" and no.isdigit() and int(no) in KYOBO_EXCL:
        continue
    by_name_v[(c, q)][V.norm(r["항목명"])] = r.get("값")
    by_name_d[(c, q)][V.norm(r["항목명"])] = r.get("값_당분기")
pd_bad = Counter(); pd_rows = []
n_cells = 0
for (c, q), m in sorted(pv.items()):
    p = prevq(q); pm = pv.get((c, p), {}) if p else {}
    for no, v in m.items():
        if c == "KR0073" and no.isdigit() and int(no) in KYOBO_EXCL:
            continue
        n_cells += 1
        d = pdg[(c, q)].get(no)
        k3 = (c, q, int(no)) if no.isdigit() else None
        if k3 in nulld:
            exp, src = None, "null_dangi"
        elif v is not None and k3 in setd:
            exp, src = setd[k3], "set_dangi"
        elif v is None:
            exp, src = None, "val_none"
        elif p is None:
            exp, src = v, "Q1"
        elif (c, p) not in pv or pm.get(no) is None:
            exp, src = None, ("prev_bucket_absent" if (c, p) not in pv else "prev_val_none")
        else:
            exp, src = v - pm[no], "diff"
        if (exp is None) != (d is None) or (exp is not None and abs(exp - d) > TOL_D):
            pd_bad[src] += 1; pd_rows.append((c, q, no, v, d, exp, src))
P(f"\n== SQ_PL_DERIV  cells={n_cells}  mismatch={len(pd_rows)}  by-kind={dict(pd_bad)}")
for x in pd_rows[:40]:
    P(f"   DERIV {x[0]} {pname[x[0]]} {x[1]} item{x[2]} 값={x[3]} 당분기={x[4]} expected={x[5]} [{x[6]}]")
# census: 값 present, 당분기 None
cen = Counter(); cen_rows = []
for (c, q), m in pv.items():
    p = prevq(q)
    for no, v in m.items():
        if c == "KR0073" and no.isdigit() and int(no) in KYOBO_EXCL:
            continue
        if v is not None and pdg[(c, q)].get(no) is None:
            k3 = (c, q, int(no)) if no.isdigit() else None
            if k3 in nulld: kind = "REGISTERED_null_dangi"
            elif p and (c, p) not in pv: kind = "CHAIN_BREAK(q-1 bucket absent)"
            elif p and pv[(c, p)].get(no) is None: kind = "PREV_VAL_NONE"
            else: kind = "UNEXPLAINED"
            cen[kind] += 1; cen_rows.append((c, q, no, kind))
P(f"== PL census 값 present & 값_당분기 None: {dict(cen)}")
chain = Counter((c, q) for c, q, no, k in cen_rows if k == "CHAIN_BREAK(q-1 bucket absent)")
P("   CHAIN_BREAK buckets: " + ", ".join(f"{c} {pname[c]} {q}({n})" for (c, q), n in sorted(chain.items())))
pvn = Counter((c, q) for c, q, no, k in cen_rows if k == "PREV_VAL_NONE")
P(f"   PREV_VAL_NONE buckets ({len(pvn)}): " + ", ".join(f"{c} {q}({n})" for (c, q), n in sorted(pvn.items()))[:2500])
P("   UNEXPLAINED: " + ", ".join(f"{c} {q} item{no}" for c, q, no, k in cen_rows if k == "UNEXPLAINED")[:2000])

def eval_eqs(idx, extra_lob):
    """same equations / tolerances as _check_pl_bridge (leg-coverage path), returns {(c,q,label): (pass, lhs, diff)}"""
    outd = {}
    for (c, q), m in idx.items():
        bo = m.get("보험손익")
        raw_lob = [m.get(k) for k in V.LOB_KEYS]
        zf = [k for k, v in zip(V.LOB_KEYS, raw_lob) if v is None]
        xlob = extra_lob.get((c, q), 0.0)
        if bo is not None and not (len(zf) == len(V.LOB_KEYS) and not xlob):
            bare = sum(0.0 if v is None else v for v in raw_lob) + xlob
            cands = [bare]
            oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
            if oi is not None and oe is not None:
                cands.append(bare + oi - oe)
            diff = min((x - bo for x in cands), key=abs)
            lab = "보험손익(leg-coverage)" if zf else "보험손익(dual)"
            outd[(c, q, "보험손익")] = (abs(diff) <= max(0.001 * abs(bo), V.DEFAULT_FLOOR), bo, diff, lab)
        for label, lhs_key, terms in V.PL_EQS:
            if c == "KR0073" and label in OCI_LABELS:
                continue
            lhs = m.get(lhs_key)
            if lhs is None or any(m.get(k) is None for k, _ in terms):
                continue
            rhs = sum(s * m[k] for k, s in terms)
            adj = V.PL_EQ_ADJ.get(label)
            if adj and all(m.get(k) is not None for k, _ in adj):
                rhs = min((rhs, rhs + sum(s * m[k] for k, s in adj)), key=lambda x: abs(x - lhs))
            diff = rhs - lhs
            outd[(c, q, label)] = (abs(diff) <= max(0.001 * abs(lhs), V.EQ_FLOOR.get(label, V.DEFAULT_FLOOR)), lhs, diff, label)
    return outd

# extra LOB (2-N) for both columns
xl_v, xl_d = defaultdict(float), defaultdict(float)
for r in pl:
    no = str(r["항목번호"])
    if V.EXTRA_LOB_ITEM_NO.match(no):
        if r.get("값") is not None: xl_v[(r["원수사명"], r["공시분기"])] += r["값"]
        if r.get("값_당분기") is not None: xl_d[(r["원수사명"], r["공시분기"])] += r["값_당분기"]
# re-key by company NAME (V uses 원수사명) for extra lob
iv = {(pname[c], q): m for (c, q), m in by_name_v.items()}
idd = {(pname[c], q): m for (c, q), m in by_name_d.items()}
ytd = eval_eqs(iv, xl_v)
sq = eval_eqs(idd, xl_d)
base = (json.loads(subprocess.run(["git", "show", f"{SHA}:{V.PL_BRIDGE_BASELINE_PATH}"], capture_output=True,
                                  check=True, cwd=ROOT).stdout.decode("utf-8")).get("entries", {}))
code_of = {v: k for k, v in pname.items()}
sq_fail = [(k, v) for k, v in sq.items() if not v[0]]
lab_ct = Counter(); lab_pass = Counter()
for k, v in sq.items():
    lab = v[3]
    (lab_pass if v[0] else lab_ct)[lab] += 1
P(f"\n== SQ_PL_EQS  evaluated={len(sq)} pass={len(sq)-len(sq_fail)} fail={len(sq_fail)}  (YTD same engine: evaluated={len(ytd)} fail={sum(1 for v in ytd.values() if not v[0])})")
for lab in sorted(set(lab_ct) | set(lab_pass)):
    ev = V.PL_EQ_EVIDENCE.get(lab, ("?",))[0]
    P(f"   [{ev:<9s}] {lab_pass[lab]:>5d}P {lab_ct[lab]:>3d}F  {lab[:60]}")
classes = Counter(); new_rows = []
for (co, q, key), (ok, lhs, diff, lab) in sorted(sq_fail):
    p = prevq(q)
    y_q = ytd.get((co, q, key)); y_p = ytd.get((co, p, key)) if p else None
    seen_q = y_q is not None and not y_q[0]
    seen_p = y_p is not None and not y_p[0]
    if seen_q or seen_p:
        cls = "YTD_ALSO_FAILS"
    elif p and y_p is None:
        cls = "DANGI_ONLY(q-1 YTD eq not evaluable)"
    elif (co, q, key) in [(x[0], x[1], x[2]) for x in []]:
        cls = "?"
    else:
        cls = "DANGI_ONLY(both YTD pass)"
    regs = [n for n in setd if n[0] == code_of[co] and n[1] == q]
    if regs: cls += "+set_dangi"
    classes[cls] += 1
    bl = f"{co}|{q}|{lab}" in base or (p and f"{co}|{p}|{lab}" in base)
    new_rows.append((code_of[co], co, q, lab, lhs, diff, cls, bl))
P(f"   fail classes: {dict(classes)}")
for x in new_rows:
    P(f"   FAIL {x[0]} {x[1]} {x[2]} [{x[3][:30]}] lhs_q={x[4]:.1f} diff={x[5]:+.1f}  {x[6]}  ytd_baselined={x[7]}")
res["pl_eqs_fail"] = [list(x) for x in new_rows]

# FY sum
fs_rows = []
for (c, q), m in pv.items():
    y, n = qkey(q)
    if n != 4: continue
    for no, v in m.items():
        if v is None or (c == "KR0073" and no.isdigit() and int(no) in KYOBO_EXCL): continue
        ds = [pdg.get((c, f"{y}.{k}Q"), {}).get(no) for k in range(1, 5)]
        if any(d is None for d in ds): continue
        s = sum(ds)
        if abs(s - v) > max(0.001 * abs(v), V.DEFAULT_FLOOR):
            fs_rows.append((c, pname[c], y, no, v, s))
P(f"\n== SQ_PL_FYSUM  fail={len(fs_rows)}")
for x in fs_rows: P(f"   FYSUM {x}")

# ---------------------------------------------------------------- cross amort single-quarter
ledger = V.csm_amort_ledger().get("entries", {})
xa = []; xa_n = 0
for (c, q), d in cd.items():
    amort = d.get(5)
    pm = pdg.get((c, q))
    if pm is None or amort is None or abs(amort) < V.CSM_AMORT_MIN_EOK: continue
    dir_ = pm.get("4")
    if dir_ is None: continue
    tot = abs(dir_) + (abs(pm["4-1"]) if pm.get("4-1") is not None else 0.0)
    if tot == 0: continue
    xa_n += 1
    resid = round(tot / 100 - abs(amort), 2)
    if abs(resid) > V.csm_amort_tol(abs(amort)):
        key = f"{cname[c]}|{q}"
        ytd_resid = None
        r = V.csm_amort_residual({"원수CSM상각": pv[(c, q)].get("4"), "수재CSM상각": pv[(c, q)].get("4-1")}, {"CSM상각": cv[(c, q)].get(5)})
        if r: ytd_resid = r[0]
        p = prevq(q)
        rp = None
        if p and (c, p) in pv and (c, p) in cv:
            rr = V.csm_amort_residual({"원수CSM상각": pv[(c, p)].get("4"), "수재CSM상각": pv[(c, p)].get("4-1")}, {"CSM상각": cv[(c, p)].get(5)})
            rp = rr[0] if rr else None
        xa.append((c, cname[c], q, resid, ytd_resid, rp, key in ledger, (p and f"{cname[c]}|{p}" in ledger)))
P(f"\n== SQ_AMORT  evaluated={xa_n} fail={len(xa)}  (tol = CSM_AMORT tol on |상각_q|)")
for x in sorted(xa, key=lambda x: (x[0], x[2])):
    P(f"   AMORT {x[0]} {x[1]} {x[2]} resid_q={x[3]:+.2f}억  ytd_resid(q)={x[4]} ytd_resid(q-1)={x[5]}  ledger(q)={x[6]} ledger(q-1)={x[7]}")
res["sq_amort_fail"] = [list(x) for x in xa]
res["pl_deriv_bad"] = [list(x) for x in pd_rows]
res["csm_deriv_bad"] = [list(x) for x in deriv_bad]
(HERE / "s1_sim.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
(HERE / "s1_sim.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print("\n".join(out))
