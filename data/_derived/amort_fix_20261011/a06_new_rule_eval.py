# -*- coding: utf-8 -*-
"""a06 (read-only): evaluate the proposed selection rule BEFORE touching the builder.

  old : viz_build_ifrs17_panels._pick_amort_block over the eligible candidates (current behaviour)
  new : collapse every period-twin group (same _source_xml + same caption (period tags stripped) + same header signature) to its
        FIRST printed member (lowest line_no, ties by list order), then run the OLD picker on the survivors.

For every extracted *_csm.json: old pick / new pick (line, raw role) and, via the real extract_amort_schedule (monkey-patched),
the panel result (total, y1) for both.  Output a06_new_rule_eval.json + console table.
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/amort_fix_20261011/a06_new_rule_eval.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")

from amortlib import V, eligible, iter_files  # noqa: E402
from rawroles import far_role, raw_lines_for, raw_role  # noqa: E402

OLD_PICK = V._pick_amort_block
TAG_RE = re.compile(r"제\d+\((?:당|전)\)기")


def hsig(b):
    flat = V._flatten_header(b.get("header") or [])
    return TAG_RE.sub("", "|".join(re.sub(r"\s+", "", c) for c in flat))


def group_key(b):
    cap = re.sub(r"<[^<>]*>", "", re.sub(r"\s+", "", str(b.get("caption") or "")))
    return (b.get("_source_xml"), cap, hsig(b))


def new_pick(blocks):
    if not blocks:
        return None
    first = {}
    for idx, b in enumerate(blocks):
        k = group_key(b)
        cur = (int(b.get("line_no") or 0), idx)
        if k not in first or cur < first[k][0]:
            first[k] = (cur, b)
    return OLD_PICK([v[1] for v in first.values()])


def role_of(rcept, b):
    lines = raw_lines_for(rcept, str(b.get("_source_xml") or ""))
    if lines is None:
        return "no_raw"
    ln = int(b.get("line_no") or 0)
    r, _, _ = raw_role(lines, ln)
    if r:
        return r + "(adj)"
    r, d, _ = far_role(lines, ln)
    return (r + f"(far@{d})") if r else "?"


def panel(blocks, company, picker):
    V._pick_amort_block = picker
    try:
        return V.extract_amort_schedule(blocks, company)
    finally:
        V._pick_amort_block = OLD_PICK


rows = []
for company, rcept, path, blocks in iter_files():
    cands = [b for b in blocks if eligible(b)]
    o, n = OLD_PICK(cands), new_pick(cands)
    rec = {"company": company, "rcept": rcept, "n_elig": len(cands),
           "old_line": None if o is None else o.get("line_no"), "new_line": None if n is None else n.get("line_no"),
           "old_src": None if o is None else o.get("_source_xml"), "new_src": None if n is None else n.get("_source_xml"),
           "changed": (o is not n),
           "old_role": None if o is None else role_of(rcept, o), "new_role": None if n is None else role_of(rcept, n)}
    po, pn = panel(blocks, company, OLD_PICK), panel(blocks, company, new_pick)
    for tag, p in (("old", po), ("new", pn)):
        rec[tag + "_total"] = None if not p else (p.get("buckets") or {}).get("total")
        rec[tag + "_y1"] = None if not p else (p.get("yearly") or {}).get("y1")
        rec[tag + "_status"] = None if not p else p.get("status")
    rows.append(rec)

(W / "a06_new_rule_eval.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(f"files {len(rows)} | pick changed in {sum(1 for r in rows if r['changed'])}")
for r in rows:
    if r["changed"]:
        print(f"CHANGED {r['company']:<18s} {r['rcept']} elig={r['n_elig']:<3} old L{r['old_line']}[{r['old_role']}] tot={r['old_total']} y1={r['old_y1']}  ->  new L{r['new_line']}[{r['new_role']}] tot={r['new_total']} y1={r['new_y1']}")
print("\nNOT changed but old pick's raw role is prior:")
for r in rows:
    if not r["changed"] and str(r["old_role"]).startswith("prior"):
        print(f"  {r['company']:<18s} {r['rcept']} old L{r['old_line']}[{r['old_role']}] tot={r['old_total']}")
