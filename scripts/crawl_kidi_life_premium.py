#!/usr/bin/env python3
"""Crawl KIDI INCOS 수입보험료 명세표 (생명보험) 신계약 초회보험료.

Life-insurance analogue of scripts/crawl_kidi_longterm_premium.py (손보 N07).
End-to-end HTTP flow reverse-engineered from incos.kidi.or.kr:

  detail   : POST /insMonth/detail/ML01.do
             {stati_type:3, comp_ln:3, stati_sheet:L01, gubun:L01,
              stattbl_id:070a01}
  companies: POST /insMonth/getQueryResult.do  queryId=getLCompanyInfo
             rows {DATA:'L03', LABEL:'삼성'} (L00 = 보험회사 합계, excluded)
  values   : POST /insMonth/getQueryResult.do  queryId=getML01List
             comp_type=<Lxx> data_year=YYYYMM
             → row LINE=47 (label '합     계', whole-company total)

Column mapping (확정 — 삼성생명 L03 202512 합계 row smoke test):
  ITEM_VAL2 = 일시납 초회보험료 금액 (= 2,755,506,632)
  ITEM_VAL4 = 월납   초회보험료 금액 (=   278,913,166)
  ITEM_VAL8 = 기타   초회보험료 금액 (=    33,858,094)
Odd ITEM_VALn are 건수(counts); even are 금액(천원). 투자계약 columns ignored.
일시납 is large for 생보 because 저축성 lump-sum dominates — captured separately
so the orchestrator can decide whether to exclude it from the CSM denominator.

Quarterly data_year is cumulative YTD (03=1Q, 06=1H, 09=9M, 12=FY).

Output: data/_derived/kidi_life_premium.json
"""
from __future__ import annotations

import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "_derived" / "kidi_life_premium.json"

BASE = "https://incos.kidi.or.kr:5443"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
DETAIL_REF = "/insMonth/detail/ML01.do"
TOTAL_LINE = "47"  # '합     계' whole-company total row (생보: NOT 99111)

# 신계약 초회보험료 금액 columns (천원); 투자계약 excluded.
COL_ILSINAP = "ITEM_VAL2"  # 일시납 초회
COL_WOLNAP = "ITEM_VAL4"   # 월납   초회
COL_ETC = "ITEM_VAL8"      # 기타   초회

# Per-product breakdown rows (LINE -> label). LINE numbers are stable across
# companies/quarters (they index the fixed template rows). 일반계정 보험상품
# 합계 (LINE 37) splits into 보장성(사망담보/사망담보외) + 저축성 below.
PRODUCT_ROWS = {
    "ilban_total": "37",   # [일반계정 보험상품 합계]
    "gaein": "99111",      # 1. 개인보험
    "bojangseong": "99112",  # 가. 보장성보험 (개인, 표준형)
    "jeochuk": "27",       # 나. 저축성보험 (개인)
    "wonrigeum": "42",     # [원리금보장형 특별계정 보험상품 합계]
    "siljeok": "46",       # [실적배당형 특별계정 보험상품 합계]
}

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

sys.stdout.reconfigure(encoding="utf-8")


def _to_int(v) -> int:
    """Round a float-string 천원 value to int (천원)."""
    try:
        return round(float(v))
    except (TypeError, ValueError):
        return 0


