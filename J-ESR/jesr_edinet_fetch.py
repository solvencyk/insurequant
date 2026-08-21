"""
J-ESR EDINET fetcher scaffold.
Fetches J-ICS ESR disclosure (Pillar-3) from EDINET XBRL filings.

Usage:
  python jesr_edinet_fetch.py --key YOUR_SUBSCRIPTION_KEY [--smoke]
  python jesr_edinet_fetch.py --key YOUR_SUBSCRIPTION_KEY --edinet-code E05026
  python jesr_edinet_fetch.py --key YOUR_SUBSCRIPTION_KEY --all --year 2026

EDINET free key registration:
  https://disclosure2.edinet-fsa.go.jp/  -> EDINET API -> Subscription-Key 取得

Output: J-ESR/raw/edinet/<edinetCode>/<docID>/ (XBRL + meta JSON)
"""

import argparse
import json
import sys
import time
import zipfile
from pathlib import Path

import requests
import urllib3

# Company-network SSL inspection workaround (self-signed CA in chain)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
VERIFY_SSL = False

# Windows CP949 stdout fix — always write UTF-8 bytes
def log(msg: str) -> None:
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()

BASE_URL = "https://disclosure.edinet-fsa.go.jp/api/v2"
OUT_DIR = Path(__file__).parent / "raw" / "edinet"

# Known EDINET codes for major insurance groups and listed companies.
# TBD codes will be populated once API key is obtained and bulk lookup runs.
KNOWN_INSURER_EDINET_CODES = {
    # HD listed
    "E05026": "東京海上ホールディングス",
    "E14905": "MS&ADインシュアランスグループHD",
    "E04979": "SOMPOホールディングス",
    "E04506": "第一生命ホールディングス",
    "E06008": "T&Dホールディングス",
    "E33424": "ソニーフィナンシャルグループ",
    "E04678": "かんぽ生命保険",
    # Listed subsidiaries filing 有報 (bonds/equity)
    "E03823": "東京海上日動火災保険",
    "E03824": "三井住友海上火災保険",
    "E03827": "損害保険ジャパン",
    "E03829": "日新火災海上保険",
    "E03833": "あいおいニッセイ同和損害保険",
    "E03850": "共栄火災海上保険",
    # TBD: populated by --lookup-all run after key obtained
    # "TXXXXXX": "第一生命保険",
    # "TXXXXXX": "大同生命保険",
    # "TXXXXXX": "太陽生命保険",
    # "TXXXXXX": "ソニー生命保険",
    # "TXXXXXX": "ライフネット生命保険",  # ticker 7157
}

# Target disclosure types for J-ICS ESR
# 有価証券報告書 = docTypeCode "120"
# 半期報告書 = "140"
DOC_TYPE_YUHO = "120"


def get_headers(key: str) -> dict:
    return {"Ocp-Apim-Subscription-Key": key}


def fetch_documents_by_date(key: str, date: str) -> list[dict]:
    """Fetch document list for a given date (YYYY-MM-DD)."""
    url = f"{BASE_URL}/documents.json?date={date}&type=2"
    resp = requests.get(url, headers=get_headers(key), timeout=30, verify=VERIFY_SSL)
    resp.raise_for_status()
    data = resp.json()
    if data.get("metadata", {}).get("status") != "200":
        raise RuntimeError(f"EDINET error: {data}")
    return data.get("results", [])


def _date_range(start: str, end: str):
    """Yield YYYY-MM-DD strings from start to end inclusive."""
    from datetime import date, timedelta
    d = date.fromisoformat(start)
    e = date.fromisoformat(end)
    while d <= e:
        yield d.isoformat()
        d += timedelta(days=1)


def search_yuho_bulk(key: str, target_codes: set, year: int) -> dict[str, list[dict]]:
    """
    Efficient bulk search: one API call per day, filter all target codes at once.
    Returns {edinet_code: [doc, ...]} for any matching documents.
    """
    from datetime import date as date_cls
    start = f"{year}-06-01"
    today = date_cls.today().isoformat()
    end = min(f"{year}-10-31", today)
    log(f"[BULK] Scanning {start}~{end} for {len(target_codes)} codes ...")
    results: dict = {code: [] for code in target_codes}
    for date_str in _date_range(start, end):
        try:
            docs = fetch_documents_by_date(key, date_str)
        except RuntimeError as e:
            if "404" in str(e):
                log(f"  {date_str}: 404 (future) — stopping")
                break
            log(f"  {date_str} WARN: {e}")
            time.sleep(0.5)
            continue
        except Exception as e:
            log(f"  {date_str} ERROR: {e}")
            time.sleep(0.5)
            continue
        hits = 0
        for doc in docs:
            code = doc.get("edinetCode")
            if code in target_codes and doc.get("docTypeCode") == DOC_TYPE_YUHO:
                name = KNOWN_INSURER_EDINET_CODES.get(code, code)
                log(f"  FOUND {date_str}: {code} {name} docID={doc.get('docID')} "
                    f"period={doc.get('periodStart')}~{doc.get('periodEnd')}")
                results[code].append(doc)
                hits += 1
        if hits == 0:
            pass  # silent for non-hit days
        time.sleep(0.3)
    return results


def search_yuho_for_insurer(key: str, edinet_code: str, year: int) -> list[dict]:
    """Single-code search (wraps bulk search for backward compat)."""
    bulk = search_yuho_bulk(key, {edinet_code}, year)
    return bulk.get(edinet_code, [])


