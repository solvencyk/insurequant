#!/usr/bin/env python3
"""Crawl KIDI INCOS 장기보험 원수보험료 현황표 (손해보험) 월납초회보험료.

This is the *real* premium denominator for the NB CSM multiple, replacing the
circular IR-back-solved value (F2). End-to-end HTTP flow reverse-engineered from
incos.kidi.or.kr (matches the user's Selenium crawler goInsisDetail N07/070b07):

  detail   : POST /insMonth/detail/MN07.do
  companies: POST /insMonth/getQueryResult.do  queryId=getNCompanyInfo  (N01..N41)
  values   : POST /insMonth/getQueryResult.do  queryId=getMN07List
             comp_type=<Nxx> data_year=YYYYMM
             → row LINE=99111 (원리금보장형장기손해보험 합계, whole company)
               ITEM_VAL4 = 월납 초회보험료 금액 (천원)  ← denominator

Quarterly data_year is cumulative YTD (03=1Q, 06=1H, 09=9M, 12=FY).
Validation: 메리츠 202503 → 29,011,838 천원.

Output: data/_derived/kidi_longterm_premium.json
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
OUT_PATH = ROOT / "data" / "_derived" / "kidi_longterm_premium.json"

BASE = "https://incos.kidi.or.kr:5443"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TOTAL_LINE = "99111"  # 원리금보장형장기손해보험 합계 (whole-company total row)
# 초회보험료(보험계약) 금액 columns: 월납(VAL4) + 기타(VAL8). The denominator is
# their sum — 월납 초회 alone systematically over-states the CSM multiple ~5% vs
# IR; adding 기타 초회 closes most of the gap (삼성화재 15.1→14.8, DB 17.2→16.8).
# 일시납 초회(VAL2) is ~0 for 손보 long-term, so excluded.
FIRST_PREMIUM_COLS = ("ITEM_VAL4", "ITEM_VAL8")  # 월납 초회 + 기타 초회 (천원)

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

sys.stdout.reconfigure(encoding="utf-8")


class KidiLongTerm:
    def __init__(self) -> None:
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar()),
            urllib.request.HTTPSHandler(context=_CTX),
        )

    def _req(self, path, data=None, ajax=False,
             ref="/insMonth/detail/MN07.do", tries=5):
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

    def _rows(self, query_id, ref="/insMonth/detail/MN07.do", **params):
        txt = self._req("/insMonth/getQueryResult.do",
                        {"queryId": query_id, **params}, ajax=True, ref=ref)
        return (json.loads(txt).get("result") or {}).get("result") or []

    def warm(self) -> None:
        self._req("/insMonth/selMonthbookList.do", ref="/insMonth/selMonthbookList.do")
        time.sleep(0.3)
        self._req("/insMonth/detail/MN07.do",
                  {"stati_type": "3", "comp_ln": "3", "stati_sheet": "N01",
                   "gubun": "N07", "stattbl_id": "070b07"},
                  ref="/insMonth/selMonthbookList.do")
        time.sleep(0.3)

    def companies(self) -> list[dict]:
        """[{code: 'N01', name: '메리츠'}, ...] excluding the N00 합계 line."""
        out = []
        for d in self._rows("getNCompanyInfo"):
            code = d.get("DATA")
            name = d.get("LABEL")
            if code and name and code != "N00":
                out.append({"code": code, "name": name})
        return out

    def first_premium(self, comp_code: str, data_year: str) -> dict | None:
        """초회보험료 금액 (천원) for the whole-company total row.

        Returns {'wolnap': VAL4, 'etc': VAL8, 'sum': VAL4+VAL8} or None.
        """
        rows = self._rows("getMN07List", comp_type=comp_code, data_year=data_year)
        for r in rows:
            if str(r.get("LINE")) == TOTAL_LINE:
                def _n(col):
                    try:
                        return int(r.get(col))
                    except (TypeError, ValueError):
                        return 0
                wol = _n("ITEM_VAL4")
                etc = _n("ITEM_VAL8")
                if wol == 0 and etc == 0:
                    return None
                return {"wolnap": wol, "etc": etc, "sum": wol + etc}
        return None


def main() -> int:
    args = sys.argv[1:]
    # periods: default quarterly YTD 2023.1Q..2026.1Q (YYYYMM with MM in 03/06/09/12)
    if args:
        periods = args
    else:
        periods = [f"{y}{m:02d}" for y in (2023, 2024, 2025) for m in (3, 6, 9, 12)]
        periods.append("202603")

    cli = KidiLongTerm()
    cli.warm()
    comps = cli.companies()
    print(f"손보사 {len(comps)}곳, 기간 {len(periods)}개")

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
                    "first_premium_cheonwon": fp["sum"],         # 월납초회 + 기타초회
                    "first_premium_eok": round(fp["sum"] / 100_000.0, 2),
                    "wolnap_only_cheonwon": fp["wolnap"],
                    "etc_cheonwon": fp["etc"],
                }
            time.sleep(0.12)
        got = sum(1 for p in periods if f"{c['name']}|{p}" in records)
        print(f"  [{ci}/{len(comps)}] {c['name']}: {got}/{len(periods)}")

    payload = {
        "_meta": {
            "source": "KIDI INCOS 장기보험 원수보험료 현황표 (손해보험, N07/070b07)",
            "metric": "월납 초회보험료 금액 (보험계약), whole-company 합계 row (LINE 99111)",
            "unit_raw": "천원 (cheonwon)",
            "data_year_semantics": "cumulative YTD (MM=03/06/09/12)",
            "crawled_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "build_script": "scripts/crawl_kidi_longterm_premium.py",
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
