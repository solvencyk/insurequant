# -*- coding: utf-8 -*-
"""a04 (read-only): test the candidate "document order inside a same-shape group" rule against the raw XML reference-date markers.

For every extracted *_csm.json whose raw DART XML is on this disk:
  group the eligible candidates by KEY = (_source_xml, caption, header signature)  [KEY variants are tried]
  rank inside the group by line_no; predicted role = 'cur' for rank 0, 'prior' for rank >= 1
  oracle role = adjacent marker (paragraph / mini-table above the table) else the nearest marker anywhere above (far)
  report every group where the prediction disagrees with the oracle and a summary.
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/amort_fix_20261011/a04_twin_rule_vs_raw.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")

from amortlib import V, eligible, iter_files  # noqa: E402
from rawroles import far_role, raw_lines_for, raw_role  # noqa: E402

TAG_RE = re.compile(r"제\d+\((?:당|전)\)기")


def hsig(b: dict) -> str:
    flat = V._flatten_header(b.get("header") or [])
    return TAG_RE.sub("", "|".join(re.sub(r"\s+", "", c) for c in flat))


def key_of(b: dict, variant: str):
    cap = re.sub(r"\s+", "", str(b.get("caption") or ""))
    cap = re.sub(r"<[^<>]*>", "", cap)        # a trailing <당기말> on the inherited caption must not split a pair
    if variant == "src+cap+hdr":
        return (b.get("_source_xml"), cap, hsig(b))
    if variant == "src+cap+hdr+rows":
        return (b.get("_source_xml"), cap, hsig(b), tuple(re.sub(r"\s+", "", str((r or [""])[0])) for r in (b.get("rows") or [])))
    raise ValueError(variant)


def oracle(rcept: str, b: dict):
    lines = raw_lines_for(rcept, str(b.get("_source_xml") or ""))
    if lines is None:
        return None, None
    ln = int(b["line_no"])
    role, _, _ = raw_role(lines, ln)
    if role:
        return role, "adj"
    role, dist, _ = far_role(lines, ln)
    return role, ("far" if role else None)


variant = sys.argv[1] if len(sys.argv) > 1 else "src+cap+hdr"
tot = Counter()
bad = []
size_dist = Counter()
for company, rcept, path, blocks in iter_files():
    cands = [b for b in blocks if eligible(b)]
    groups = defaultdict(list)
    for b in cands:
        groups[key_of(b, variant)].append(b)
    for k, mem in groups.items():
        mem.sort(key=lambda b: int(b.get("line_no") or 0))
        size_dist[len(mem)] += 1
        for rank, b in enumerate(mem):
            o, how = oracle(rcept, b)
            if o is None:
                tot["no_oracle"] += 1
                continue
            pred = "cur" if rank == 0 else "prior"
            if pred == o:
                tot[f"ok_{how}"] += 1
            else:
                tot[f"MISMATCH_{how}"] += 1
                bad.append((company, rcept, b.get("_source_xml"), b.get("line_no"), rank, len(mem), o, how, str(b.get("caption"))[:60]))
print("variant:", variant)
print("group size distribution:", dict(sorted(size_dist.items())))
print("summary:", dict(tot))
for x in bad:
    print("  MISMATCH", x)
