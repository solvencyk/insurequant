# -*- coding: utf-8 -*-
"""a02 (read-only): print what sits right above every eligible amortisation table of the given companies' newest filing(s)
(the 12 non-blank lines above the <TABLE, plus the first table rows) so the 당기/전기 marker layout can be read by eye.
Usage: a02_context_dump.py <company> [<company> ...]  [--rcept YYYY...]  [--above N]"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")
from rawroles import raw_lines_for  # noqa: E402

args = sys.argv[1:]
above = 12
rcepts = set()
names = []
i = 0
while i < len(args):
    if args[i] == "--above":
        above = int(args[i + 1]); i += 2
    elif args[i] == "--rcept":
        rcepts.add(args[i + 1]); i += 2
    else:
        names.append(args[i]); i += 1

census = json.loads((W / "a01_old_pick_census.json").read_text(encoding="utf-8"))
for r in census:
    if r["company"] not in names:
        continue
    if rcepts and r["rcept"] not in rcepts:
        continue
    if not rcepts and not r["rcept"].startswith("2026"):
        continue
    print("=" * 100)
    print(r["company"], r["rcept"], "old pick line", r["old_pick_line"], r["old_pick_src"])
    for c in r["cands"]:
        lines = raw_lines_for(r["rcept"], c["src"])
        print("-" * 80)
        print(f"cand line {c['line_no']} {c['src']} rows={c['n_rows']} bcols={c['bucket_cols']} role={c['role']} {'<== OLD PICK' if c['is_old_pick'] else ''}")
        if lines is None:
            print("   (raw not on disk)")
            continue
        ln = int(c["line_no"])
        shown = []
        j = ln - 2
        while j >= 0 and len(shown) < above:
            s = lines[j].strip()
            if s:
                shown.append((j + 1, re.sub(r"\s+", " ", s)[:150]))
            j -= 1
        for n, s in reversed(shown):
            print(f"   {n}: {s}")
        # first few cells of the table
        k, cells = ln, []
        while k < min(len(lines), ln + 60) and len(cells) < 8:
            m = re.search(r"<T[DH]\b[^>]*>(.*?)</T[DH]>", lines[k], re.S)
            if m:
                cells.append(re.sub(r"\s+", " ", m.group(1))[:30])
            k += 1
        print("   first cells:", cells)
