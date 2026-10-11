#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 3c helper: run the production Tier-2 PL handler on one DART filing and show the rows that
carry a keyword, so a Tier-2 note item (e.g. 재보험 위험조정 변동, item 10) can be compared with the printed cells.  Read-only.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_note_probe.py KR0072 2024.1Q [keyword] [--items 5,10]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown import companies as C  # noqa: E402


def main():
    code, q = sys.argv[1], sys.argv[2]
    kw = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "위험조정"
    fy = f"FY{q[:4]}_Q{q[5]}"
    dirs = sorted((ROOT / "data" / "dart" / fy / "raw").glob(f"{code}_*"))
    xml = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)[0]
    tables = list(_iter_tables_with_context(xml))
    h = C.LIFE_HANDLERS.get(code) or C.SONBO_HANDLERS.get(code)
    out = h(tables)
    print("XML", xml.name, "handler", h.__name__, "tables", len(tables))
    print({k: v for k, v in sorted(out.items(), key=lambda kv: str(kv[0])) if not str(k).startswith("_")})
    n = 0
    for i, t in enumerate(tables):
        hdr = " ".join(str(c) for r in (t.header or []) for c in r)[:140]
        for r in t.rows:
            if r and kw in "".join(str(c) for c in r[:3]):
                print(f"[t{i} line {t.line_no}] hdr='{hdr}' row={[str(c)[:26] for c in r[:9]]}")
                n += 1
                if n >= 40:
                    return


if __name__ == "__main__":
    main()
