"""Extract and analyze transitional measures (경과조치) from FY2025_Q4 PDFs.

분석 대상:
  1. 공통적용 경과조치 (모든 회사)
  2. 선택적용 경과조치 (회사별 상이)
  3. 특히 ② 장수위험·사업비위험·해지위험 및 대재해위험 경과조치
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pdfplumber

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\solvency\data\disclosure\FY2025_Q4\pdf")

# Keywords to search for
KEYWORDS = {
    "common": ["공통적용 경과조치", "공통적용"],
    "selective": ["선택적용 경과조치", "선택적용"],
    "longevity": ["장수위험", "장수 위험"],
    "expense": ["사업비위험", "사업비 위험"],
    "lapse": ["해지위험", "해지 위험"],
    "disaster": ["대재해위험", "대재해 위험", "대상해"],
    "type2": ["② ", "2. ", "2)"],  # 아이템 ② 찾기
}

def extract_text_from_pdf(pdf_path: Path, max_pages: int = 20) -> str:
    """Extract text from first N pages of PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = min(len(pdf.pages), max_pages)
            pages = [pdf.pages[i].extract_text() or "" for i in range(num_pages)]
            return "\n".join(pages)
    except Exception as e:
        return f"ERROR: {e.__class__.__name__}"


def analyze_transitional_measures(text: str) -> dict:
    """Analyze which transitional measures are present in the text."""
    results = {
        "has_common": False,
        "has_selective": False,
        "has_longevity": False,
        "has_expense": False,
        "has_lapse": False,
        "has_disaster": False,
        "has_type2_item": False,
        "section_snippet": None,
    }

    # Normalize spaces within keywords
    text_normalized = re.sub(r"([가-힣])\s+([가-힣])", r"\1\2", text)

    # Check for keywords
    if any(kw in text_normalized for kw in KEYWORDS["common"]):
        results["has_common"] = True

    if any(kw in text_normalized for kw in KEYWORDS["selective"]):
        results["has_selective"] = True

    if any(kw in text_normalized for kw in KEYWORDS["longevity"]):
        results["has_longevity"] = True

    if any(kw in text_normalized for kw in KEYWORDS["expense"]):
        results["has_expense"] = True

    if any(kw in text_normalized for kw in KEYWORDS["lapse"]):
        results["has_lapse"] = True

    if any(kw in text_normalized for kw in KEYWORDS["disaster"]):
        results["has_disaster"] = True

    # Check for ② item (item 2 in list)
    if re.search(r"②\s", text_normalized):
        results["has_type2_item"] = True

    # Try to capture a snippet around "선택적용 경과조치"
    match = re.search(
        r"(선택적용\s*경과조치.{0,300})",
        text_normalized,
        re.DOTALL
    )
    if match:
        snippet = match.group(1)[:200]
        results["section_snippet"] = snippet

    return results


