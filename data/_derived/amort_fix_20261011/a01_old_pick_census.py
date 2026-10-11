# -*- coding: utf-8 -*-
"""a01 (read-only): for EVERY data/dart/extracted/*_csm.json (all companies, all filings) replay the CURRENT picker
(viz_build_ifrs17_panels._pick_amort_block over the same `_eligible` candidate list) and, where the raw DART XML is on this
disk (FY2025 only; data/dart/**/raw/ is git-ignored), read the true reference-date role of every candidate from the paragraph
that introduces the table (<당기말> / <전기말>, see rawroles.py).

Output: a01_old_pick_census.json  +  a console table of every file whose current pick is NOT a 'cur' table or whose candidate
list contains >1 same-shape table (twin group).
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/amort_fix_20261011/a01_old_pick_census.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")

import viz_build_ifrs17_panels as V  # noqa: E402
from rawroles import raw_lines_for, raw_role  # noqa: E402

KW = ("상각", "인식", "예상", "기대", "CSM")


def eligible(b: dict) -> bool:
    """verbatim copy of the nested `_eligible` in extract_amort_schedule (kept in sync by a03)"""
    if not any(k in str(b.get("caption") or "") for k in KW):
        return False
    if V.header_has_year_buckets(b.get("header") or []):
        return True
    rows = b.get("rows") or []
    for k in range(min(3, len(rows))):
        if V._row_has_year_buckets(rows[k]):
            return True
    stubs = [str(r[0]).strip() for r in rows[:6] if r]
    return sum(1 for s in stubs if V._classify_bucket_cell(s) is not None) >= 3


def total_of(b: dict):
    """the 합계/계 value of the block as the panel would read it (raw units), None if not a plain header-bucket table"""
    sched = V.extract_amort_schedule([b], "")
    return sched


out = []
for p in sorted(V.SRC.glob("*_csm.json")):
    m = V._FILENAME_RE.match(p.stem)
    if not m:
        continue
    company, rcept = m.group(1), m.group(2)
    blocks = json.loads(p.read_text(encoding="utf-8"))
    blocks = blocks if isinstance(blocks, list) else [blocks]
    cands = [b for b in blocks if eligible(b)]
    old = V._pick_amort_block(cands)
    rec = {"file": p.name, "company": company, "rcept": rcept, "n_blocks": len(blocks), "n_eligible": len(cands),
           "old_pick_line": None if old is None else old.get("line_no"),
           "old_pick_src": None if old is None else old.get("_source_xml"), "cands": []}
    for b in cands:
        lines = raw_lines_for(rcept, str(b.get("_source_xml") or ""))
        if lines is None:
            role, pl, ptxt = "no_raw", None, None
        else:
            role, pl, ptxt = raw_role(lines, int(b.get("line_no") or 0))
        rec["cands"].append({
            "line_no": b.get("line_no"), "src": b.get("_source_xml"), "score": b.get("score"),
            "n_rows": len(b.get("rows") or []), "bucket_cols": V._bucket_columns_count(b),
            "caption": str(b.get("caption") or "")[:110], "header0": V._flatten_header(b.get("header") or [])[:14],
            "role": role, "para_line": pl, "para_txt": ptxt,
            "is_old_pick": old is not None and b is old,
        })
    out.append(rec)

(W / "a01_old_pick_census.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

print(f"files: {len(out)}  (with raw on disk: {sum(1 for r in out if any(c['role'] != 'no_raw' for c in r['cands']))})")
n_prior = n_none = n_cur = 0
for r in out:
    pk = next((c for c in r["cands"] if c["is_old_pick"]), None)
    roles = [c["role"] for c in r["cands"]]
    if pk is None:
        print(f"  {r['company']:<20s} {r['rcept']} no eligible candidate")
        continue
    flag = ""
    if pk["role"] == "prior":
        n_prior += 1
        flag = "  <== OLD PICK IS THE PRIOR-PERIOD TABLE"
    elif pk["role"] == "cur":
        n_cur += 1
    elif pk["role"] is None:
        n_none += 1
        flag = "  (introducing paragraph has no marker)"
    if flag or r["rcept"].startswith("2026"):
        print(f"  {r['company']:<20s} {r['rcept']} elig={r['n_eligible']} pick line {pk['line_no']} role={pk['role']} roles={roles}{flag}")
print("\nold pick role (raw-verified files only): cur", n_cur, "| prior", n_prior, "| no marker", n_none)
