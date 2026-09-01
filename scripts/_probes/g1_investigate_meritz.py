# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_disclosure_parser import extract_kics_detail_rows, build_label_lookups
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero, _label_matches

for tq, period in [("2023.2Q", "FY2023_Q2"), ("2024.4Q", "FY2024_Q4"), ("2025.1Q", "FY2025_Q1")]:
    cands = sorted((REPO / "md_inbox" / period).glob("KR0001_*.md"))
    md_path = cands[0]
    md = md_path.read_text(encoding="utf-8")
    table = extract_kics_detail_rows(md, tq)
    print(f"=== {tq}: table len={len(table)} ===")
    for label, raw in table:
        if "비례성" in label or "요구자본" in label.replace(" ", ""):
            print("  ROW:", repr(label), "=", repr(raw))
    canon25 = "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치"
    lookup, core = build_label_lookups(table)
    v = match_baseline_value_or_zero(canon25, lookup, core, table)
    print("  matched value:", v)
    for label, raw in table:
        if _label_matches(canon25, label):
            print("  MATCH-CANDIDATE:", repr(label), "=", repr(raw))
