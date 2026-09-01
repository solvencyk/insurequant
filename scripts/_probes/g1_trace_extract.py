# -*- coding: utf-8 -*-
"""Trace exactly what extract_kics_detail_rows returns for item23-26 rows,
for KR0009 2023.1Q, to find where item25/26 drops out of the pipeline."""
from __future__ import annotations
import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_disclosure_parser import extract_kics_detail_rows, build_label_lookups, normalise_label

md = (REPO / "md_inbox/FY2023_Q1/KR0009_현대해상.md").read_text(encoding="utf-8")
table = extract_kics_detail_rows(md, "2023.1Q")
print(f"table has {len(table)} (label, raw) pairs")
for label, raw in table:
    if "요구자본" in label or "관계회사" in label or "종속회사" in label:
        print(f"  LABEL={label!r}  RAW={raw!r}  normalised={normalise_label(label)!r}")

lookup, core = build_label_lookups(table)
print("\nnormalised keys in lookup containing '종속' or '관계':")
for k, v in lookup.items():
    if "종속" in v[0] or "관계" in v[0]:
        print(f"  key={k!r} -> label={v[0]!r} val={v[1]!r}")

canon24 = "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치"
canon25 = "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치"
canon26 = "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치"
print("\ncanonical normalised:")
print(" 24:", normalise_label(canon24))
print(" 25:", normalise_label(canon25))
print(" 26:", normalise_label(canon26))
