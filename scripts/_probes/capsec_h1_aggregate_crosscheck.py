# -*- coding: utf-8 -*-
"""For the companies that filed H1 2026 but lack the itemized "자본으로 인정되는 채무증권"
section, cross-check FY2025's hybrid total against the universal "신종자본증권 미상환 잔액"
maturity-bucket table's 합계/총계 (grand total), as_of 작성기준일(BASE_DT)=20260630.
This does NOT give per-bond detail, only a total — used to flag material drift, not to
replace fy2025 bond-level detail.
"""
import io, json, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "dart" / "FY2026_Q2" / "raw"
fy25 = json.loads((ROOT / "data" / "bonds" / "capital_securities_fy2025.json").read_text(encoding="utf-8"))
FY25_BY_CODE = {c["code"]: c for c in fy25["companies"]}
census = json.loads((ROOT / "data" / "_derived" / "_probe_capsec_h1_census.json").read_text(encoding="utf-8"))
NO_DETAIL_CODES = ["KR0001", "KR0002", "KR0003", "KR0005", "KR0009", "KR0010",
                    "KR0073", "KR0079", "KR0082", "KR0083", "KR0087", "KR1000"]

for code in NO_DETAIL_CODES:
    d = next((p for p in RAW_DIR.iterdir() if p.name.startswith(code + "_")), None)
    xml = next(d.glob("*.xml"), None) if d else None
    if xml is None:
        print(f"{code}: no xml")
        continue
    text = xml.read_text(encoding="utf-8", errors="replace")
    idx = text.find("신종자본증권 미상환 잔액")
    if idx == -1:
        print(f"{code}: title not found")
        continue
    window = text[idx:idx + 6000]
    base_dt_m = re.search(r'AUNIT="BASE_DT" AUNITVALUE="(\d{8})"', window)
    base_dt = base_dt_m.group(1) if base_dt_m else None
    # grand total row: TD "합계" then a row of TE ACODE=..._DATT cells; take the LAST one (total column)
    total_row_m = re.search(r"<TD[^>]*>\s*합계\s*</TD>((?:\s*<TE[^>]*>[^<]*</TE>)+)", window, re.DOTALL)
    total_val = None
    if total_row_m:
        cells = re.findall(r"<TE[^>]*>([^<]*)</TE>", total_row_m.group(1))
        if cells:
            raw = cells[-1].replace(",", "").strip()
            if raw not in ("-", "", "－"):
                try:
                    total_val = int(raw)
                except ValueError:
                    total_val = None
    fy = FY25_BY_CODE.get(code, {})
    fy_hyb_sum = sum(b["outstanding_mn"] for b in fy.get("bonds", []) if b["tier"] == "hybrid")
    match = "MATCH" if (total_val is not None and abs(total_val - fy_hyb_sum) <= max(5000, fy_hyb_sum * 0.02)) else "DIFF"
    print(f"{code}  base_dt={base_dt}  h1_aggregate_total_mn={total_val}  fy25_hybrid_sum_mn={fy_hyb_sum}  {match}")
