"""Read-only landscape scan across ALL KR0079 (미래에셋생명) raw filings on disk.

Purpose: for ticket inbox/parser/20260828T2300Z, determine which quarters use the NEW
XBRL-structured "18-1" note format (confirmed extractable, 2026.2Q survey) vs the OLD
"22.6 보험손익의 변동내역" prose/individual-table format (confirmed NOT extractable for
item6/11, 2023.2Q per prior investigation). Does not touch any master JSON.

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/mirae_yesilcha_quarter_scan.py
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

FILES = [
    ("2023.1Q", "data/dart/FY2023_Q1/raw/KR0079_미래에셋생명"),  # zip only, expect skip
    ("2023.2Q", "data/dart/FY2023_Q2/raw/KR0079_미래에셋생명/20230814003137.xml"),
    ("2023.3Q", "data/dart/FY2023_Q3/raw/KR0079_미래에셋생명/20231114002863.xml"),
    ("2023.4Q", "data/dart/FY2023_Q4/raw/KR0079_미래에셋생명_20240320002014/20240320002014.xml"),
    ("2024.1Q", "data/dart/FY2024_Q1/raw/KR0079_미래에셋생명/20240516001903.xml"),
    ("2024.2Q", "data/dart/FY2024_Q2/raw/KR0079_미래에셋생명/20240814004148.xml"),
    ("2024.3Q", "data/dart/FY2024_Q3/raw/KR0079_미래에셋생명/20241114002301.xml"),
    ("2024.4Q", "data/dart/FY2024_Q4/raw/KR0079_미래에셋생명_20250318001228/20250318001228.xml"),
    ("2025.1Q", "data/dart/FY2025_Q1/raw/KR0079_미래에셋생명/20250515001717.xml"),
    ("2025.2Q", "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명"),  # zip only, expect skip
    ("2025.3Q", "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명"),  # zip only, expect skip
    ("2025.4Q", "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664/20260318001664.xml"),
    ("2026.1Q", "data/dart/FY2026_Q1/raw/KR0079_미래에셋생명/20260529001897.xml"),
    ("2026.2Q", "data/dart/FY2026_Q2/raw/KR0079_미래에셋생명/20260814004054.xml"),
]

MARKERS = [
    ("new_18-1_note_comment", r"18-1\. 보험계약부채"),
    ("new_exp_label_direct", r"발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가"),
    ("new_act_label_direct", r"발생한 보험금 및 기타 보험서비스비용"),
    ("new_loss_alloc_label", r"손실요소배분액"),
    ("new_exp_label_re", r"발생한 보험금 및 그 밖의 발생한 재보험수익에 따른 증가분"),
    ("old_caption_22.6", r"22\.6\s*보험손익의 변동내역"),
    ("old_caption_generic", r"보험손익의 변동내역"),
    ("unit_won", r"\(단위\s*:\s*원\)"),
    ("unit_baekman", r"\(단위\s*:\s*백만원\)"),
    ("label_당반기", r"당반기"),
    ("label_당분기", r"당분기"),
    ("label_당기", r"당기(?!말)"),
    ("tier1_general_ins_rev", r"일반보험서비스수익"),
]


def main():
    print(f"{'quarter':8s} " + " ".join(f"{name:22s}" for name, _ in MARKERS))
    for qtr, relpath in FILES:
        p = ROOT / relpath
        if p.is_dir():
            xmls = list(p.glob("*.xml"))
            if not xmls:
                print(f"{qtr:8s}  [no .xml on disk -- only zip/meta present, cannot scan]")
                continue
            p = xmls[0]
        if not p.exists():
            print(f"{qtr:8s}  [MISSING: {p}]")
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        counts = []
        for name, pat in MARKERS:
            counts.append(len(re.findall(pat, text)))
        print(f"{qtr:8s} " + " ".join(f"{c:22d}" for c in counts))


if __name__ == "__main__":
    main()
