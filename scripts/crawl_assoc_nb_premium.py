#!/usr/bin/env python3
"""Crawl + merge 월납환산 신계약 premium sources.

Sources (priority when merging per company/period):
  1. data/assoc/nb_premium_overrides.yaml
  2. KIDI INCOS insLong/selectStattblAjax (when numeric rows exist)
  3. data/assoc/ir_wolnap_benchmarks.json (IR text extract)

Output: data/assoc/nb_premium_wolnap.json
Run: scripts/extract_ir_wolnap_benchmarks.py first for IR benchmarks.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from assoc.nb_premium_common import load_alias_map, resolve_company, sibeok_month_to_eok_month  # noqa: E402

OUT_PATH = ROOT / "data" / "assoc" / "nb_premium_wolnap.json"
IR_BENCH_PATH = ROOT / "data" / "assoc" / "ir_wolnap_benchmarks.json"
OVERRIDES_PATH = ROOT / "data" / "assoc" / "nb_premium_overrides.yaml"
TEMPLATES_OUT = ROOT / "templates" / "data" / "assoc" / "nb_premium_wolnap.json"

BASE = "https://incos.kidi.or.kr:5443"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

KIDI_LONG_COMPANY_STATTBL = "20040"  # 장기 회사별 (probe: col1=year, str1=company)


def _load_yaml_companies(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw.get("companies") or {}


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


class KidiClient:
    def __init__(self) -> None:
        self.cj = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def _request(
        self,
        path: str,
        data: dict | None = None,
        *,
        ajax: bool = False,
        referer: str = BASE + "/insMonth/selMonthbookList.do",
    ) -> str:
        url = BASE + path
        if data is None:
            req = urllib.request.Request(url)
        else:
            body = urllib.parse.urlencode(data).encode()
            req = urllib.request.Request(url, data=body, method="POST")
            req.add_header(
                "Content-Type",
                "application/x-www-form-urlencoded; charset=UTF-8"
                if ajax
                else "application/x-www-form-urlencoded",
            )
        req.add_header("User-Agent", UA)
        if ajax:
            req.add_header("X-Requested-With", "XMLHttpRequest")
        req.add_header("Referer", referer)
        return self.opener.open(req, timeout=60).read().decode("utf-8", "replace")

    def warm(self) -> None:
        self._request("/insMonth/selMonthbookList.do")

    def query(self, query_id: str, referer: str, **params: str) -> dict:
        payload = {"queryId": query_id, **params}
        text = self._request("/insMonth/getQueryResult.do", payload, ajax=True, referer=referer)
        return json.loads(text)

    def crawl_ml02(self) -> dict:
        spec = {
            "id": "life_company_ml02",
            "detail_path": "/insMonth/detail/ML02.do",
            "query_last": "getML02LastYM",
            "query_list": "getML02List",
            "form": {
                "stati_type": "3",
                "comp_ln": "3",
                "stati_sheet": "L01",
                "gubun": "L02",
                "stattbl_id": "070a02",
            },
        }
        referer = BASE + spec["detail_path"]
        self._request(spec["detail_path"], spec["form"], referer=BASE + "/insMonth/selMonthbookList.do")
        last_resp = self.query(spec["query_last"], referer)
        last_ym = ((last_resp.get("result") or {}).get("result") or [{}])[0].get("DATA_YEAR")
        rows: list[dict] = []
        for ym in filter(None, [last_ym, "202512", "202412"]):
            resp = self.query(spec["query_list"], referer, comp_type="", data_year=ym)
            batch = (resp.get("result") or {}).get("result") or []
            if batch:
                rows = batch
                break
        return {"table_id": spec["id"], "last_ym": last_ym, "row_count": len(rows), "rows": rows[:100]}

    def crawl_long_company_stattbl(self, target_year: str = "2024") -> dict:
        form = {"stattbl_id": KIDI_LONG_COMPANY_STATTBL, "insrnc_item_cmmn_code": "A01020"}
        detail = self._request("/insMonth/selMonthbookDetail.do", form)
        hidden = dict(re.findall(r'name="([^"]+)"[^>]*value="([^"]*)"', detail))
        payload = {**hidden, "stattbl_id": KIDI_LONG_COMPANY_STATTBL, "data_year": target_year}
        referer = BASE + "/insMonth/selMonthbookDetail.do"
        text = self._request("/insLong/selectStattblAjax.do", payload, ajax=True, referer=referer)
        obj = json.loads(text)
        rows = obj.get("resultJosn") or []
        years = sorted({str(r.get("col1")) for r in rows if r.get("col1")})
        return {
            "table_id": "long_company_20040",
            "target_year": target_year,
            "years_available": years,
            "row_count": len(rows),
            "rows": rows,
        }


def _parse_kidi_long_rows(rows: list[dict], alias_map: dict[str, str], target_year: str) -> dict[str, dict]:
    """Parse KIDI 20040 company rows — col2 often total premium (천원) for the year."""
    out: dict[str, dict] = {}
    for row in rows:
        if str(row.get("col1")) != str(target_year):
            continue
        raw_name = (row.get("str1") or "").strip()
        if not raw_name or raw_name in ("회사명", "합계") or "보험" in raw_name and len(raw_name) > 10:
            continue
        if not re.search(r"[\uac00-\ud7a3]", raw_name):
            continue
        company = resolve_company(raw_name, alias_map)
        if not company:
            continue
        # col2 = annual total 천원 (probe pattern for 삼성 row)
        raw_val = row.get("col2") or row.get("col3")
        if raw_val in (None, "", "0"):
            continue
        try:
            cheon = float(str(raw_val).replace(",", ""))
        except ValueError:
            continue
        # annual 천원 → monthly 억원: /100000/12
        eok_month = round(cheon / 100_000.0 / 12.0, 4)
        if eok_month <= 0:
            continue
        key = f"{company}|{target_year}"
        out[key] = {
            "company": company,
            "period": target_year,
            "wolnap_premium_eok_month": eok_month,
            "source": "kidi:stattbl_20040",
            "scope": "long_term_annual_total_over_12",
            "raw_cheonwon_annual": cheon,
        }
    return out


def _merge_ir_benchmarks(benchmarks: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for b in benchmarks:
        if b.get("wolnap_premium_eok_month") is None:
            continue
        company = b["company"]
        period = b.get("period") or "unknown"
        key = f"{company}|{period}"
        out[key] = {
            "company": company,
            "period": period,
            "wolnap_premium_eok_month": b["wolnap_premium_eok_month"],
            "wolnap_premium_sibeok_month": b.get("wolnap_premium_sibeok_month"),
            "source": b.get("source", "ir:benchmark"),
            "scope": b.get("scope"),
            "source_note": b.get("source_note"),
        }
    return out


def build_payload() -> dict:
    alias_map = load_alias_map()
    client = KidiClient()
    client.warm()

    kidi_ml02 = client.crawl_ml02()
    kidi_long = client.crawl_long_company_stattbl("2024")
    kidi_long_2019 = client.crawl_long_company_stattbl("2019")

    companies: dict[str, dict] = {}

    # overrides
    for name, ov in _load_yaml_companies(OVERRIDES_PATH).items():
        period = ov.get("period") or "override"
        key = f"{name}|{period}"
        companies[key] = {
            "company": name,
            "period": period,
            "wolnap_premium_eok_month": float(ov["wolnap_premium_eok"]),
            "source": ov.get("source") or "override:yaml",
            "scope": ov.get("scope"),
        }

    # IR benchmarks
    ir_payload = _load_json(IR_BENCH_PATH)
    companies.update(_merge_ir_benchmarks(ir_payload.get("benchmarks") or []))

    # KIDI long company table
    for year, block in [("2024", kidi_long), ("2019", kidi_long_2019)]:
        parsed = _parse_kidi_long_rows(block.get("rows") or [], alias_map, year)
        for key, row in parsed.items():
            if key not in companies:
                companies[key] = row

    kidi_numeric = any(
        r.get("wolnap_premium_eok_month") for r in companies.values() if r.get("source", "").startswith("kidi:")
    )

    return {
        "_meta": {
            "source": "KIDI INCOS + IR artifacts + overrides",
            "definition": "월납환산 신계약보험료 (monthly, 억원)",
            "crawled_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "build_script": "scripts/crawl_assoc_nb_premium.py",
            "ir_benchmarks_path": str(IR_BENCH_PATH.relative_to(ROOT)).replace("\\", "/"),
            "kidi_ml02_row_count": kidi_ml02.get("row_count"),
            "kidi_long_years": kidi_long.get("years_available"),
            "kidi_numeric_companies": kidi_numeric,
            "company_record_count": len(companies),
        },
        "kidi_raw": {"ml02": kidi_ml02, "long_2024": kidi_long, "long_2019": kidi_long_2019},
        "companies": companies,
    }


def main() -> int:
    payload = build_payload()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    TEMPLATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATES_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = payload["_meta"]
    print(f"Wrote {OUT_PATH}")
    print(f"  company_records={meta['company_record_count']} kidi_numeric={meta['kidi_numeric_companies']}")
    print(f"  kidi_ml02_rows={meta['kidi_ml02_row_count']} kidi_long_years={meta['kidi_long_years']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
