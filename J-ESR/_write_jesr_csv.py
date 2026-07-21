"""Write J-ESR/jesr_sources_2026Q1.csv from raw JSON."""
import csv, json
from pathlib import Path

RAW = Path(__file__).parent / "raw" / "jesr_sources_raw.json"
OUT = Path(__file__).parent / "jesr_sources_2026Q1.csv"

data = json.loads(RAW.read_text(encoding="utf-8"))

COLS = [
    "company_jp", "company_en", "ticker", "group_or_solo",
    "esr_pct", "esr_basis", "as_of",
    "所要資本_bn_jpy", "適格資本_bn_jpy", "総資産_tn_jpy",
    "target_pct", "yoy_change_pp",
    "source_url", "doc_type", "doc_date", "notes",
]

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
    w.writeheader()
    for row in data:
        # Format nulls as empty string
        out_row = {k: ("" if row.get(k) is None else row[k]) for k in COLS}
        w.writerow(out_row)

print(f"Written: {OUT} ({len(data)} rows)")