def download_xbrl_zip(key: str, doc_id: str, out_dir: Path) -> Path:
    """Download and extract XBRL package for a given document ID."""
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{doc_id}.zip"
    url = f"{BASE_URL}/documents/{doc_id}?type=1"
    resp = requests.get(url, headers=get_headers(key), stream=True, timeout=60, verify=VERIFY_SSL)
    resp.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)
    return out_dir


def extract_esr_from_xbrl(xbrl_dir: Path) -> dict:
    """
    Extract ESR Pillar-3 fields from XBRL files.

    J-ICS XBRL taxonomy tags (FSA draft, expected in FY2025 有報 schema):
      - jis:EconomicSolvencyRatio (ESR%)
      - jis:EligibleCapital (適格資本, 百万円)
      - jis:RequiredCapital (所要資本, 百万円)
      - jis:EligibleCapitalTier1 / Tier2
      - jis:RequiredCapitalInsuranceRisk / MarketRisk / CreditRisk / OperationalRisk

    STUB: actual tag names TBD until FSA publishes J-ICS XBRL taxonomy (expected FY2025 有報 cycle).
    Until then, parse inline XBRL from HTML or extract from PDF via LLM.
    """
    xbrl_files = list(xbrl_dir.rglob("*.xbrl")) + list(xbrl_dir.rglob("*.xml"))
    result = {
        "esr_pct": None,
        "eligible_capital_mn_jpy": None,
        "required_capital_mn_jpy": None,
        "extraction_method": "xbrl_stub",
        "xbrl_files_found": [str(f.relative_to(xbrl_dir)) for f in xbrl_files[:10]],
        "note": "XBRL taxonomy tags TBD — FSA J-ICS schema not yet published",
    }
    return result


def validate_esr_record(rec: dict) -> list[str]:
    """Math-based validator (no hand-gold needed)."""
    errors = []
    esr = rec.get("esr_pct")
    ec = rec.get("eligible_capital_mn_jpy")
    rc = rec.get("required_capital_mn_jpy")
    if esr is not None:
        if not (80 <= esr <= 600):
            errors.append(f"esr_pct={esr} outside plausible range 80-600%")
    if ec is not None and rc is not None and rc > 0:
        derived = ec / rc * 100
        if esr is not None and abs(derived - esr) > 2:
            errors.append(
                f"math mismatch: eligible/required*100={derived:.1f} vs esr_pct={esr}"
            )
    return errors


def smoke_test(key: str):
    """Smoke test: verify API connectivity with key."""
    log("[SMOKE] Testing EDINET API connectivity...")
    # Use a known weekday with filings
    url = f"{BASE_URL}/documents.json?date=2025-06-19&type=2"
    resp = requests.get(url, headers=get_headers(key), timeout=30, verify=VERIFY_SSL)
    log(f"  HTTP status: {resp.status_code}")
    data = resp.json()
    meta = data.get("metadata", {})
    log(f"  EDINET status: {meta.get('status')} message: {meta.get('message')}")
    count = meta.get("resultset", {}).get("count", 0)
    log(f"  Documents on 2025-06-19: {count}")
    if meta.get("status") == "200":
        log("[SMOKE] PASS — API key valid")
        return True
    log("[SMOKE] FAIL — check key")
    return False


def main():
    parser = argparse.ArgumentParser(description="J-ESR EDINET fetcher scaffold")
    parser.add_argument("--key", required=True, help="EDINET Subscription-Key")
    parser.add_argument("--smoke", action="store_true", help="Connectivity smoke test only")
    parser.add_argument("--edinet-code", help="Fetch single company by EDINET code")
    parser.add_argument("--all", dest="all_known", action="store_true",
                        help="Fetch all known insurer codes")
    parser.add_argument("--year", type=int, default=2026,
                        help="Fiscal year (期末 March 31 of this year)")
    args = parser.parse_args()

    if args.smoke:
        ok = smoke_test(args.key)
        sys.exit(0 if ok else 1)

    target_codes: list[str] = []
    if args.edinet_code:
        target_codes = [args.edinet_code]
    elif args.all_known:
        target_codes = list(KNOWN_INSURER_EDINET_CODES.keys())
    else:
        parser.print_help()
        sys.exit(1)

    # Bulk search: one API call per day for all codes
    bulk = search_yuho_bulk(args.key, set(target_codes), args.year)

    results = []
    for code in target_codes:
        name = KNOWN_INSURER_EDINET_CODES.get(code, "unknown")
        docs = bulk.get(code, [])
        if not docs:
            log(f"\n[{code}] {name} — not yet submitted")
            results.append({"edinet_code": code, "company_jp": name, "status": "not_found"})
            continue
        for doc in docs:
            doc_id = doc["docID"]
            out = OUT_DIR / code / doc_id
            log(f"\n[{code}] {name} — downloading {doc_id}...")
            try:
                download_xbrl_zip(args.key, doc_id, out)
                esr_data = extract_esr_from_xbrl(out)
                errors = validate_esr_record(esr_data)
                results.append({
                    "edinet_code": code,
                    "company_jp": name,
                    "doc_id": doc_id,
                    "period_start": doc.get("periodStart"),
                    "period_end": doc.get("periodEnd"),
                    "submit_date": doc.get("submitDateTime"),
                    "esr_data": esr_data,
                    "validation_errors": errors,
                    "status": "ok" if not errors else "warn",
                })
            except Exception as e:
                log(f"  ERROR: {e}")
                results.append({"edinet_code": code, "company_jp": name, "doc_id": doc_id,
                                 "status": "error", "error": str(e)})
            time.sleep(1)

    out_json = Path(__file__).parent / "raw" / "edinet_fetch_results.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"\n[DONE] {len(results)} records -> {out_json}")


if __name__ == "__main__":
    main()
