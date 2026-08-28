# -*- coding: utf-8 -*-
"""Export each root master JSON to a values-only public CSV for the site's
설문 게이트 다운로드 (survey-gated download) feature on index.html.

Reads the SAME 8 masters `build_master_xlsx.py` bundles (mirror this list if that
one changes) directly from JSON — never touches insurequant_master_tables.xlsx,
so there is no risk of wiping its formula cache (project rule: never openpyxl
load+save the master xlsx).

Output: public_exports/<sheet_name>.csv (UTF-8 BOM, for Windows Excel).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "public_exports"

# (json file, sheet name) — mirrors build_master_xlsx.py MASTERS (그 리스트가
# 바뀌면 이것도 같이 바꿀 것). "요약" 시트는 실데이터가 아니라 제외.
MASTERS = [
    ("IFRS17_BS.json", "17BS"),
    ("kics_disclosure.json", "K-ICS공시"),
    ("kics_rate_sensitivity.json", "금리민감도"),
    ("CSM_waterfall.json", "CSM워터폴"),
    ("CSM_amortization.json", "CSM상각"),
    ("NB_CSM_multiple.json", "신계약CSM배수"),
    ("PL_breakdown.json", "손익분해PL"),
    ("dividend.json", "배당"),
]


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for json_name, sheet_name in MASTERS:
        rows = json.loads((REPO / json_name).read_text(encoding="utf-8"))
        if not rows:
            print(f"  SKIP {json_name}: empty")
            continue
        fieldnames = list(rows[0].keys())
        out_path = OUT_DIR / f"{sheet_name}.csv"
        with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        print(f"  wrote {out_path.relative_to(REPO)}: {len(rows)} rows x {len(fieldnames)} cols")


if __name__ == "__main__":
    main()
