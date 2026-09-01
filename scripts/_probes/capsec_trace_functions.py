# -*- coding: utf-8 -*-
"""Import the real builder module and call its extraction primitives directly against a
company's H1 raw XML, to see exactly what each function returns (not guesswork from text greps)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_capital_securities_fy2026h1 as B  # noqa: E402  (this import wraps sys.stdout to utf-8 itself)

codes = sys.argv[1:]
for code in codes:
    print(f"===== {code} =====")
    xml_path, text = B.load_h1_xml(code)
    if text is None:
        print("  NO XML")
        continue
    print(f"  file={xml_path}")

    rows = B._issuance_rows(text)
    print(f"  _issuance_rows: n={len(rows)}")
    for r in rows:
        print(f"    {r}")
    as_of = B._issuance_as_of(text)
    print(f"  _issuance_as_of: {as_of}")

    mgr_rows = B._bond_manager_rows(text)
    print(f"  _bond_manager_rows: n={len(mgr_rows)}")
    for r in mgr_rows:
        print(f"    {r}")
    mgr_as_of = B._bond_manager_as_of(text)
    print(f"  _bond_manager_as_of: {mgr_as_of}")

    detail_rows = B.extract_subordinated_detail(text)
    print(f"  extract_subordinated_detail: n={len(detail_rows)}")
    for r in detail_rows:
        print(f"    {r}")

    names, cur_rows = B.extract_subordinated_current(text, "current")
    print(f"  extract_subordinated_current(current): names={names} rows_keys={list(cur_rows.keys()) if cur_rows else None}")
    print()
