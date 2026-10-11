#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17): dump one table of a DART body XML (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_xml_table.py <xml path> <line_no> [--max N]

`line_no` is the `.line_no` the table iterator reports (see scripts/bspl_followup_kr1000_probe.py).  Prints caption, header and every row.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402


def main():
    xml = Path(sys.argv[1])
    line_no = int(sys.argv[2])
    mx = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--max" else 200
    for t in _iter_tables_with_context(xml):
        if t.line_no != line_no:
            continue
        print(f"line {t.line_no} rows {len(t.rows)} caption: {(t.caption or '')[:200]!r}")
        print("header:", t.header)
        for i, r in enumerate(t.rows[:mx]):
            print(i, [str(c) for c in r])
        return
    print("table not found at line", line_no)


if __name__ == "__main__":
    main()
