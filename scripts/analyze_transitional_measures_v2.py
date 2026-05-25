"""Extract and analyze transitional measures with detailed output to JSON."""
from __future__ import annotations

import json
import re
from pathlib import Path
from collections import defaultdict

import pdfplumber

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\solvency\data\disclosure\FY2025_Q4\pdf")
OUTPUT = Path(r"C:\Users\sangwook.cho\Desktop\solvency\transitional_measures_analysis.json")

def extract_text_from_pdf(pdf_path: Path, max_pages: int = 30) -> str:
    """Extract text from first N pages of PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = min(len(pdf.pages), max_pages)
            pages = [pdf.pages[i].extract_text() or "" for i in range(num_pages)]
            return "\n".join(pages)
    except Exception as e:
        return f"ERROR: {e.__class__.__name__}"


def find_transitional_measures_section(text: str) -> dict:
    """Extract transitional measures section with more detailed matching."""
    results = {
        "has_transitional_measures": False,
        "sections_found": [],
        "selective_measures": [],
        "common_measures": [],
        "specific_risks": {
            "longevity": False,
            "expense": False,
            "lapse": False,
            "disaster": False,
        },
    }

    # Normalize whitespace within Korean text
    text_normalized = re.sub(r"([가-힣])\s+([가-힣])", r"\1\2", text)

    # Look for transitional measures sections
    # Pattern 1: "경과조치" heading with content
    pattern = r"(경과조치.*?)(?=\n[가-힣]|\n\d|$)"
    matches = re.finditer(pattern, text_normalized, re.DOTALL)

    for match in matches:
        section = match.group(1)[:500]  # Get first 500 chars
        results["has_transitional_measures"] = True
        results["sections_found"].append(section)

    # Look for "선택적용"
    if "선택적용" in text_normalized:
        results["has_transitional_measures"] = True
        # Try to extract surrounding context
        idx = text_normalized.find("선택적용")
        context = text_normalized[max(0, idx-100):idx+300]
        results["selective_measures"].append(context)

    # Look for "공통적용"
    if "공통적용" in text_normalized:
        results["has_transitional_measures"] = True
        idx = text_normalized.find("공통적용")
        context = text_normalized[max(0, idx-100):idx+300]
        results["common_measures"].append(context)

    # Check for specific risks
    if any(kw in text_normalized for kw in ["장수위험", "장수 위험"]):
        results["specific_risks"]["longevity"] = True
    if any(kw in text_normalized for kw in ["사업비위험", "사업비 위험"]):
        results["specific_risks"]["expense"] = True
    if any(kw in text_normalized for kw in ["해지위험", "해지 위험"]):
        results["specific_risks"]["lapse"] = True
    if any(kw in text_normalized for kw in ["대재해위험", "대재해 위험", "대상해"]):
        results["specific_risks"]["disaster"] = True

    return results


def main():
    pdfs = sorted(ROOT.glob("*.pdf"))
    print(f"Analyzing {len(pdfs)} PDFs from FY2025_Q4...", flush=True)

    results_by_company: dict[str, dict] = {}

    for i, pdf_path in enumerate(pdfs, 1):
        company_code = pdf_path.stem.split("_")[0]
        company_name = pdf_path.stem.split("_", 1)[1] if "_" in pdf_path.stem else "?"

        print(f"[{i:2d}/{len(pdfs)}] {company_code}...", end=" ", flush=True)

        text = extract_text_from_pdf(pdf_path)

        if "ERROR" in text:
            print("ERROR")
            results_by_company[company_code] = {
                "company_name": company_name,
                "status": "error",
                "error_msg": text,
            }
            continue

        if len(text.strip()) < 100:
            print("NO_TEXT")
            results_by_company[company_code] = {
                "company_name": company_name,
                "status": "no_text",
            }
            continue

        analysis = find_transitional_measures_section(text)
        print("OK")

        results_by_company[company_code] = {
            "company_name": company_name,
            "status": "ok",
            **analysis,
        }

    # Save to JSON
    output_data = {
        "total_companies": len(pdfs),
        "analysis_timestamp": "2025.4Q",
        "companies": results_by_company,
    }

    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {OUTPUT}")

    # Print summary
    companies_with_measures = sum(
        1 for data in results_by_company.values()
        if data.get("has_transitional_measures", False)
    )

    print(f"\nCompanies with transitional measures: {companies_with_measures}/{len(pdfs)}")


if __name__ == "__main__":
    raise SystemExit(main())
