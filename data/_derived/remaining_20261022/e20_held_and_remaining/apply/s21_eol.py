#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 21 (read-only): byte-level newline convention of the files this round edits."""
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
FILES = ["TODO_parser_ifrs17.md", "docs/changelog_parser_ifrs17.md", "docs/todo_archive_parser_ifrs17.md",
         "inbox/parser/20261022T1800Z__orchestrator__MULTI_2023.1Q-2025.2Q__latest_comparative_held_and_remaining.md",
         "PL_breakdown.json", "PL_breakdown_provenance.json", "data/_gold/user_pl_cells.json", "data/_gold/gold_overlay_ledger.json",
         "tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json"]
for f in FILES:
    b = (ROOT / f).read_bytes()
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n")
    cr = b.count(b"\r")
    print(f"{f}: bytes={len(b)} CRLF={crlf} bareLF={lf - crlf} bareCR={cr - crlf} BOM={b.startswith(b'\xef\xbb\xbf')} endsWithNL={b.endswith(b'\n')}")
