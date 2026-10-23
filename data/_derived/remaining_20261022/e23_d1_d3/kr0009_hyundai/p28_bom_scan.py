# -*- coding: utf-8 -*-
"""Read-only: no UTF-8 BOM and valid UTF-8 / Python syntax in every file this load created (evidence folder + answer draft) and in the repo files it changed; reports non-UTF-8 console captures."""
import ast
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
base = ROOT / "data/_derived/remaining_20261022/e23_d1_d3"
files = sorted(p for p in (base / "kr0009_hyundai").rglob("*") if p.is_file()) + [base / "answers/kr0009_hyundai.md"]
files += [ROOT / r for r in ("tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json",
                              "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json", "PL_breakdown.json", "CSM_waterfall.json", "PL_breakdown_provenance.json",
                              "CSM_waterfall_provenance.json", "data/_derived/qoq_warn.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json")]
bad = 0
n = 0
nonutf = []
for f in files:
    if not f.is_file():
        continue
    b = f.read_bytes()
    n += 1
    if b[:3] == b"\xef\xbb\xbf":
        print("BOM:", f)
        bad += 1
    try:
        t = b.decode("utf-8")
    except UnicodeDecodeError as e:
        print("NOT UTF-8:", f, e)
        nonutf.append(f)
        bad += 1
        continue
    if f.suffix == ".py":
        try:
            ast.parse(t)
        except SyntaxError as e:
            print("SYNTAX:", f.name, e)
            bad += 1
    if "\x08" in t:
        print("BACKSPACE char:", f.name)
        bad += 1
print(f"scanned {n} files, problems {bad}")
