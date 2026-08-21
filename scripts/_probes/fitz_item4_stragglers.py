"""For the still-unresolved item4 stragglers, try fitz text extraction
directly on the raw PDF (bypassing docling/MD) and print any page containing
the item4 row pattern, so a human can read off the value.
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
RAW_ROOT = REPO / "data" / "disclosure"

TARGETS = [
    ("KR0051", "FY2023_Q1"), ("KR0071", "FY2023_Q1"), ("KR0074", "FY2023_Q2"),
    ("KR0051", "FY2023_Q3"), ("KR0051", "FY2023_Q4"), ("KR0049", "FY2024_Q3"),
    ("KR0005", "FY2024_Q4"), ("KR0051", "FY2024_Q4"), ("KR0069", "FY2024_Q4"),
    ("KR0071", "FY2024_Q4"), ("KR0087", "FY2024_Q4"), ("KR0080", "FY2023_Q2"),
    ("KR0080", "FY2024_Q4"), ("KR0080", "FY2025_Q1"), ("KR0080", "FY2025_Q2"),
    ("KR0080", "FY2026_Q1"), ("KR0087", "FY2026_Q1"), ("KR1098", "FY2023_Q4"),
    ("KR0001", "FY2023_Q2"), ("KR0049", "FY2026_Q1"),
]


def main():
    for code, period in TARGETS:
        raw_dir = RAW_ROOT / period / "raw"
        if not raw_dir.is_dir():
            print(f"{code} {period}: NO RAW DIR {raw_dir}")
            continue
        matches = sorted(raw_dir.glob(f"{code}_*.pdf"))
        if not matches:
            print(f"{code} {period}: NO PDF FOUND in {raw_dir}")
            continue
        pdf_path = matches[-1]  # prefer amended (sorts after base name)
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"{code} {period}: OPEN FAILED {e}")
            continue
        found_any = False
        for i, page in enumerate(doc):
            text = page.get_text()
            if "순자산" in text and "건전성감독기준" in text and ("경과조치 적용 전" in text or "지급여력비율 세부" in text):
                found_any = True
                print(f"===== {code} {period} file={pdf_path.name} page {i+1} =====")
                # print only lines around 순자산/지급여력금액/구분 to keep it short
                lines = text.split("\n")
                for j, ln in enumerate(lines):
                    if any(k in ln for k in ("구  분", "구 분", "구분", "당분기", "해당 분기",
                                              "지급여력금액", "순자산", "보통주", "자본조정",
                                              "이익잉여금", "기타포괄", "조정준비금", "직전",
                                              "전전")):
                        print(f"  L{j}: {ln}")
        if not found_any:
            print(f"{code} {period} file={pdf_path.name}: NO MATCHING PAGE FOUND")


if __name__ == "__main__":
    main()
