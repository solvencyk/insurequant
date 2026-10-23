# -*- coding: utf-8 -*-
"""read-only: extract of the IR factsheet cells the load relies on (the raw xlsx are gitignored like the DART raw files, so the values are recorded here): sheet '(3) UW Income', rows 4-6 headers and the 보 험 손 익 rows of
the 일반 / 장기 / 자동차 blocks and the 합계 row, columns K (3-month) and L (cumulative) of the FY2024 Q1..Q4 factsheets.  Own zipfile+XML reader (hd_lib), no openpyxl."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hd_lib as H  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
IR = {
    "2023.1Q": "data/ir/FY2024_Q1/raw/KR0009_현대해상/dd7e547e6e1f9cc171b77dcb4bf67d58.xlsx",
    "2023.2Q": "data/ir/FY2024_Q2/raw/KR0009_현대해상/d33c3d385303361798f75607750ca360.xlsx",
    "2023.3Q": "data/ir/FY2024_Q3/raw/KR0009_현대해상/7a517f00b391c158b282d1412c609776.xlsx",
    "2023.4Q": "data/ir/FY2024_Q4/raw/KR0009_현대해상/2a11f147695dacd4665923059eceed11.xlsx",
}
ROWS = {"일반": 11, "장기": 26, "자동차": 30, "합계": 31}
out = {}
for q, rel in IR.items():
    S = H.read_xlsx_sheet(rel, "(3) UW Income")
    out[q] = dict(file=rel, sheet="(3) UW Income", unit_L4=S.get("L4"), header_K6=S.get("K6"), header_L6=S.get("L6"),
                  block_labels={r: S.get(f"B{r}") for r in (8, 12, 27, 31)},
                  rows={name: dict(label=S.get(f"C{r}") if name != "합계" else S.get(f"B{r}"), K_3m=S.get(f"K{r}"), L_cum=S.get(f"L{r}"), K_cell=f"K{r}", L_cell=f"L{r}") for name, r in ROWS.items()},
                  legs_sum_L=sum(S[f"L{r}"] for r in (11, 26, 30)))
    print(q, "L6", repr(S.get("L6")), "legs sum", out[q]["legs_sum_L"], "L31", S.get("L31"))
(Path(__file__).resolve().parent / "ir_legs_extract.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
