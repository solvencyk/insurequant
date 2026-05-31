# -*- coding: utf-8 -*-
"""Smoke test for canonical DART path helpers — verifies new paths land on
the existing Reorg #2 leaves so future fetches don't drift."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
REPO = Path(__file__).resolve().parents[1]

from scripts._dart_path_helpers import annual_raw_dir, quarterly_raw_dir  # noqa


CASES = [
    ("annual",
     dict(canonical_name="메리츠화재해상보험", rcept_no="20250331003145",
          kics_name="메리츠화재해상보험"),
     "data/dart/FY2024_Q4/raw/KR0001_메리츠화재해상보험_20250331003145"),
    ("annual",
     dict(canonical_name="삼성생명", rcept_no="20250312001063",
          kics_name="삼성생명보험"),
     "data/dart/FY2024_Q4/raw/KR0069_삼성생명_20250312001063"),
    ("annual",
     dict(canonical_name="IBK연금보험", rcept_no="20250328000503",
          kics_name="IBK연금보험"),
     "data/dart/FY2024_Q4/raw/KR1011_IBK연금보험_20250328000503"),
    ("annual",
     dict(canonical_name="케이비라이프생명보험", rcept_no="20250314000905",
          kics_name="KB라이프생명"),
     "data/dart/FY2024_Q4/raw/KR0099_케이비라이프생명보험_20250314000905"),
    ("annual",
     dict(canonical_name="코리안리", rcept_no="20250320001161",
          kics_name="코리안리재보험"),
     "data/dart/FY2024_Q4/raw/KR1000_코리안리_20250320001161"),
    ("annual",
     dict(canonical_name="에이아이에이생명보험", rcept_no="20250401000094",
          kics_name="에이아이에이생명보험"),
     "data/dart/FY2024_Q4/raw/KR0080_에이아이에이생명보험_20250401000094"),
    ("quarterly",
     dict(canonical_name="메리츠화재해상보험", period_label="2023.1Q",
          kr_code="KR0001"),
     "data/dart/FY2023_Q1/raw/KR0001_메리츠화재해상보험"),
    ("quarterly",
     dict(canonical_name="삼성생명", period_label="2025.2Q", kr_code="KR0069"),
     "data/dart/FY2025_Q2/raw/KR0069_삼성생명"),
    ("annual_group",
     dict(canonical_name="하나금융지주", rcept_no="20250324000400",
          corp_code="00547583"),
     "data/dart/FY2024_Q4/raw/00547583_하나금융지주_20250324000400"),
]


def main() -> int:
    ok = fail = 0
    for kind, kw, expected in CASES:
        fn = annual_raw_dir if kind.startswith("annual") else quarterly_raw_dir
        actual = fn(**kw).relative_to(REPO).as_posix()
        match = actual == expected
        flag = "OK  " if match else "FAIL"
        print(f"  [{flag}] {kind:14s} -> {actual}")
        if not match:
            print(f"            expected: {expected}")
            fail += 1
        else:
            ok += 1
    print(f"\n{ok}/{ok+fail} passed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
