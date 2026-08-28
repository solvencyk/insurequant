"""Does the same 'second (OFS) copy of note 18-1 has row-label/value shift' defect recur in
KR0079's OTHER annual (사업보고서) filings -- FY2023_Q4 and FY2024_Q4 -- or is it unique to
the FY2025_Q4 submission? Read-only, single-pass parse (no split needed, mirrors the
2025.4Q root-cause probe).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

DIRS = {
    "2023.4Q": ROOT / "data/dart/FY2023_Q4/raw/KR0079_미래에셋생명_20240320002014",
    "2024.4Q": ROOT / "data/dart/FY2024_Q4/raw/KR0079_미래에셋생명_20250318001228",
}

for label, D in DIRS.items():
    main_xml = sorted(D.glob("*.xml"), key=lambda p: p.stat().st_size, reverse=True)[0]
    print(f"\n{'='*100}\n{label}: {main_xml.name} ({main_xml.stat().st_size:,} bytes, "
          f"{sum(1 for _ in open(main_xml, encoding='utf-8', errors='replace')):,} lines)")
    tables = list(_iter_tables_with_context(main_xml))
    cands = [t for t in tables
             if "자산인 보험계약의 기초 장부금액" in "".join(r[0] if r else "" for r in t.rows)
             and any("발생한 보험금 및 기타 보험서비스비용" in "".join(r[:2]) for r in t.rows)
             and len(t.rows) >= 15]
    print(f"  candidate tables (15-col shape, both anchor labels): {len(cands)}")
    for i, t in enumerate(cands):
        # find the specific two rows and print their raw values (first 3 numeric cells only,
        # to keep this compact)
        row_rev = next((r for r in t.rows if (r[0] if r else "") == "보험수익"), None)
        row_svc_parent = next((r for r in t.rows if (r[0] if r else "") == "보험서비스비용" and len(r) <= 2), None)
        row_act = next((r for r in t.rows if "발생한 보험금 및 기타 보험서비스비용" in "".join(r[:2])), None)
        row_asset_open = next((r for r in t.rows if (r[0] if r else "") == "자산인 보험계약의 기초 장부금액"), None)
        print(f"  cand#{i} line={t.line_no}: "
              f"자산기초={'BLANK' if not row_asset_open or not any(c.strip() for c in row_asset_open[1:]) else row_asset_open[1]}  "
              f"보험수익={'BLANK' if not row_rev or not any(c.strip() for c in row_rev[1:]) else row_rev[1]}  "
              f"발생한보험금[0:3]={row_act[2:5] if row_act else None}")
