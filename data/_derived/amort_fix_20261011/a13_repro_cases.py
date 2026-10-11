# -*- coding: utf-8 -*-
"""a13 (read-only): cause reproduction straight from the raw DART XML (independent of the extractor) for chosen companies:
the two candidate tables, what introduces each (caption paragraph / bare marker paragraph / unit mini-table / fiscal-year heading),
its line_no, the 합계 row's first and last numbers, and which one the OLD and the NEW picker choose.
Usage: a13_repro_cases.py <company> ...      (FY2025 filing = newest rcept, the one that feeds the panel)"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
sys.stdout.reconfigure(encoding="utf-8")

from amortlib import V  # noqa: E402
from rawroles import far_role, raw_lines_for, raw_role  # noqa: E402

TD = re.compile(r"<TD\b[^>]*>(.*?)</TD>", re.S)


def table_rows(lines, start):
    """text cells of every row of the <TABLE starting at 1-based line `start`"""
    i, depth, rows, cur = start - 1, 0, [], None
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("<TABLE"):
            depth += 1
        elif s.startswith("</TABLE"):
            depth -= 1
            if depth == 0:
                break
        elif s.startswith("<TR"):
            cur = []
        elif s.startswith("</TR"):
            if cur is not None:
                rows.append(cur)
            cur = None
        else:
            m = TD.search(lines[i])
            if m and cur is not None:
                cur.append(re.sub(r"\s+", " ", re.sub(r"<[^<>]*>", "", m.group(1))).strip())
        i += 1
    return rows


before = json.loads((W / "a08_selection_before.json").read_text(encoding="utf-8"))
after = json.loads((W / "a08_selection_after.json").read_text(encoding="utf-8"))
for co in sys.argv[1:]:
    files = sorted((k for k, v in after.items() if v["company"] == co), key=lambda k: after[k]["rcept"])
    fn = files[-1]
    rec_b, rec_a = before[fn], after[fn]
    rc = rec_a["rcept"]
    print("=" * 110)
    print(f"{co}  rcept {rc}  extracted {fn}")
    print(f"  OLD picker -> {rec_b['pick_src']} line {rec_b['pick_line']}   NEW picker -> {rec_a['pick_src']} line {rec_a['pick_line']}")
    blocks = json.loads((V.SRC / fn).read_text(encoding="utf-8"))
    from amortlib import eligible  # noqa: E402
    cands = [b for b in blocks if eligible(b) and b.get("_source_xml") == rec_a["pick_src"]]
    twins = [b for b in cands if V._twin_shape(b) == V._twin_shape(next(x for x in cands if x.get("line_no") == rec_a["pick_line"]))]
    for b in sorted(twins, key=lambda b: b["line_no"]):
        lines = raw_lines_for(rc, b["_source_xml"])
        role, pl, ptxt = raw_role(lines, b["line_no"])
        frole, fdist, ftxt = far_role(lines, b["line_no"])
        rows = table_rows(lines, b["line_no"])
        tot = next((r for r in rows if r and re.sub(r"\s", "", r[0]) in ("합계", "계") or (len(r) > 1 and re.sub(r"\s", "", r[1]) in ("합계", "계"))), None)
        print(f"  TABLE line {b['line_no']:>6}  caption(extracted)={str(b.get('caption'))[:70]!r}")
        print(f"      introduced by (line {pl}): {ptxt!r}  => role {role}" + ("" if role else f"   | nearest marker above: {ftxt!r} (@{fdist} lines) => {frole}"))
        print(f"      합계 row (first 3 + last cell): {tot[:3] + ['...'] + tot[-1:] if tot else None}")
        print(f"      <== OLD pick" if b["line_no"] == rec_b["pick_line"] else "", "<== NEW pick" if b["line_no"] == rec_a["pick_line"] else "")
