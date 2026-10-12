"""Read-only census v2: like s11, plus (a) the builder's own CURRENT-column extraction of the same filing (fidelity self-test against
CSM_waterfall.json) and (b) in-filing consistency flags for the PRIOR column:
  c_open_ok : (interim) prior opening == prior opening of the same-year annual filing, within max(0.15, 0.1%)
  c_chain_ok: (annual)  prior closing == current opening of the same annual filing (a filing's own year-start balance), within max(0.15, 0.1%)
A prior vector is TRUSTED only when its filing's current extraction reproduces the master (fidelity) AND the relevant consistency flag holds.
Output csm_prior_scan_v2.csv
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import prior_csm as P  # noqa: E402

B = P.B
master = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
M, NAMES = {}, {}
for r in master:
    M.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
    NAMES[r["원보험사코드"]] = r["원수사명"]

LATER = [f"{y}.{n}Q" for y in (2024, 2025, 2026) for n in (1, 2, 3, 4) if f"{y}.{n}Q" <= "2026.2Q"]


def raw_dirs(kr, q):
    fy = f"FY{q[:4]}_Q{q[5]}"
    return sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*"))


def tol(v):
    return max(0.15, abs(v) * 0.0005) if v is not None else 0.15


def close(a, b, rel=0.001):
    if a is None or b is None:
        return None
    return abs(a - b) <= max(0.15, rel * max(abs(a), abs(b)))


def cmp_vec(pv, mv):
    if not pv or not mv:
        return None, []
    bad = []
    for k in range(1, 7):
        a, b = pv.get(k), mv.get(k)
        if a is None or b is None:
            continue
        if abs(a - b) > tol(b):
            bad.append(k)
    return ("DIFF" if bad else "SAME"), bad


def main():
    krs = sorted({d.name.split("_")[0] for fy in (ROOT / "data/dart").glob("FY*_Q*") for d in (fy / "raw").glob("KR*") if d.is_dir()})
    out = []
    t0 = time.time()
    for kr in krs:
        name = NAMES.get(kr) or B.META.get(kr, (kr,))[0]
        ann_prior, ann_cur = {}, {}
        for y in (2023, 2024, 2025):
            for rd in raw_dirs(kr, f"{y}.4Q"):
                try:
                    cv, _ = P.current_waterfall(rd, name, None)
                except Exception:
                    cv = None
                if cv:
                    ann_cur[y] = cv
        for y in (2024, 2025):
            for rd in raw_dirs(kr, f"{y}.4Q"):
                try:
                    pv, _s, _n = P.prior_waterfall(rd, name, None)
                except Exception:
                    pv = None
                if pv:
                    ann_prior[y] = pv
        for q in LATER:
            for rd in raw_dirs(kr, q):
                y = int(q[:4])
                qprev = f"{y-1}{q[4:]}"
                row = {"kr": kr, "name": name, "later_q": q, "prior_q": qprev, "dir": rd.name}
                try:
                    anchor_p = None if q.endswith("4Q") else ((ann_prior.get(y) or {}).get(1) or M.get((kr, f"{y-1}.4Q"), {}).get(1))
                    pv, src, n = P.prior_waterfall(rd, name, anchor_p)
                    anchor_c = None if q.endswith("4Q") else ((ann_cur.get(y) or {}).get(1) or (ann_cur.get(y - 1) or {}).get(6))
                    cv = None
                    try:
                        cv, csrc = P.current_waterfall(rd, name, anchor_c)
                    except Exception:
                        csrc = "ERR"
                    row.update(anchor_p=anchor_p, n_prior_blocks=n, src=src)
                    st_cur, bad_cur = cmp_vec(cv, M.get((kr, q)))
                    row["fidelity"] = st_cur or "NA"
                    row["fidelity_bad"] = ",".join(map(str, bad_cur))
                    mv = M.get((kr, qprev))
                    if pv is None:
                        row["status"] = "NO_PRIOR"
                    elif not mv:
                        row["status"] = "NO_MASTER"
                    else:
                        stt, bad = cmp_vec(pv, mv)
                        row["status"] = stt
                        row["diff_items"] = ",".join(map(str, bad))
                    # consistency flags
                    if pv is not None:
                        if q.endswith("4Q"):
                            cur_open = (cv or {}).get(1) if cv else None
                            row["c_chain_ok"] = close(pv.get(6), cur_open)
                            row["cur_open"] = cur_open
                        else:
                            ap = ann_prior.get(y)
                            row["c_open_ok"] = close(pv.get(1), (ap or {}).get(1)) if ap else None
                    for k in range(1, 7):
                        row[f"p{k}"] = (pv or {}).get(k)
                        row[f"m{k}"] = (M.get((kr, qprev)) or {}).get(k)
                        row[f"c{k}"] = (cv or {}).get(k)
                except Exception as e:
                    row["status"] = "ERR"
                    row["src"] = f"{type(e).__name__}: {e}"[:200]
                out.append(row)
        print(f"{kr} {name} {round(time.time()-t0)}s", flush=True)
    cols = ["kr", "name", "later_q", "prior_q", "dir", "status", "diff_items", "fidelity", "fidelity_bad", "c_open_ok", "c_chain_ok", "cur_open",
            "anchor_p", "n_prior_blocks", "src"] + [f"p{k}" for k in range(1, 7)] + [f"m{k}" for k in range(1, 7)] + [f"c{k}" for k in range(1, 7)]
    with open(HERE / "csm_prior_scan_v2.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    print(Counter(r["status"] for r in out))
    print("fidelity", Counter(r.get("fidelity") for r in out))


if __name__ == "__main__":
    main()
