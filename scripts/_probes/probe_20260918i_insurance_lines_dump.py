# -*- coding: utf-8 -*-
"""Show only the tables whose ROW LABELS carry insurance-service lines
(보험수익 / 보험비용 / 보험서비스비용 / 재보험수익 / 재보험비용 / 보험손익), for one bucket.

Usage: probe_20260918i_insurance_lines_dump.py KR0069 2023.1Q
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_pl_breakdown as B  # noqa: E402
from scripts.pl_breakdown.tier1 import _is_income_statement, _header_blob  # noqa: E402
from scripts.pl_breakdown.common import _label  # noqa: E402

code, quarter = sys.argv[1], sys.argv[2]
MAXT = int(sys.argv[3]) if len(sys.argv) > 3 else 40

filings = B.discover_filings()
dirs = filings.get(code, {}).get(quarter)
if not dirs:
    print("no dirs for", code, quarter)
    sys.exit(1)

tables = []
for d in dirs:
    for x in B._xmls_in(d):
        try:
            tables.extend(B._tag_basis(
                list(B._iter_tables_by_basis(Path(x), B._iter_tables_with_context)), x))
        except Exception as e:
            print("parse fail", x, type(e).__name__, e)

ROW_RE = re.compile(r"(보험수익|보험비용|보험서비스비용|보험서비스수익|재보험수익|재보험비용"
                    r"|재보험서비스|보험손익|보험서비스결과|보험영업)")

print(f"{code} {quarter}: {len(tables)} tables")
shown = 0
for i, t in enumerate(tables):
    rows = list(getattr(t, "rows", []) or [])
    labs = [_label(r) for r in rows]
    if not any(ROW_RE.search(l or "") for l in labs):
        continue
    shown += 1
    if shown > MAXT:
        print("... (truncated)")
        break
    cap = (getattr(t, "caption", "") or "")[:160]
    print(f"\n--- [{i}] IS={_is_income_statement(t)} basis={getattr(t,'_basis',None)} ---")
    print(f"    caption: {cap}")
    print(f"    header : {_header_blob(t)[:240]}")
    for r in rows[:60]:
        lab = _label(r)
        if not lab:
            continue
        print(f"      {lab[:46]:<48} {list(r[1:7])}")
print(f"\n(shown {shown} tables)")
