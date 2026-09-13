# -*- coding: utf-8 -*-
"""
J-ESR EDINET fetcher. J-ICS ESR(Pillar-3) 를 EDINET 제출서류에서 찾는 루트.

Usage:
  python J-ESR/jesr_edinet_fetch.py --smoke              # 키 유효성·응답 확인
  python J-ESR/jesr_edinet_fetch.py --scan --from 2026-06-01 --to 2026-07-31
  python J-ESR/jesr_edinet_fetch.py --edinet-code E03847 --year 2026
  python J-ESR/jesr_edinet_fetch.py --all --year 2026

키: 환경변수 `EDINET_KEY` 가 기본. `--key` 로 덮어쓴다. 무료 등록은
  https://api.edinet-fsa.go.jp/ (EDINET API 利用登録) — 저장소에 키를 커밋하지 말 것.

2026-09-13 실측으로 고친 것 3가지
---------------------------------
1. **호스트**. 정본은 `api.edinet-fsa.go.jp/api/v2`. 종전의
   `disclosure.edinet-fsa.go.jp/api/v2` 는 301→`disclosure2…`→302 로 튕겨 간다(따라가면
   되긴 하나 홉 2개를 매 요청 낭비한다). **키 없이 부르면 HTTP 200 에 본문이
   `{"StatusCode": 401, …}` 로 온다** — status_code 만 보면 "성공인데 결과 0건" 으로 읽힌다.
2. **회사코드**. 하드코딩 dict 에 있던 13개 중 7개가 오답이었다(E04979=パーク24,
   E04506=九州電力 …). 코드는 이제 `jp_insurers.csv` 한 곳에서만 읽는다 —
   그 파일은 `edinet_codelist.py` 가 공식 코드리스트로 채운다.
3. **SSL**. `verify=False` 하드코딩을 걷어내고 `jesr_http.verify_setting()` 으로.
   기본 검증 ON, 회사망 SSL 인스펙션 PC 에서만 `JESR_INSECURE_SSL=1`.

Output: J-ESR/raw/edinet/<edinetCode>/<docID>/ (XBRL + meta JSON)
        J-ESR/raw/edinet/scan_<from>_<to>.json (스캔 인덱스)
"""

import argparse
import csv
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jesr_http  # noqa: E402

VERIFY_SSL = jesr_http.verify_setting()

# Windows CP949 stdout fix — always write UTF-8 bytes
def log(msg: str) -> None:
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()

BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"
OUT_DIR = Path(__file__).parent / "raw" / "edinet"
INSURERS_CSV = Path(__file__).resolve().parent / "jp_insurers.csv"

def load_insurer_codes(only_obligated: bool = False) -> dict[str, str]:
    """`jp_insurers.csv` 에서 EDINET 코드를 읽는다(정본은 그 csv 하나뿐).

    하드코딩 dict 를 되살리지 말 것 — 2026-09-13 실측에서 그 dict 의 13개 중 7개가
    다른 회사 코드였다. 갱신은 `python J-ESR/edinet_codelist.py --apply`.
    """
    codes: dict[str, str] = {}
    with INSURERS_CSV.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    for row in rows[1:]:
        if len(row) < 7:
            continue
        code, eligible = row[5].strip(), row[6].strip()
        if not code.startswith("E"):
            continue
        if only_obligated and eligible != "yes":
            continue
        codes.setdefault(code, row[0].strip())
    return codes


# Target disclosure types for J-ICS ESR
# 有価証券報告書 = docTypeCode "120"
# 半期報告書 = "140"
DOC_TYPE_YUHO = "120"

#: main() 에서 jp_insurers.csv 로 채운다(코드->회사명 표시용)
_CODE_NAMES: dict[str, str] = {}


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
                name = _CODE_NAMES.get(code, code)
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


def smoke_test(key: str) -> bool:
    """키 유효성 + 보험사 有報 가 실제로 잡히는지까지 확인(응답 200 만 보면 반쪽이다)."""
    log("[SMOKE] EDINET API v2 — key + insurer-filing check")
    probe_date = "2026-06-26"  # 3월기 有報 제출 피크(東京海上HD 제출일)
    url = f"{BASE_URL}/documents.json?date={probe_date}&type=2"
    resp = requests.get(url, headers=get_headers(key), timeout=30, verify=VERIFY_SSL)
    log(f"  HTTP {resp.status_code}  host={BASE_URL}")
    if resp.status_code != 200:
        log("[SMOKE] FAIL — 키 또는 호스트 확인")
        return False
    data = resp.json()
    meta = data.get("metadata", {})
    count = (meta.get("resultset") or {}).get("count", 0)
    log(f"  EDINET status={meta.get('status')} message={meta.get('message')} count={count}")
    codes = load_insurer_codes()
    docs = [d for d in data.get("results", [])
            if d.get("edinetCode") in codes and d.get("docTypeCode") == DOC_TYPE_YUHO]
    log(f"  보험사 有報 on {probe_date}: {len(docs)}")
    for d in docs:
        log(f"    {d['edinetCode']} {codes[d['edinetCode']]} docID={d['docID']} "
            f"period={d.get('periodEnd')}")
    ok = meta.get("status") == "200" and count > 0
    log("[SMOKE] PASS — key valid" if ok else "[SMOKE] FAIL — check key")
    return ok


