#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17): find / dump tables of the DART body XML of one (company code, quarter) (read-only).

  ... bspl_apply_xmltable.py KR0072 2023.2Q --files                       list the XML files
  ... bspl_apply_xmltable.py KR0072 2023.2Q --find 키워드1 키워드2 [--rows 20] [--file N]   tables whose text contains ALL keywords
  ... bspl_apply_xmltable.py KR0072 2023.2Q --line 21320 [--rows 80] [--file N]            dump the table at a line number
`--file N` selects the N-th XML (default: all).  Tables are iterated with src.ifrs17.csm_extractor._iter_tables_with_context.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402


def xml_files(code: str, quarter: str):
    y, q = quarter.split(".")
    base = ROOT / "data" / "dart" / f"FY{y}_Q{q[0]}" / "raw"
    out = []
    for d in sorted(base.glob(f"{code}_*")):
        out += sorted(p for p in d.rglob("*.xml"))
    return out


def main():
    a = sys.argv[1:]
    code, quarter = a[0], a[1]
    rows_n = int(a[a.index("--rows") + 1]) if "--rows" in a else 30
    sel = int(a[a.index("--file") + 1]) if "--file" in a else None
    files = xml_files(code, quarter)
    if "--files" in a or not files:
        for i, f in enumerate(files):
            print(i, f.relative_to(ROOT), f.stat().st_size)
        return
    if sel is not None:
        files = [files[sel]]
    kws = []
    if "--find" in a:
        i = a.index("--find") + 1
        while i < len(a) and not a[i].startswith("--"):
            kws.append(a[i])
            i += 1
    line = int(a[a.index("--line") + 1]) if "--line" in a else None
    for f in files:
        print(f"##### {f.relative_to(ROOT)}")
        for t in _iter_tables_with_context(f):
            if line is not None:
                if t.line_no != line:
                    continue
            elif kws:
                txt = " ".join(str(c) for r in t.rows for c in r) + " " + " ".join(str(h) for h in (t.header or []))
                if not all(k in txt for k in kws):
                    continue
            else:
                continue
            print(f"--- line {t.line_no} rows {len(t.rows)} caption: {(t.caption or '')[:140]!r}")
            print("header:", t.header)
            for i, r in enumerate(t.rows[:rows_n]):
                print(i, [str(c)[:30] for c in r])


if __name__ == "__main__":
    main()
