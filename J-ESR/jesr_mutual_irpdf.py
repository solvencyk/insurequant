"""
J-ESR IR-PDF route for non-EDINET mutual companies (相互会社).

Mutual life insurers are NOT required to file 有価証券報告書 with EDINET.
ESR data for these companies comes from:
  - ディスクロージャー誌 (annual disclosure report PDF) — published around June-July
  - 決算プレスリリース (earnings press release PDF) — published around May
  - 保険計理人意見書 (actuarial opinion) — sometimes embedded

Target companies:
  - 日本生命保険 (Nippon Life)
  - 住友生命保険 (Sumitomo Life)
  - 明治安田生命保険 (Meiji Yasuda Life)
  - 富国生命保険 (Fukoku Life)
  - 朝日生命保険 (Asahi Life)

Usage:
  python jesr_mutual_irpdf.py --check        # check URL availability
  python jesr_mutual_irpdf.py --download     # download all PDFs
  python jesr_mutual_irpdf.py --extract      # extract ESR via LLM (requires PDF in raw/)

Output: J-ESR/raw/mutual/<company>/<filename>.pdf
"""

import argparse
import json
from pathlib import Path

import requests

OUT_DIR = Path(__file__).parent / "raw" / "mutual"

# URL patterns for each mutual company's ESR/solvency disclosure.
# Updated annually — check IR pages each May/June.
MUTUAL_COMPANIES = [
    {
        "company_jp": "日本生命保険",
        "company_en": "Nippon Life Insurance",
        "code": "nippon_life",
        "ir_base": "https://www.nissay.co.jp/kaisha/annai/kenzen/",
        "disclosure_url": "https://www.nissay.co.jp/kaisha/annai/kenzen/",
        "press_url": "https://www.nissay.co.jp/news/2026/",
        "pdf_url_pattern": "TBD — check May 2026 press release page",
        "note": "ESR headline typically in May 決算プレス, detail in ディスクロ誌(July)",
    },
    {
        "company_jp": "住友生命保険",
        "company_en": "Sumitomo Life Insurance",
        "code": "sumitomo_life",
        "ir_base": "https://www.sumitomolife.co.jp/about/company/disclosure/settlement/",
        "disclosure_url": "https://www.sumitomolife.co.jp/about/company/disclosure/settlement/",
        "press_url": "https://www.sumitomolife.co.jp/about/news/",
        "pdf_url_pattern": "TBD — check May 2026 press release page",
        "note": "住友生命はESR 2026.3末=184%公表済(2025.3末比較). 資料=決算説明会資料",
    },
    {
        "company_jp": "明治安田生命保険",
        "company_en": "Meiji Yasuda Life Insurance",
        "code": "meiji_yasuda",
        "ir_base": "https://www.meijiyasuda.co.jp/profile/corporate_info/disclosure/data/",
        "disclosure_url": "https://www.meijiyasuda.co.jp/profile/corporate_info/disclosure/data/",
        "press_url": "https://www.meijiyasuda.co.jp/profile/news/",
        "pdf_url_pattern": "TBD — check May 2026 press release page",
        "note": "明治安田はESR 2026.3末=216%公表済(速報). 決算説明会資料に所要資本内訳あり",
    },
    {
        "company_jp": "富国生命保険",
        "company_en": "Fukoku Life Insurance",
        "code": "fukoku_life",
        "ir_base": "https://www.fukoku-life.co.jp/about/finance/health/",
        "disclosure_url": "https://www.fukoku-life.co.jp/about/finance/health/",
        "press_url": "https://www.fukoku-life.co.jp/aboutus/news/",
        "pdf_url_pattern": "TBD — check May 2026 press release page",
        "note": "富国生命はESR 2026.3末=260.9%公表済(速報)",
    },
    {
        "company_jp": "朝日生命保険",
        "company_en": "Asahi Life Insurance",
        "code": "asahi_life",
        "ir_base": "https://www.asahi-life.co.jp/company/zaimu/",
        "disclosure_url": "https://www.asahi-life.co.jp/company/zaimu/",
        "press_url": "https://www.asahi-life.co.jp/",
        "pdf_url_pattern": "TBD — check May 2026 press release page",
        "note": "小型相互社. ESR 2026.3末未確認",
    },
]

# Confirmed ESR values from prior manual collection (1차 수집).
# Used as seed for validation until PDFs are downloaded and re-extracted.
CONFIRMED_SEED = {
    "sumitomo_life": {"esr_pct": 184.0, "as_of": "2025-12-31", "as_of_consistent": False,
                      "source": "manual_2024Q3_press"},
    "meiji_yasuda": {"esr_pct": 216.0, "as_of": "2025-12-31", "as_of_consistent": False,
                     "source": "manual_2024Q3_press"},
    "fukoku_life": {"esr_pct": 260.9, "as_of": "2025-12-31", "as_of_consistent": False,
                    "source": "manual_2024Q3_press"},
    "nippon_life": {"esr_pct": 224.0, "as_of": "2025-12-31", "as_of_consistent": False,
                    "source": "manual_2024Q3_press"},
}


