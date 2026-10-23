# -*- coding: utf-8 -*-
"""read-only: line-ending convention (CRLF / LF counts), trailing bytes and BOM of every repo file the load changed: pre-load backup vs final"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0009_hyundai"
FILES = ["PL_breakdown.json", "CSM_waterfall.json", "PL_breakdown_provenance.json", "CSM_waterfall_provenance.json", "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json",
         "tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json", "data/_derived/qoq_warn.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json"]
ok = True
for rel in FILES:
    a, b = (BK / rel).read_bytes(), (ROOT / rel).read_bytes()
    ca, cb = a.count(b"\r\n"), b.count(b"\r\n")
    la, lb = a.count(b"\n"), b.count(b"\n")
    same_conv = (ca == 0) == (cb == 0) and (ca == la) == (cb == lb)
    ok = ok and same_conv and b[:3] != b"\xef\xbb\xbf" and a[-2:] == b[-2:]
    print(f"{rel}: CRLF {ca}/{la} -> {cb}/{lb}; BOM after {b[:3] == b'\\xef\\xbb\\xbf'}; ending {a[-2:]!r} -> {b[-2:]!r}; convention {'kept' if same_conv else 'CHANGED'}")
print("ALL CONVENTIONS KEPT" if ok else "CHECK")
