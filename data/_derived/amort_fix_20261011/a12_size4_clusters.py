# -*- coding: utf-8 -*-
"""a12 (read-only): the 17 twin clusters of size 4 (two pairs with identical caption + header + row labels): are the two 'current'
members the same numbers (a note printed twice) or two different sub-tables?  Prints, per cluster, each member's line_no, adjacent raw
role and the (y1, total) the panel would compute from that block alone."""
from __future__ import annotations

import sys
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")

from amortlib import V, eligible, iter_files  # noqa: E402
from rawroles import raw_lines_for, raw_role  # noqa: E402

for company, rcept, path, blocks in iter_files():
    cands = [b for b in blocks if eligible(b)]
    n = len(cands)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    shapes = [V._twin_shape(b) for b in cands]
    stubs = [V._row_stubs(b) for b in cands]
    for i in range(n):
        for j in range(i + 1, n):
            if shapes[i] == shapes[j] and V._stubs_alike(stubs[i], stubs[j]):
                parent[find(i)] = find(j)
    cl = {}
    for i in range(n):
        cl.setdefault(find(i), []).append(i)
    for members in cl.values():
        if len(members) < 4:
            continue
        members.sort(key=lambda i: (int(cands[i].get("line_no") or 0), i))
        print(f"{company} {rcept}  cluster of {len(members)}  src={cands[members[0]].get('_source_xml')}")
        for i in members:
            b = cands[i]
            lines = raw_lines_for(rcept, str(b.get("_source_xml") or ""))
            role = "no_raw" if lines is None else (raw_role(lines, int(b.get("line_no") or 0))[0] or "-")
            r = V.extract_amort_schedule([b], company) or {}
            print(f"     L{b.get('line_no'):<6} role={role:<6} rows={len(b.get('rows') or []):<3} y1={(r.get('yearly') or {}).get('y1')} total={(r.get('buckets') or {}).get('total')}")
