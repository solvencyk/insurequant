"""Read-only: print every table that carries 자산총계 + 부채총계 in the FY2023 and FY2024 annual DART filings of a company (first 4 numeric cells per row).
usage: python s99_bs_xml_peek.py KR0074 [FY2023_Q4 FY2024_Q4]"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _norm  # noqa: E402

kr = sys.argv[1]
fys = sys.argv[2:] or ["FY2023_Q4", "FY2024_Q4"]
M = {r["항목번호"]: r["값"] for r in json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8")) if r["원보험사코드"] == kr and r["공시분기"] == "2023.4Q"}
print("master 2023.4Q (백만원):", {k: M.get(k) for k in (1, 2, 3, 20, 31)})
for fy in fys:
    for rd in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*")):
        print("=" * 100)
        print(fy, rd.name)
        for x in sorted(rd.rglob("*.xml")):
            for t in _iter_tables_with_context(x):
                labs = [_norm(r[0]).replace(" ", "") for r in t.rows if r]
                if "자산총계" in labs and "부채총계" in labs:
                    hdr = [c for r in t.header for c in r][:5]
                    print(f"  {x.name} line {t.line_no} caption {(t.caption or '')[:44]!r} hdr {hdr}")
                    for r in t.rows:
                        lab = _norm(r[0]).replace(" ", "") if r else ""
                        if lab in ("자산총계", "부채총계", "자본총계"):
                            print("      ", lab, [c for c in r[1:5]])
