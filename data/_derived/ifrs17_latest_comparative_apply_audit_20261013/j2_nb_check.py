import json, os, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
def git(rev, path):
    return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:{path}"]).decode("utf-8"))
new = git("HEAD", "NB_CSM_multiple.json"); old = git("b8c37fff", "NB_CSM_multiple.json")
csm = {}
for r in json.load(open(REPO + "/CSM_waterfall.json", encoding="utf-8")):
    csm[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = float(r["값"])
out = open(here + "/j2_nb_check.txt", "w", encoding="utf-8")
# 1) diff of the file between b8c37fff and HEAD
changed = []
for a, b in zip(old, new):
    for k in b:
        if a.get(k) != b.get(k): changed.append((b["원보험사코드"], b["공시분기"], k, a.get(k), b.get(k)))
out.write(f"rows old={len(old)} new={len(new)} changed leaves={len(changed)}\n")
# 2) recompute every row of the changed companies/quarters
def prevq(q):
    y, n = int(q[:4]), int(q[5]); return f"{y}.{n-1}Q" if n > 1 else None
bad = 0
rows = {(r["원보험사코드"], r["공시분기"]): r for r in new}
for (code, q), r in sorted(rows.items()):
    if (code, q) not in {("KR0087", "2023.1Q"), ("KR0087", "2023.2Q"), ("KR0001", "2023.3Q"), ("KR0001", "2023.4Q"), ("KR0087", "2023.3Q"), ("KR0001", "2023.2Q")}: continue
    ytd = csm.get((code, q, 2)); pq = prevq(q); pytd = csm.get((code, pq, 2)) if pq else 0.0
    nb_ytd = r.get("신계약CSM_연누계"); nb_q = r.get("신계약CSM_당분기")
    w_ytd = r.get("월납월초보험료_연누계"); w_q = r.get("월납월초보험료_당분기")
    exp_q = (ytd - pytd) if (ytd is not None and pytd is not None) else None
    ok1 = ytd is not None and nb_ytd is not None and abs(nb_ytd - ytd) < 0.051
    ok2 = exp_q is not None and nb_q is not None and abs(nb_q - exp_q) < 0.051
    m_ytd = nb_ytd / w_ytd if (nb_ytd is not None and w_ytd) else None
    m_q = nb_q / w_q if (nb_q is not None and w_q) else None
    ok3 = m_ytd is not None and abs(m_ytd - r["신계약CSM배수_연누계"]) < 6e-4
    ok4 = m_q is not None and abs(m_q - r["신계약CSM배수_당분기"]) < 6e-4
    bad += (not (ok1 and ok2 and ok3 and ok4))
    out.write(f"{code} {q}: CSM item2 YTD(master)={ytd} prev={pytd} -> NB ytd {nb_ytd} (ok {ok1}) quarter {nb_q} vs {exp_q} (ok {ok2}) | multiple ytd {r['신계약CSM배수_연누계']} vs {m_ytd and round(m_ytd,4)} (ok {ok3}) quarter {r['신계약CSM배수_당분기']} vs {m_q and round(m_q,4)} (ok {ok4})\n")
# 3) denominators unchanged
for a, b in zip(old, new):
    for k in ("월납월초보험료_연누계", "월납월초보험료_당분기"):
        if a.get(k) != b.get(k): out.write(f"DENOMINATOR CHANGED {b['원보험사코드']} {b['공시분기']} {k} {a.get(k)} -> {b.get(k)}\n")
for c in changed: out.write(f"   changed: {c}\n")
out.write(f"bad rows: {bad}\n")
