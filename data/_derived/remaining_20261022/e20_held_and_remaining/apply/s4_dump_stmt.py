#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 4: dump the SEPARATE-basis '4-2. 포괄손익계산서' of the needed filings (label + every cell with line / short context) -> s4_stmt_<code>_<fy>.txt (read-only)
usage: s4_dump_stmt.py CODE FY [FY ...]"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_xml as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
code = sys.argv[1]
for fy in sys.argv[2:]:
    path = X.main_xml(code, fy)
    lines = X.load_lines(path)
    out = [f"# {code} {fy} {X.rel(path)} ({len(lines)} lines)"]
    ts = X.find_titles(lines, r"4-2\. 포괄손익계산서")
    if ts:
        s, e, rows = X.read_statement_at(lines, ts[0])
        out.append(f"# ATOC xml, title line {s}, end {e}, rows {len(rows)}")
        for r in rows:
            lab = r["label"][0] if r["label"] else ""
            cs = " | ".join(f"{c['text']}@{c['line']}:{X.short_ctx(c['ctx'])}" for c in r["cells"])
            out.append(f"R{r['tr_line']} [{lab}] {cs}")
    else:
        s, e = X.html_marker_range(lines, r"4-2\. 포괄손익계산서")
        if s is None:
            out.append("# no '4-2. 포괄손익계산서' title or marker found")
        else:
            rows = X.read_html_rows(lines, s, e)
            out.append(f"# HTML, marker line {s}, end {e}, rows {len(rows)}")
            for r in rows:
                if not r["cells"]:
                    continue
                lab = r["cells"][0]["text"]
                cs = " | ".join(f"{c['text']}@{c['line']}" for c in r["cells"][1:])
                out.append(f"R{r['tr_line']} [{lab}] {cs}")
    (HERE / f"s4_stmt_{code}_{fy}.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(code, fy, len(out))
