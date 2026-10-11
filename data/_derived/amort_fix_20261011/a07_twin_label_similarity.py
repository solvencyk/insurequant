# -*- coding: utf-8 -*-
"""a07 (read-only): how similar are the first-column row labels of two members of the same (source, caption, header) group?
Used to decide whether the "twin" test needs a row-label guard (non-twin siblings that share caption + header)."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")

from amortlib import V, eligible, iter_files  # noqa: E402

TAG_RE = re.compile(r"제\d+\((?:당|전)\)기")


def hsig(b):
    flat = V._flatten_header(b.get("header") or [])
    return TAG_RE.sub("", "|".join(re.sub(r"\s+", "", c) for c in flat))


def gkey(b):
    cap = re.sub(r"<[^<>]*>", "", re.sub(r"\s+", "", str(b.get("caption") or "")))
    return (b.get("_source_xml"), cap, hsig(b))


def labels(b):
    out = []
    for r in b.get("rows") or []:
        if r:
            s = re.sub(r"\s+", "", str(r[0]))
            if s:
                out.append(s)
    return out


def jacc(a, b):
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 1.0


old_pick = V._pick_amort_block
print("group-mates of the OLD pick (same source+caption+header), by label Jaccard with the pick:")
for company, rcept, path, blocks in iter_files():
    cands = [b for b in blocks if eligible(b)]
    pk = old_pick(cands)
    if pk is None:
        continue
    k = gkey(pk)
    mates = [(i, b) for i, b in enumerate(cands) if gkey(b) == k and b is not pk]
    if not mates:
        continue
    pl = labels(pk)
    s = []
    for i, b in mates:
        s.append((int(b.get("line_no") or 0), round(jacc(pl, labels(b)), 2), len(b.get("rows") or [])))
    flag = "" if all(j >= 0.99 for _, j, _ in s) else "   <== not identical labels"
    print(f"  {company:<16s} {rcept} pick L{pk.get('line_no')} rows{len(pk.get('rows') or [])} mates(line, jaccard, rows)={s}{flag}")