def main():
    pdfs = sorted(ROOT.glob("*.pdf"))
    print(f"Analyzing {len(pdfs)} PDFs from FY2025_Q4...\n")

    results_by_company: dict[str, dict] = {}

    for i, pdf_path in enumerate(pdfs, 1):
        company_code = pdf_path.stem.split("_")[0]
        company_name = pdf_path.stem.split("_", 1)[1] if "_" in pdf_path.stem else "?"

        print(f"[{i:2d}/{len(pdfs)}] {company_code} {company_name}...", end=" ", flush=True)

        text = extract_text_from_pdf(pdf_path)

        if "ERROR" in text:
            print(f"[ERROR] {text}")
            results_by_company[company_code] = {
                "company_name": company_name,
                "status": "error",
                "error_msg": text,
            }
            continue

        if len(text.strip()) < 100:
            print("[NO_TEXT] Image-only PDF")
            results_by_company[company_code] = {
                "company_name": company_name,
                "status": "no_text",
            }
            continue

        analysis = analyze_transitional_measures(text)
        print("[OK]")

        results_by_company[company_code] = {
            "company_name": company_name,
            "status": "ok",
            **analysis,
        }

    # Generate report
    print("\n" + "=" * 80)
    print("SUMMARY: 경과조치 적용 현황 (Transitional Measures)")
    print("=" * 80)

    # Group by measure type
    has_selective = [
        (code, data) for code, data in results_by_company.items()
        if data.get("has_selective", False)
    ]
    has_longevity_risk = [
        (code, data) for code, data in results_by_company.items()
        if data.get("has_longevity", False)
    ]
    has_expense_risk = [
        (code, data) for code, data in results_by_company.items()
        if data.get("has_expense", False)
    ]
    has_lapse_risk = [
        (code, data) for code, data in results_by_company.items()
        if data.get("has_lapse", False)
    ]
    has_disaster_risk = [
        (code, data) for code, data in results_by_company.items()
        if data.get("has_disaster", False)
    ]

    print(f"\n[선택적용 경과조치 적용 회사]: {len(has_selective)}개")
    for code, data in sorted(has_selective):
        print(f"  {code:6s} {data['company_name']}")

    print(f"\n[구체적 위험별 적용 현황]")
    print(f"  - 장수위험 경과조치:                    {len(has_longevity_risk):2d}개")
    for code, data in sorted(has_longevity_risk)[:10]:
        print(f"      {code:6s} {data['company_name']}")
    if len(has_longevity_risk) > 10:
        print(f"      ... and {len(has_longevity_risk) - 10} more")

    print(f"  - 사업비위험 경과조치:                  {len(has_expense_risk):2d}개")
    for code, data in sorted(has_expense_risk)[:10]:
        print(f"      {code:6s} {data['company_name']}")
    if len(has_expense_risk) > 10:
        print(f"      ... and {len(has_expense_risk) - 10} more")

    print(f"  - 해지위험 경과조치:                    {len(has_lapse_risk):2d}개")
    for code, data in sorted(has_lapse_risk)[:10]:
        print(f"      {code:6s} {data['company_name']}")
    if len(has_lapse_risk) > 10:
        print(f"      ... and {len(has_lapse_risk) - 10} more")

    print(f"  - 대재해위험 경과조치:                  {len(has_disaster_risk):2d}개")
    for code, data in sorted(has_disaster_risk)[:10]:
        print(f"      {code:6s} {data['company_name']}")
    if len(has_disaster_risk) > 10:
        print(f"      ... and {len(has_disaster_risk) - 10} more")

    # Detailed table
    print("\n" + "=" * 80)
    print("DETAILED TABLE: 회사별 경과조치 적용 현황")
    print("=" * 80)
    print(f"{'Code':<8} {'Company':<30} {'선택':<4} {'장수':<4} {'사업':<4} {'해지':<4} {'대재':<4} {'Status':<8}")
    print("-" * 80)

    for code in sorted(results_by_company.keys()):
        data = results_by_company[code]
        if data["status"] == "ok":
            selective = "O" if data.get("has_selective", False) else "-"
            longevity = "O" if data.get("has_longevity", False) else "-"
            expense = "O" if data.get("has_expense", False) else "-"
            lapse = "O" if data.get("has_lapse", False) else "-"
            disaster = "O" if data.get("has_disaster", False) else "-"
            print(
                f"{code:<8} {data['company_name']:<30} {selective:<4} {longevity:<4} {expense:<4} {lapse:<4} {disaster:<4} {'OK':<8}"
            )
        elif data["status"] == "no_text":
            print(f"{code:<8} {data['company_name']:<30} {'?':<4} {'?':<4} {'?':<4} {'?':<4} {'?':<4} {'NO_TEXT':<8}")
        else:
            print(f"{code:<8} {data['company_name']:<30} {'?':<4} {'?':<4} {'?':<4} {'?':<4} {'?':<4} {'ERROR':<8}")

    print("\nLegend: O = 적용 / - = 미적용 / ? = 확인 불가")
    print("\n선택: 선택적용 경과조치")
    print("장수: 장수위험 경과조치")
    print("사업: 사업비위험 경과조치")
    print("해지: 해지위험 경과조치")
    print("대재: 대재해위험 경과조치")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
