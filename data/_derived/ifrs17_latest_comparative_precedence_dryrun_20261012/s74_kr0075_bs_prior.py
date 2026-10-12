"""Read-only: KR0075 BNP파리바카디프생명 2023.4Q 자산총계/부채총계/자본총계 - master (FY2023 original) vs the FY2024 감사보고서's 2023-12-31 comparative column.
(registered open item 'KR0075 카디프 2023.4Q 자산·부채총계 0.08% 차이 원인'). Prints every table of the audit report that carries 자산총계 + 부채총계."""
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
from scripts.build_net_income_breakdown import to_num  # noqa: E402

M = {r["항목번호"]: r["값"] for r in json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0075" and r["공시분기"] == "2023.4Q"}
print("master 2023.4Q (백만원):", {k: M.get(k) for k in (1, 2, 3, 20, 31)})
for fy, rd in (("FY2023_Q4 (original)", next((ROOT / "data/dart/FY2023_Q4/raw").glob("KR0075_*"))), ("FY2024_Q4 (latest comparative)", next((ROOT / "data/dart/FY2024_Q4/raw").glob("KR0075_*")))):
    print("=" * 100)
    print(fy, rd.name)
    for x in sorted(rd.rglob("*.xml")):
        for t in _iter_tables_with_context(x):
            labs = [_norm(r[0]).replace(" ", "") for r in t.rows if r]
            if "자산총계" in labs and "부채총계" in labs:
                hdr = [c for r in t.header for c in r][:6]
                print("  table line", t.line_no, "caption", (t.caption or "")[:50].replace("\n", " "), "hdr", hdr)
                for r in t.rows:
                    lab = _norm(r[0]).replace(" ", "") if r else ""
                    if lab in ("자산총계", "부채총계", "자본총계"):
                        print("     ", lab, [c for c in r[1:5]])