def scan_range(key: str, start: str, end: str, doc_types: tuple = (DOC_TYPE_YUHO,)) -> dict:
    """기간 전체를 훑어 보험사 제출서류 인덱스를 만든다(하루 1콜).

    10월 재census 때 "누가 언제 무엇을 냈나" 를 사람 눈으로 찾지 않기 위한 인덱스.
    산출: J-ESR/raw/edinet/scan_<start>_<end>.json
    """
    codes = load_insurer_codes()
    log(f"[SCAN] {start} ~ {end} · 보험사 코드 {len(codes)}개 · docType {doc_types}")
    hits: list[dict] = []
    days = 0
    for date_str in _date_range(start, end):
        days += 1
        try:
            docs = fetch_documents_by_date(key, date_str)
        except Exception as exc:  # 하루 실패가 전체를 죽이지 않게
            log(f"  {date_str} WARN {exc}")
            time.sleep(0.5)
            continue
        for doc in docs:
            code = doc.get("edinetCode")
            if code in codes and doc.get("docTypeCode") in doc_types:
                rec = {
                    "date": date_str,
                    "edinet_code": code,
                    "company_jp": codes[code],
                    "filer_name": doc.get("filerName"),
                    "doc_id": doc.get("docID"),
                    "doc_type_code": doc.get("docTypeCode"),
                    "doc_description": doc.get("docDescription"),
                    "period_start": doc.get("periodStart"),
                    "period_end": doc.get("periodEnd"),
                    "submit_datetime": doc.get("submitDateTime"),
                    "xbrl_flag": doc.get("xbrlFlag"),
                    "pdf_flag": doc.get("pdfFlag"),
                }
                hits.append(rec)
                log(f"  HIT {date_str} {code} {codes[code]} {doc.get('docDescription')}")
        time.sleep(0.2)
    payload = {"scanned_days": days, "start": start, "end": end,
               "doc_types": list(doc_types), "insurer_codes": len(codes),
               "hits": hits}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"scan_{start}_{end}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"[SCAN] {len(hits)} hits / {days} days -> {out}")
    return payload


def main():
    parser = argparse.ArgumentParser(description="J-ESR EDINET fetcher")
    parser.add_argument("--key", default=os.environ.get("EDINET_KEY"),
                        help="EDINET Subscription-Key (기본: 환경변수 EDINET_KEY)")
    parser.add_argument("--smoke", action="store_true", help="Connectivity smoke test only")
    parser.add_argument("--scan", action="store_true",
                        help="기간 스캔 — 보험사 제출서류 인덱스만 만든다(다운로드 없음)")
    parser.add_argument("--from", dest="date_from", default="2026-06-01")
    parser.add_argument("--to", dest="date_to", default="2026-07-31")
    parser.add_argument("--doc-types", default=DOC_TYPE_YUHO,
                        help="쉼표구분 docTypeCode (기본 120=有価証券報告書)")
    parser.add_argument("--edinet-code", help="Fetch single company by EDINET code")
    parser.add_argument("--all", dest="all_known", action="store_true",
                        help="Fetch all insurer codes flagged edinet_eligible=yes")
    parser.add_argument("--year", type=int, default=2026,
                        help="Fiscal year (期末 March 31 of this year)")
    args = parser.parse_args()

    if not args.key:
        log("[FATAL] EDINET 키가 없다 — 환경변수 EDINET_KEY 를 세우거나 --key 로 넘긴다")
        sys.exit(2)

    if args.smoke:
        ok = smoke_test(args.key)
        sys.exit(0 if ok else 1)

    if args.scan:
        scan_range(args.key, args.date_from, args.date_to,
                   tuple(t.strip() for t in args.doc_types.split(",") if t.strip()))
        sys.exit(0)

    target_codes: list[str] = []
    if args.edinet_code:
        target_codes = [args.edinet_code]
    elif args.all_known:
        target_codes = list(load_insurer_codes(only_obligated=True))
    else:
        parser.print_help()
        sys.exit(1)

    global _CODE_NAMES
    _CODE_NAMES = load_insurer_codes()

    # Bulk search: one API call per day for all codes
    bulk = search_yuho_bulk(args.key, set(target_codes), args.year)

    results = []
    for code in target_codes:
        name = _CODE_NAMES.get(code, "unknown")
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
