# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_disclosure_parser import extract_kics_detail_rows, build_label_lookups
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero, _label_matches

cands = sorted((REPO / "md_inbox" / "FY2024_Q4").glob("KR0051_*.md"))
print("file:", cands)
md = cands[0].read_text(encoding="utf-8")
table = extract_kics_detail_rows(md, "2024.4Q")
print(f"table len={len(table)}")
for label, raw in table:
    if "비례성" in label or "종속" in label or "관계" in label or "기타 요구자본" in label or "기타요구자본" in label:
        print("  ROW:", repr(label), "=", repr(raw))

canon = {23: "Ⅲ. 기타 요구자본(1+2+3)",
         24: "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치",
         25: "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치",
         26: "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치"}
lookup, core = build_label_lookups(table)
for it in (23, 24, 25, 26):
    v = match_baseline_value_or_zero(canon[it], lookup, core, table)
    print(f"  item{it} match = {v!r}")