def check_urls():
    """HEAD check on all known IR pages."""
    print("[CHECK] Verifying mutual company IR pages...")
    for c in MUTUAL_COMPANIES:
        for label, url in [("ir_base", c["ir_base"]), ("press", c["press_url"])]:
            try:
                r = requests.head(url, timeout=10, allow_redirects=True)
                status = r.status_code
            except Exception as e:
                status = f"ERROR:{e}"
            print(f"  {c['code']:20s} {label:8s} [{status}] {url}")


def download_pdfs(dry_run: bool = False):
    """
    Download ESR PDFs for mutual companies.
    PDF URLs must be updated each year — check IR pages for actual links.
    """
    print("[DOWNLOAD] Downloading mutual company PDFs...")
    for c in MUTUAL_COMPANIES:
        pattern = c.get("pdf_url_pattern", "TBD")
        if pattern.startswith("TBD"):
            print(f"  {c['code']:20s} SKIP — pdf_url_pattern not yet set (check IR after May 2026)")
            continue
        out = OUT_DIR / c["code"]
        out.mkdir(parents=True, exist_ok=True)
        filename = pattern.split("/")[-1]
        dest = out / filename
        if dry_run:
            print(f"  {c['code']:20s} DRY-RUN -> {dest}")
            continue
        print(f"  {c['code']:20s} Downloading {pattern}...")
        try:
            r = requests.get(pattern, timeout=60, stream=True)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
            print(f"    Saved {dest} ({dest.stat().st_size} bytes)")
        except Exception as e:
            print(f"    ERROR: {e}")


def extract_esr_from_pdfs():
    """
    Extract ESR fields from downloaded PDFs using LLM.

    LLM prompt template (Japanese):
    ---
    以下の日本語保険会社PDFから、経済価値ベースの支払余力（ESR/J-ICS）に関する以下の数値を抽出してください。
    - ESR比率 (%)
    - 所要資本 (億円 or 百万円)
    - 適格資本 (億円 or 百万円)
    - 基準日 (YYYY-MM-DD)
    数値が見つからない場合は null とし、理由をnotesに記載してください。
    ---
    Validator: eligible_capital / required_capital * 100 ~= esr_pct (±2%)
    """
    print("[EXTRACT] Extracting ESR from mutual company PDFs...")
    results = []
    for c in MUTUAL_COMPANIES:
        pdf_dir = OUT_DIR / c["code"]
        pdfs = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
        if not pdfs:
            seed = CONFIRMED_SEED.get(c["code"])
            rec = {
                "company_jp": c["company_jp"],
                "company_en": c["company_en"],
                "code": c["code"],
                "esr_pct": seed["esr_pct"] if seed else None,
                "as_of": seed["as_of"] if seed else None,
                "as_of_consistent": seed["as_of_consistent"] if seed else None,
                "eligible_capital_mn_jpy": None,
                "required_capital_mn_jpy": None,
                "source": seed["source"] if seed else "none",
                "status": "seed_only_no_pdf",
                "note": c["note"],
            }
        else:
            # Placeholder for actual LLM extraction
            rec = {
                "company_jp": c["company_jp"],
                "company_en": c["company_en"],
                "code": c["code"],
                "esr_pct": None,
                "as_of": None,
                "as_of_consistent": None,
                "eligible_capital_mn_jpy": None,
                "required_capital_mn_jpy": None,
                "pdf_files": [str(p.name) for p in pdfs],
                "source": "pdf_extraction_stub",
                "status": "pdf_found_extraction_needed",
                "note": "Run LLM extraction on these PDFs",
            }
        results.append(rec)
        print(f"  {c['code']:20s} esr={rec['esr_pct']} status={rec['status']}")

    out_json = Path(__file__).parent / "raw" / "mutual_esr_extract.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[DONE] {len(results)} mutual companies -> {out_json}")
    return results


def main():
    parser = argparse.ArgumentParser(description="J-ESR mutual company IR-PDF route")
    parser.add_argument("--check", action="store_true", help="Check IR page availability")
    parser.add_argument("--download", action="store_true", help="Download PDFs")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual download)")
    parser.add_argument("--extract", action="store_true", help="Extract ESR from PDFs")
    args = parser.parse_args()

    if args.check:
        check_urls()
    if args.download:
        download_pdfs(dry_run=args.dry_run)
    if args.extract:
        extract_esr_from_pdfs()
    if not any([args.check, args.download, args.extract]):
        parser.print_help()


if __name__ == "__main__":
    main()
