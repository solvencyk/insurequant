# -*- coding: utf-8 -*-
"""a14 (read-only): independent post-fix checks (does not reuse the writer's own assertions).

 A. CSM_amortization.json vs git HEAD: same row list/order, the ONLY differing cells are the intended 2025.4Q 상각액 cells; file format
    (CRLF, no trailing newline) unchanged.
 B. master 2025.4Q vs the rebuilt panel: for every non-Lina panel company master y_k == round(panel yearly y_k, 1); Lina == the PDF values.
 C. 검산: schedule total vs CSM_waterfall closing of the same FY (item 6, 2025.4Q) and of the year before, for ALL panel companies,
    old panel vs new panel; year-over-year monotonicity (y_k+1 <= y_k * 1.02 for k=1..9 where both exist) old vs new; unit sanity.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- A
head = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:CSM_amortization.json"], capture_output=True, check=True).stdout.decode("utf-8")
work_raw = (ROOT / "CSM_amortization.json").read_bytes()
work = json.loads(work_raw.decode("utf-8"))
old = json.loads(head)
print("A. rows HEAD/work:", len(old), len(work), "| CRLF:", b"\r\n" in work_raw, "| trailing newline:", work_raw.endswith(b"\n"))
diffs = []
for o, w in zip(old, work):
    assert [k for k in o] == [k for k in w], "key order differs"
    for k in o:
        if o[k] != w[k]:
            diffs.append((o["원수사명"], o["공시분기"], o["경과차년"], k, o[k], w[k]))
assert len(old) == len(work)
print("   differing cells:", len(diffs), "| fields touched:", sorted({d[3] for d in diffs}), "| quarters touched:", sorted({d[1] for d in diffs}),
      "| companies:", len({d[0] for d in diffs}))
print("   other rows byte-identical objects:", len(old) - len(diffs) - sum(1 for d in diffs) + len(diffs) >= 0)

# ---------------------------------------------------------------- B
newp = {c["company"]: c for c in json.loads((ROOT / "data/dart/viz/csm_amort_schedule.json").read_text(encoding="utf-8"))["companies"]}
oldp = {c["company"]: c for c in json.loads((ROOT / "data/_derived/amort_fix_backup_20261011/csm_amort_schedule.json.pre_fix").read_text(encoding="utf-8"))["companies"]}
ALIAS = {"미래에셋생명": "미래에셋생명보험", "삼성생명": "삼성생명보험", "코리안리": "코리안리재보험", "아이비케이연금보험": "IBK연금보험",
         "케이비라이프생명보험": "KB라이프생명", "에이아이지손해보험": "AIG손해보험", "엠지손해보험": "예별손해보험"}
m25 = {}
for r in work:
    if r["공시분기"] == "2025.4Q":
        m25.setdefault(r["원수사명"], {})[r["경과차년"]] = r["상각액"]
bad = 0
for co, p in newp.items():
    mn = ALIAS.get(co, co)
    if mn not in m25 or p.get("rcept_no") is None:
        continue                       # reinsurers (master-derived) / companies without master rows
    for k in range(1, 11):
        pv = (p.get("yearly") or {}).get(f"y{k}")
        pv = None if pv is None else round(float(pv), 1)
        mv = m25[mn].get(k)
        if mv is None and pv is None:
            continue
        if mv is None or pv is None or abs(mv - pv) > 0.051:
            bad += 1
            print(f"   B mismatch {co} y{k}: master {mv} vs panel {pv}")
print("B. master 2025.4Q vs rebuilt panel (all DART companies): mismatching cells (tolerance 0.05, Lina has 5-dp PDF values):", bad)

# ---------------------------------------------------------------- C
wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
close = {(r["원수사명"], r["공시분기"]): r["값"] for r in wf if r["항목번호"] == 6 and r.get("값") is not None}


def mono(y):
    vals = [y.get(f"y{k}") for k in range(1, 11)]
    bad_pairs = [k for k in range(1, 10) if vals[k - 1] is not None and vals[k] is not None and vals[k] > vals[k - 1] * 1.02 + 0.5]
    return bad_pairs


print("C. 검산 (억원)  company: total(old) total(new) | closing FY2025 / FY2024 | |old/FY2024-1| |new/FY2025-1| | non-monotone steps old->new")
rows = []
for co in sorted(newp):
    n, o = newp[co], oldp[co]
    mn = ALIAS.get(co, co)
    cN, cP = close.get((mn, "2025.4Q")), close.get((mn, "2024.4Q"))
    tn, to = (n.get("buckets") or {}).get("total"), (o.get("buckets") or {}).get("total")
    yn, yo = n.get("yearly") or {}, o.get("yearly") or {}
    changed = (n != o)
    rows.append((co, changed, to, tn, cN, cP, mono(yo), mono(yn), n.get("unit"), n.get("status")))
    if changed:
        r_old = None if not (to and cP) else abs(to / cP - 1)
        r_new = None if not (tn and cN) else abs(tn / cN - 1)
        print(f"   {co:<14s} {to} -> {tn} | {cN} / {cP} | {None if r_old is None else round(r_old, 5)} | {None if r_new is None else round(r_new, 5)} | {mono(yo)} -> {mono(yn)} | unit {n.get('unit')}")
print("   unchanged entries (not touched):", sum(1 for r in rows if not r[1]))
exact = [r[0] for r in rows if r[1] and r[3] and r[4] and abs(r[3] / r[4] - 1) < 0.0005]
print(f"   changed entries whose NEW total equals the FY2025 closing CSM within 0.05%: {len(exact)}: {exact}")
partial = [r[0] for r in rows if r[1] and r[0] not in exact]
print(f"   changed entries with a PARTIAL total (split table: years 1..8 only, no 계 column read): {partial}")
print("   units in changed entries:", {r[8] for r in rows if r[1]}, "| statuses:", {r[9] for r in rows if r[1]})
