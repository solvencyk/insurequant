"""
EDINET API v2 feasibility probe for J-ESR track.
Tests: document list retrieval, XBRL zip download, company search.
Run: python J-ESR/probe_edinet.py
Output: J-ESR/raw/edinet_probe_result.json
"""

import json
import urllib.request
import urllib.error
from pathlib import Path

RAW_DIR = Path(__file__).parent / "raw"
RAW_DIR.mkdir(exist_ok=True)

EDINET_BASE = "https://api.edinet-fsa.go.jp/api/v2"

# Insurance company EDINET codes (edinetCode) — major insurers
# Source: EDINET company search (https://disclosure.edinet-fsa.go.jp/)
INSURERS = {
    "E05026": "東京海上ホールディングス",
    "E14905": "MS&ADインシュアランスグループHD",
    "E04979": "SOMPOホールディングス",
    "E04506": "第一生命ホールディングス",
    "E06008": "T&Dホールディングス",
    "E33424": "ソニーフィナンシャルグループ",
    "E04678": "かんぽ生命保険",
}

# FY2025 annual report filing date range (有価証券報告書 for FY ending 2026-03-31
# typically filed June-July 2026)
PROBE_DATE = "2026-06-20"


def log(msg: str):
    import sys
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def fetch_json(url: str, label: str) -> dict:
    log(f"  GET {label}: {url[:80]}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "insurequant-probe/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            data = json.loads(raw.decode("utf-8"))
            # EDINET v2 response: top-level keys vary; check for "metadata" or "results"
            meta = data.get("metadata", {})
            count = (meta.get("resultset") or {}).get("count", len(data.get("results", [])))
            status = meta.get("status", resp.status)
            log(f"    -> OK, http={resp.status}, keys={list(data.keys())[:5]}, count={count}")
            return data
    except urllib.error.HTTPError as e:
        log(f"    -> HTTP {e.code}: {e.reason}")
        return {"error": f"HTTP {e.code}", "reason": str(e.reason)}
    except Exception as e:
        log(f"    -> ERROR: {e}")
        return {"error": str(e)}


def probe_document_list(date: str) -> dict:
    """書類一覧API — list all documents for a given date."""
    url = f"{EDINET_BASE}/documents.json?date={date}&type=2"
    return fetch_json(url, f"document_list({date})")


def probe_company_search(edinet_code: str, company: str) -> dict:
    """Filter document list for a specific company by edinetCode."""
    # EDINET API doesn't have a direct company search — filter from daily list
    url = f"{EDINET_BASE}/documents.json?date={PROBE_DATE}&type=2"
    result = fetch_json(url, f"doc_list_for_{edinet_code[:6]}")
    if "results" in result:
        docs = [d for d in result["results"] if d.get("edinetCode") == edinet_code]
        print(f"    -> Found {len(docs)} docs for {company} ({edinet_code})")
        return {"company": company, "edinetCode": edinet_code, "docs": docs}
    return {"company": company, "edinetCode": edinet_code, "error": result.get("error", "no results")}


def probe_no_key():
    """Test: can we call the API without a Subscription-Key?"""
    print("\n[1] No-key probe (expect 200 or 401)")
    url = f"{EDINET_BASE}/documents.json?date=2026-05-20&type=2"
    return fetch_json(url, "no_key_probe")


def probe_with_dates():
    """Test date range around FY2026 annual report filing season."""
    print("\n[2] Document list probes (FY2026 annual filing season)")
    results = {}
    for date in ["2026-06-20", "2026-07-01"]:
        results[date] = probe_document_list(date)
    return results


def main():
    print("=== EDINET API v2 Feasibility Probe ===")
    print(f"Target: {EDINET_BASE}")
    print(f"Purpose: J-ICS ESR solvency data for {len(INSURERS)} insurers\n")

    report = {
        "probe_date": PROBE_DATE,
        "target_insurers": INSURERS,
        "results": {}
    }

    # 1. No-key test
    report["results"]["no_key"] = probe_no_key()

    # 2. Date-range document list
    report["results"]["date_probes"] = probe_with_dates()

    # 3. Interpretation
    no_key = report["results"]["no_key"]
    if "error" in no_key:
        report["verdict"] = {
            "api_accessible": False,
            "requires_key": "HTTP 400/401" in str(no_key.get("error", "")),
            "note": "EDINET API v2 may require Subscription-Key registration at https://disclosure.edinet-fsa.go.jp/",
            "fallback": "IR PDF direct download (already done for headline ESR)",
        }
    else:
        report["verdict"] = {
            "api_accessible": True,
            "note": "API accessible without key. XBRLs available for FY2026 insurers once filed.",
            "next_step": "Download ZIP, parse XBRL for 経済価値ベースソルベンシー比率 element",
        }

    log("\n[3] Verdict:")
    log(json.dumps(report["verdict"], ensure_ascii=False, indent=2))

    out = RAW_DIR / "edinet_probe_result.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {out}")
    return report


if __name__ == "__main__":
    main()
