# -*- coding: utf-8 -*-
"""a10 (read-only): per-company proof table for the FY2025 filings whose selection moved (a08 before/after).

For each company (the filing that feeds the panel, i.e. the latest rcept with status ok):
  raw role of the OLD and NEW pick (adjacent marker paragraph / mini-table, else nearest marker above), explicit 당/전 tag inside the
  block's own header/caption, the schedule total (억원) before/after, the CSM_waterfall closing of the same FY (2025.4Q) and of the
  year before (2024.4Q), and the FY2024-filing cross-check: that filing's CURRENT-year schedule must equal this filing's PRIOR-year
  schedule (old pick) -- the same 2024-12-31 numbers printed twice.
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/amort_fix_20261011/a10_final_proof.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")

from amortlib import V  # noqa: E402
from rawroles import far_role, raw_lines_for, raw_role  # noqa: E402

before = json.loads((W / "a08_selection_before.json").read_text(encoding="utf-8"))
after = json.loads((W / "a08_selection_after.json").read_text(encoding="utf-8"))
wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
close = {(r["원수사명"], r["공시분기"]): r["값"] for r in wf if r["항목번호"] == 6 and r.get("값") is not None}
ALIAS = V._CSM_NAME_ALIAS
TAG = re.compile(r"제\s*\d+\s*\(\s*(당|전)\s*\)\s*기")


def master_name(co: str) -> str:
    return ALIAS.get(co, co)


def block_of(fname: str, line: int, src: str):
    blocks = json.loads((V.SRC / fname).read_text(encoding="utf-8"))
    for b in blocks:
        if b.get("line_no") == line and b.get("_source_xml") == src:
            return b
    return None


def role(rcept: str, b: dict) -> str:
    lines = raw_lines_for(rcept, str(b.get("_source_xml") or ""))
    if lines is None:
        return "no_raw"
    ln = int(b.get("line_no") or 0)
    r, _, _ = raw_role(lines, ln)
    if r:
        return r + "/adj"
    r, d, _ = far_role(lines, ln)
    return f"{r}/far@{d}" if r else "-"


def tag_in_block(b: dict) -> str:
    txt = " ".join([str(b.get("caption") or "")] + [str(c) for hr in (b.get("header") or []) for c in hr] + [str(x) for x in (b.get("footnotes") or [])])
    m = TAG.search(txt)
    return ("당" if m.group(1) == "당" else "전") if m else "-"


# the panel entry per company = the latest rcept with the best status; here: latest rcept among files that exist
by_co = {}
for fname, rec in after.items():
    by_co.setdefault(rec["company"], []).append((rec["rcept"], fname))
rows = []
for co, lst in sorted(by_co.items()):
    lst.sort()
    rc, fn = lst[-1]
    if not rc.startswith("2026"):
        continue
    # pick the latest-rcept file whose result is the panel's (status rank then rcept)
    rank = {"ok": 3, "partial": 2, "empty": 1}
    best = max(lst, key=lambda t: (rank.get((after[t[1]]["result"] or {}).get("status"), 0), t[0]))
    rc, fn = best
    b, a = before[fn], after[fn]
    moved = (b["pick_line"], b["pick_src"]) != (a["pick_line"], a["pick_src"])
    fy = int(rc[:4]) - 1
    mn = master_name(co)
    cN, cP = close.get((mn, f"{fy}.4Q")), close.get((mn, f"{fy - 1}.4Q"))
    tb = ((b["result"] or {}).get("buckets") or {}).get("total")
    ta = ((a["result"] or {}).get("buckets") or {}).get("total")
    ob = block_of(fn, b["pick_line"], b["pick_src"]) if b["pick_line"] else None
    nb = block_of(fn, a["pick_line"], a["pick_src"]) if a["pick_line"] else None
    # FY2024-filing cross-check
    prev = [x for x in lst if x[0][:4] == str(int(rc[:4]) - 1)]
    x24 = None
    if prev:
        pr = after[prev[-1][1]]["result"] or {}
        x24 = ((pr.get("yearly") or {}).get("y1"), (pr.get("buckets") or {}).get("total"))
    rows.append({
        "company": co, "rcept": rc, "moved": moved,
        "old": [b["pick_line"], role(rc, ob) if ob else None, tag_in_block(ob) if ob else None],
        "new": [a["pick_line"], role(rc, nb) if nb else None, tag_in_block(nb) if nb else None],
        "total_before": tb, "total_after": ta, "close_FY": cN, "close_FY-1": cP,
        "rel_old_vs_FY-1": None if not (tb and cP) else round(abs(tb / cP - 1), 5),
        "rel_new_vs_FY": None if not (ta and cN) else round(abs(ta / cN - 1), 5),
        "fy24filing_cur_y1_total": x24,
        "y1_old": (b["result"] or {}).get("yearly", {}).get("y1") if b["result"] else None,
        "y1_new": (a["result"] or {}).get("yearly", {}).get("y1") if a["result"] else None,
    })
(W / "a10_final_proof.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(f"{'company':<14s} mv  old(line,role,tag)                new(line,role,tag)              total old -> new     close FY / FY-1      |old-FY-1| |new-FY|  FY2024 filing cur (y1,total)")
for r in rows:
    print(f"{r['company']:<14s} {'Y' if r['moved'] else '.'}  {str(r['old']):<34s} {str(r['new']):<34s} {r['total_before']} -> {r['total_after']}  {r['close_FY']} / {r['close_FY-1']}  {r['rel_old_vs_FY-1']} {r['rel_new_vs_FY']}  {r['fy24filing_cur_y1_total']}")
