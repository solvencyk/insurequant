#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 2: where do KR1000 (코리안리) 2023.1Q / 2023.2Q BS values come from?

Read-only probe.  For a DART body XML (data/dart/FY####_Q#/raw/KR1000_*/xml/*.xml):
  * runs the production body-XML BS reader (`build_equity_composition_tier2.parse_filing`) and prints what it returns,
  * lists every table that has a 자산총계 row with its caption, basis marker, unit, header and the first numeric columns,
    so the column meaning (당기말 / 전기말) can be read directly.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_kr1000_probe.py <FYdir> [code]
  e.g. ... scripts/bspl_followup_kr1000_probe.py FY2023_Q1 KR1000
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from scripts import build_equity_composition_tier2 as T  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402


def main():
    fy = sys.argv[1]
    code = sys.argv[2] if len(sys.argv) > 2 else "KR1000"
    dirs = sorted((ROOT / "data" / "dart" / fy / "raw").glob(f"{code}_*"))
    xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
    xml = xmls[0]
    print("XML", xml, xml.stat().st_size)
    vals, diag = T.parse_filing(xml)
    print("parse_filing diag:", diag)
    keep = {k: v for k, v in vals.items() if k in (40, 41, 1, 6) or k >= 200}
    for k in sorted(keep):
        print(f"  key {k}: {keep[k]:,.6f}")
    raw_lines = xml.read_text(encoding="utf-8", errors="replace").split("\n")
    markers = T._unit_markers_by_line(raw_lines)
    bmarks = T._bs_basis_markers(raw_lines)
    tables = list(_iter_tables_with_context(xml))
    print("tables", len(tables))
    for t in tables:
        labs = [T._bs_label(r[0]) for r in t.rows if r and r[0]]
        if "자산총계" not in labs:
            continue
        scale = T._find_unit(markers, t.line_no)
        basis = T._find_basis(bmarks, t.line_no)
        print("-" * 100)
        print(f"line {t.line_no} rows {len(t.rows)} scale {scale} basis_marker {basis} caption: {(t.caption or '')[:120]!r}")
        print("header:", t.header)
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = T._bs_label(r[0])
            if lab in ("자산총계", "부채총계", "자본총계", "자본금", "이익잉여금", "기타포괄손익누계액", "보험계약부채",
                       "재보험계약부채", "현금및현금성자산", "기타부채", "유형자산", "자산", "부채", "자본"):
                print("   ", [str(c)[:22] for c in r[:6]])


if __name__ == "__main__":
    main()
