# -*- coding: utf-8 -*-
"""a11 (read-only): does "the first-printed table of a twin cluster is the current period" hold on the raw XML?

Uses the PRODUCTION helpers of the fixed builder (V._twin_shape / V._row_stubs / V._stubs_alike) to cluster the eligible candidates of
every extracted *_csm.json, then checks the raw reference-date marker that DIRECTLY introduces each table (a paragraph, a SPAN, or a
one-row mini-table right above it; `adj` oracle only -- the far oracle is noise-prone).
Reports per cluster size: how many clusters have a marker on the first-printed member / on later members, and every violation.
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/amort_fix_20261011/a11_order_rule_proof.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")

from amortlib import V, eligible, iter_files  # noqa: E402
from rawroles import raw_lines_for, raw_role  # noqa: E402

stat = Counter()
viol = []
explicit = Counter()
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
    clusters = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)
    for members in clusters.values():
        if len(members) < 2:
            stat["clusters_size1"] += 1
            continue
        members.sort(key=lambda i: (int(cands[i].get("line_no") or 0), i))
        lines_tied = len({int(cands[i].get("line_no") or 0) for i in members}) < len(members)
        roles = []
        for i in members:
            b = cands[i]
            lines = raw_lines_for(rcept, str(b.get("_source_xml") or ""))
            if lines is None:
                roles.append("no_raw")
            else:
                r, _, _ = raw_role(lines, int(b.get("line_no") or 0))
                roles.append(r or "-")
        k = len(members)
        stat[f"clusters_size{k}"] += 1
        if lines_tied:
            stat["clusters_with_tied_line_no"] += 1
        known = [(pos, r) for pos, r in enumerate(roles) if r in ("cur", "prior")]
        if not known:
            stat["clusters_no_adjacent_marker"] += 1
            continue
        stat["clusters_with_adjacent_marker"] += 1
        # the rule says: position 0 is cur, the rest are not the picked cur.  For size-2 clusters positions 1 must be prior.
        first_ok = roles[0] in ("cur", "-", "no_raw")
        if roles[0] == "prior":
            viol.append((company, rcept, "FIRST_IS_PRIOR", roles, [cands[i].get("line_no") for i in members]))
        if k == 2 and roles[1] == "cur":
            viol.append((company, rcept, "SECOND_IS_CUR", roles, [cands[i].get("line_no") for i in members]))
        if k == 2 and roles[0] == "cur" and roles[1] == "prior":
            stat["size2_cur_then_prior"] += 1
        if k >= 4:
            stat[f"size{k}_sequence_" + "".join(r[0] for r in roles)] += 1
        for i in members:
            pass
print("stats:")
for k in sorted(stat):
    print(f"  {k}: {stat[k]}")
print("violations of 'first printed = current':", len(viol))
for v in viol:
    print("  ", v)
