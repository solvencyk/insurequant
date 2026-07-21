"""Sample PDF content to manually inspect transitional measures."""
from pathlib import Path
import pdfplumber

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\solvency\data\disclosure\FY2025_Q4\pdf")

# Sample a few PDFs to see what the content looks like
samples = [
    "KR0001_메리츠화재해상보험.pdf",
    "KR0068_한화생명.pdf",
    "KR0099_케이비라이프생명보험.pdf",  # The one with selective measures
]

for pdf_name in samples:
    pdf_path = ROOT / pdf_name
    if not pdf_path.exists():
        print(f"NOT FOUND: {pdf_name}\n")
        continue

    print("=" * 80)
    print(f"FILE: {pdf_name}")
    print("=" * 80)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Search first 15 pages for 경과조치 keyword
            for page_idx in range(min(15, len(pdf.pages))):
                page = pdf.pages[page_idx]
                text = page.extract_text() or ""

                # Search for transitional measures keywords
                if any(kw in text for kw in ["경과조치", "선택적용", "공통적용"]):
                    print(f"\nPAGE {page_idx + 1}:")
                    print("-" * 80)
                    # Find and print lines containing keywords
                    for line in text.split('\n'):
                        if any(kw in line for kw in ["경과조치", "선택적용", "공통적용", "위험", "장수", "사업비", "해지", "대재"]):
                            print(line[:100])
                    print()

    except Exception as e:
        print(f"ERROR: {e}\n")

    print()