class KidiLife:
    def __init__(self) -> None:
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar()),
            urllib.request.HTTPSHandler(context=_CTX),
        )

    def _req(self, path, data=None, ajax=False, ref=DETAIL_REF, tries=5):
        h = {"User-Agent": UA, "Referer": BASE + ref}
        if ajax:
            h["X-Requested-With"] = "XMLHttpRequest"
            h["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        method = "POST" if data is not None else "GET"
        last = None
        for _ in range(tries):
            try:
                r = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
                return self.op.open(r, timeout=60).read().decode("utf-8", "replace")
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(1.5)
        raise last

    def _rows(self, query_id, ref=DETAIL_REF, **params):
        txt = self._req("/insMonth/getQueryResult.do",
                        {"queryId": query_id, **params}, ajax=True, ref=ref)
        return (json.loads(txt).get("result") or {}).get("result") or []

    def warm(self) -> None:
        self._req("/insMonth/selMonthbookList.do", ref="/insMonth/selMonthbookList.do")
        time.sleep(0.3)
        self._req("/insMonth/detail/ML01.do",
                  {"stati_type": "3", "comp_ln": "3", "stati_sheet": "L01",
                   "gubun": "L01", "stattbl_id": "070a01"},
                  ref="/insMonth/selMonthbookList.do")
        time.sleep(0.3)

    def companies(self) -> list[dict]:
        """[{code: 'L01', name: '한화'}, ...] excluding the L00 합계 line."""
        out = []
        for d in self._rows("getLCompanyInfo"):
            code = d.get("DATA")
            name = d.get("LABEL")
            if code and name and code != "L00":
                out.append({"code": code, "name": name})
        return out

    def first_premium(self, comp_code: str, data_year: str) -> dict | None:
        """신계약 초회보험료 금액 (천원) for the whole-company 합계 row + breakdown.

        Returns dict with 일시납/월납/기타 초회 and a per-product breakdown of
        each, or None if no data.
        """
        rows = self._rows("getML01List", comp_type=comp_code, data_year=data_year)
        if not rows:
            return None
        by_line = {str(r.get("LINE")): r for r in rows}
        total = by_line.get(TOTAL_LINE)
        if total is None:
            return None

        ils = _to_int(total.get(COL_ILSINAP))
        wol = _to_int(total.get(COL_WOLNAP))
        etc = _to_int(total.get(COL_ETC))
        if ils == 0 and wol == 0 and etc == 0:
            return None

        breakdown = {}
        for key, line in PRODUCT_ROWS.items():
            r = by_line.get(line)
            if r is None:
                continue
            breakdown[key] = {
                "ilsinap": _to_int(r.get(COL_ILSINAP)),
                "wolnap": _to_int(r.get(COL_WOLNAP)),
                "etc": _to_int(r.get(COL_ETC)),
            }

        return {
            "ilsinap": ils,
            "wolnap": wol,
            "etc": etc,
            # 월납+기타 초회 = 보장성 중심의 NB CSM 분모 후보 (일시납 저축성 제외)
            "wolnap_etc_sum": wol + etc,
            "breakdown": breakdown,
        }


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--smoke":
        cli = KidiLife()
        cli.warm()
        fp = cli.first_premium("L03", "202512")
        print("삼성생명 L03 202512 합계 row:")
        print(json.dumps(fp, ensure_ascii=False, indent=2))
        ok = (fp and fp["ilsinap"] == 2755506632
              and fp["wolnap"] == 278913166 and fp["etc"] == 33858094)
        print("SMOKE", "PASS" if ok else "FAIL")
        print("월납초회+기타초회 (억원):", round(fp["wolnap_etc_sum"] / 100_000.0, 2))
        return 0 if ok else 1

    # periods: default quarterly YTD 2023.1Q..2026.1Q (YYYYMM with MM in 03/06/09/12)
    if args:
        periods = args
    else:
        periods = [f"{y}{m:02d}" for y in (2023, 2024, 2025) for m in (3, 6, 9, 12)]
        periods.append("202603")

    cli = KidiLife()
    cli.warm()
    comps = cli.companies()
    print(f"생보사 {len(comps)}곳, 기간 {len(periods)}개")

    records: dict[str, dict] = {}
    for ci, c in enumerate(comps, 1):
        for p in periods:
            try:
                fp = cli.first_premium(c["code"], p)
            except Exception as e:  # noqa: BLE001
                print(f"  ! {c['name']} {p}: {e}")
                fp = None
            if fp:
                records[f"{c['name']}|{p}"] = {
                    "company_kidi": c["name"],
                    "comp_code": c["code"],
                    "data_year": p,
                    "ilsinap_chowoe_cheonwon": fp["ilsinap"],
                    "wolnap_chowoe_cheonwon": fp["wolnap"],
                    "etc_chowoe_cheonwon": fp["etc"],
                    "wolnap_etc_sum_cheonwon": fp["wolnap_etc_sum"],
                    "ilsinap_chowoe_eok": round(fp["ilsinap"] / 100_000.0, 2),
                    "wolnap_chowoe_eok": round(fp["wolnap"] / 100_000.0, 2),
                    "etc_chowoe_eok": round(fp["etc"] / 100_000.0, 2),
                    "wolnap_etc_sum_eok": round(fp["wolnap_etc_sum"] / 100_000.0, 2),
                    "breakdown_cheonwon": fp["breakdown"],
                }
            time.sleep(0.12)
        got = sum(1 for p in periods if f"{c['name']}|{p}" in records)
        print(f"  [{ci}/{len(comps)}] {c['name']}: {got}/{len(periods)}")

    payload = {
        "_meta": {
            "source": "KIDI INCOS 수입보험료 명세표 (생명보험, ML01/070a01)",
            "metric": "신계약 초회보험료 금액 (보험계약), whole-company 합계 row (LINE 47)",
            "columns": {
                "ilsinap_chowoe": "ITEM_VAL2 (일시납 초회)",
                "wolnap_chowoe": "ITEM_VAL4 (월납 초회)",
                "etc_chowoe": "ITEM_VAL8 (기타 초회)",
            },
            "note": ("일시납 초회 includes large 저축성 lump-sum; "
                     "wolnap_etc_sum excludes it (보장성 중심 NB CSM 분모 후보). "
                     "투자계약 컬럼 제외."),
            "unit_raw": "천원 (cheonwon)",
            "data_year_semantics": "cumulative YTD (MM=03/06/09/12)",
            "crawled_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "build_script": "scripts/crawl_kidi_life_premium.py",
            "periods": periods,
            "company_count": len(comps),
            "record_count": len(records),
        },
        "records": records,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH}  ({len(records)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
