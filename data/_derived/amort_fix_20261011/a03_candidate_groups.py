# -*- coding: utf-8 -*-
"""a03 (read-only): show, for the newest filing(s) of the given companies, every eligible amortisation candidate with its
shape (header signature, row labels), its 합계 value, and the raw reference-date role (adjacent + far).
Usage: a03_candidate_groups.py <company> [<company> ...] [--all]   (--all: every filing, not only rcept 2026...)"""
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
from rawroles import raw_lines_for, raw_role, far_role  # noqa: E402
from amortlib import eligible  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
every = "--all" in sys.argv


def hsig(b):
    flat = V._flatten_header(b.get("header") or [])
    return "|".join(flat)[:90]


def total_of(b):
    rows = b.get("rows") or []
    for r in rows:
        if r and "합계" in str(r[0]).replace(" ", ""):
            nums = [V.parse_num(c) for c in r[1:]]
            nums = [n for n in nums if n is not None]
            return (nums[-1] if nums else None), len(nums)
    return None, 0


for p in sorted(V.SRC.glob("*_csm.json")):
    m = V._FILENAME_RE.match(p.stem)
    company, rcept = m.group(1), m.group(2)
    if args and company not in args:
        continue
    if not every and not rcept.startswith("2026"):
        continue
    blocks = json.loads(p.read_text(encoding="utf-8"))
    cands = [b for b in blocks if eligible(b)]
    old = V._pick_amort_block(cands)
    print("=" * 110)
    print(company, rcept, "eligible", len(cands), "old pick line", None if old is None else old.get("line_no"))
    for b in sorted(cands, key=lambda b: (str(b.get("_source_xml")), b.get("line_no") or 0)):
        lines = raw_lines_for(rcept, str(b.get("_source_xml") or ""))
        if lines is None:
            adj = far = ("no_raw", None)
        else:
            adj = raw_role(lines, int(b["line_no"]))[:2]
            far = far_role(lines, int(b["line_no"]))[:2]
        tot, n = total_of(b)
        labels = [str((r or [""])[0])[:10] for r in (b.get("rows") or [])[:3]]
        print(f"  {str(b.get('_source_xml'))[-12:]:>12s} L{b.get('line_no'):<6} sc{b.get('score')} rows{len(b.get('rows') or []):<3} bc{V._bucket_columns_count(b):<3} adj={adj[0]!s:<6} far={far[0]!s:<6}@{far[1]} {'*PICK*' if old is not None and b is old else '      '} tot={tot} (n={n}) hdr={hsig(b)!r} lab={labels}")
