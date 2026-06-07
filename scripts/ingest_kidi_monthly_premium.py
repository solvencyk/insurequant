#!/usr/bin/env python3
"""KIDI INCOS monthly premium ingest -- 28사 × YTD quarter-ends.

Endpoint: POST https://incos.kidi.or.kr:5443/insMonth/getQueryResult.do
  queryId=getML01List (생보 원수보험료 현황) | getMN07List (손보 장기 원수보험료 현황)
  comp_type=<L## or N##>   data_year=YYYYMM   -> top-row aggregate cumulative YTD.

Top row (LINE=47 for ML01, LINE=99111 for MN07):
  ITEM_VAL2 = 일시납 초회 금액 (천원)  -- excluded from NB CSM denominator
  ITEM_VAL4 = 월납 초회 금액 (천원)    -- included
  ITEM_VAL8 = 기타 초회 금액 (천원)    -- included
  분모(억원) = (ITEM_VAL4 + ITEM_VAL8) / 100_000

User decisions (2026-05-30):
  - Excluded: 일시납 (저축성 일시납 mostly; not NB CSM source).
  - Included: 월납 초회 + 기타 초회.
  - Cardinality: 28-co (23 listed + 5 foreign-affiliate). 2023.1Q ~ 2026.1Q quarter-ends
    (KIDI updates 2026.1Q in April 2026; missing periods are honest gaps).

Output:
  data/kidi/FY<year>_Q<q>/raw/<KR>_<YYYYMM>.json  -- raw response per (insurer, period)
  data/kidi/premium_summary.json                   -- aggregated index keyed by KR_code+period
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Reuse the existing session/cookie/SSL wrapper.
from scripts.crawl_assoc_nb_premium import KidiClient, BASE  # noqa: E402

OUT_DIR = ROOT / "data" / "kidi"

# KR code -> (KIDI cbCmp code, table name).
# Mapping from user-provided cbCmp <select> options. Legacy/inactive entries
# (제일, 리젠트, 한화제일합병, ING, 푸르덴셜, 페더럴, R&SA, MG, 현대하이카다이렉트,
#  스위스리, 뮌헨리, 알리안츠 etc.) are omitted -- they are either delisted or
# absorbed into successors already covered.
MAPPING: dict[str, tuple[str, str]] = {
    # === 생보 (ML01) ===
    "KR0068": ("L01", "ML01"),   # 한화생명
    "KR0070": ("L02", "ML01"),   # 에이비엘생명보험 (ABL)
    "KR0069": ("L03", "ML01"),   # 삼성생명보험
    "KR0071": ("L04", "ML01"),   # 흥국생명보험
    "KR0073": ("L05", "ML01"),   # 교보생명보험
    "KR0094": ("L11", "ML01"),   # 신한라이프생명보험
    "KR0083": ("L12", "ML01"),   # 푸본현대생명보험
    "KR0076": ("L31", "ML01"),   # 아이엠라이프 (구 DGB생명)
    "KR0072": ("L33", "ML01"),   # 케이디비생명보험 (KDB)
    "KR0079": ("L34", "ML01"),   # 미래에셋생명보험
    "KR0099": ("L39", "ML01"),   # KB라이프생명 (구 푸르덴셜 L61 합병)
    "KR0074": ("L51", "ML01"),   # 라이나생명보험 (audit-only)
    "KR0097": ("L63", "ML01"),   # 하나생명보험 (audit-only)
    "KR0082": ("L71", "ML01"),   # DB생명보험
    "KR0095": ("L72", "ML01"),   # 메트라이프생명보험 (audit-only)
    "KR0087": ("L74", "ML01"),   # 동양생명
    "KR0100": ("L77", "ML01"),   # 처브라이프 (구 ACE Life, audit-only)
    "KR0075": ("L78", "ML01"),   # 비엔피파리바카디프
    "KR1011": ("L79", "ML01"),   # IBK연금보험
    "KR0104": ("L80", "ML01"),   # 농협생명보험
    "KR1010": ("L86", "ML01"),   # 교보라이프플래닛
    # AIA (audit-only, not in kics_disclosure) -> L52
    "AIA":    ("L52", "ML01"),   # 에이아이에이생명보험
    # === 손보 장기 (MN07) ===
    "KR0001": ("N01", "MN07"),   # 메리츠화재해상보험
    "KR0002": ("N02", "MN07"),   # 한화손해보험
    "KR0003": ("N03", "MN07"),   # 롯데손해보험
    "KR0004": ("N04", "MN07"),   # 예별손해보험 (cbCmp label still "MG"; 사명변경 후에도 코드 유지)
    "KR0005": ("N05", "MN07"),   # 흥국화재
    "KR0008": ("N08", "MN07"),   # 삼성화재해상보험
    "KR0009": ("N09", "MN07"),   # 현대해상
    "KR0010": ("N10", "MN07"),   # KB손해보험
    "KR0011": ("N11", "MN07"),   # DB손해보험
    "KR1000": ("N13", "MN07"),   # 코리안리재보험 (재보험사; 장기손보 거의 없음)
    "KR0049": ("N16", "MN07"),   # 악사손해보험
    "KR0050": ("N42", "MN07"),   # 하나손해보험
    "KR0051": ("N43", "MN07"),   # 신한이지손해보험
    "KR0029": ("N51", "MN07"),   # AIG손해보험 (excluded from K-ICS universe)
    "KR0032": ("N71", "MN07"),   # NH농협손해보험
    "KR1098": ("N80", "MN07"),   # 카카오페이손해보험
    # 캐롯 (KR1059, N76) not in kics_disclosure -- include for completeness.
    "KR1059": ("N76", "MN07"),   # 캐롯손해보험
}

# Default quarter-ends to ingest (2023.1Q ~ 2026.1Q).
DEFAULT_PERIODS = [
    "202303", "202306", "202309", "202312",
    "202403", "202406", "202409", "202412",
    "202503", "202506", "202509", "202512",
    "202603",
]


def fetch_one(client: KidiClient, table: str, comp_type: str, data_year: str) -> dict:
    referer = BASE + f"/insMonth/detail/{table}.do?stattbl_id={table}"
    return client.query(
        f"get{table}List", referer, comp_type=comp_type, data_year=data_year
    )


def top_row(rows: list[dict], table: str) -> dict | None:
    """Pick the top aggregate row.

    ML01: LVL=1 / LINE=47 / ITEM_NM=합계 / etc. -- first row is reliably the topline.
    MN07: LVL=2 / LINE=99111 / ITEM_NM=원리금보장형장기손해보험 합계 -- also first row.
    """
    if not rows:
        return None
    return rows[0]


def summarize(row: dict | None) -> dict:
    if not row:
        return {
            "single_premium_cheonwon": None,
            "month_premium_cheonwon": None,
            "etc_premium_cheonwon": None,
            "denominator_eok": None,
        }
    v2 = float(row.get("ITEM_VAL2") or 0)
    v4 = float(row.get("ITEM_VAL4") or 0)
    v8 = float(row.get("ITEM_VAL8") or 0)
    return {
        "label": row.get("ITEM_NM"),
        "line": row.get("LINE"),
        "level": row.get("LVL"),
        "single_premium_cheonwon": v2,
        "month_premium_cheonwon": v4,
        "etc_premium_cheonwon": v8,
        "denominator_cheonwon": v4 + v8,
        "denominator_eok": round((v4 + v8) / 100_000.0, 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--insurers", nargs="*",
        help="Restrict to specific KR codes (default = all in MAPPING).",
    )
    parser.add_argument(
        "--periods", nargs="*",
        help=f"Restrict to specific YYYYMM (default = {DEFAULT_PERIODS}).",
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="Smoke test: KR0008 + KR0069 × 202512 only, validate sample numbers.",
    )
    args = parser.parse_args()

    if args.smoke:
        insurers = ["KR0008", "KR0069"]
        periods = ["202512"]
    else:
        insurers = args.insurers or list(MAPPING)
        periods = args.periods or DEFAULT_PERIODS

    unknown = [i for i in insurers if i not in MAPPING]
    if unknown:
        print(f"WARN: unknown KR codes: {unknown}", file=sys.stderr)
        insurers = [i for i in insurers if i in MAPPING]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Canonical layout per source: data/kidi/FY<year>_Q<q>/raw/KR####_<YYYYMM>.json
    # (yyyymm month 03/06/09/12 -> Q1/Q2/Q3/Q4)
    _Q_BY_MONTH = {"03": 1, "06": 2, "09": 3, "12": 4}

    def period_dir_for(yyyymm: str) -> Path:
        year, mm = yyyymm[:4], yyyymm[4:]
        q = _Q_BY_MONTH.get(mm)
        if q is None:
            raise ValueError(f"unexpected month in {yyyymm}; only quarter-ends 03/06/09/12 supported")
        return OUT_DIR / f"FY{year}_Q{q}" / "raw"

    client = KidiClient()
    client.warm()

    entries: dict[str, dict] = {}
    errors: list[dict] = []

    total = len(insurers) * len(periods)
    print(f"[ingest] {len(insurers)} insurer(s) × {len(periods)} period(s) = {total} fetch", flush=True)

    n = 0
    for kr in insurers:
        comp_type, table = MAPPING[kr]
        for ym in periods:
            n += 1
            try:
                resp = fetch_one(client, table, comp_type, ym)
            except Exception as exc:  # noqa: BLE001
                print(f"  [{n}/{total}] {kr} {ym} ERROR {exc}", flush=True)
                errors.append({"kr": kr, "period": ym, "error": str(exc)})
                continue
            rows = ((resp.get("result") or {}).get("result")) or []
            top = top_row(rows, table)
            summary = summarize(top)

            key = f"{kr}|{ym}"
            entries[key] = {
                "kr_code": kr,
                "kidi_code": comp_type,
                "table": table,
                "period_yyyymm": ym,
                "row_count": len(rows),
                **summary,
            }
            raw_dir = period_dir_for(ym)
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_path = raw_dir / f"{kr}_{ym}.json"
            raw_path.write_text(
                json.dumps(resp, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            deno = summary["denominator_eok"]
            print(f"  [{n}/{total}] {kr} {ym} rows={len(rows)} 분모={deno}억", flush=True)

    summary_path = OUT_DIR / "premium_summary.json"
    payload = {
        "_meta": {
            "source": "KIDI INCOS getML01List + getMN07List",
            "endpoint": BASE + "/insMonth/getQueryResult.do",
            "stamp_utc": stamp,
            "insurer_count": len(insurers),
            "period_count": len(periods),
            "ok_count": len(entries),
            "error_count": len(errors),
            "definition": "denominator = ITEM_VAL4 (월납 초회) + ITEM_VAL8 (기타 초회), 일시납 제외",
            "unit": "cheonwon (raw) / 억원 (denominator_eok)",
        },
        "entries": entries,
        "errors": errors,
    }
    summary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ingest] wrote {summary_path} (entries={len(entries)} errors={len(errors)})")

    # Smoke validation
    if args.smoke:
        expect = {
            "KR0008|202512": {"v4": 215_799_013.0, "v8": 4_286_738.0},
            "KR0069|202512": {"v4": 278_913_166.174, "v8": 33_858_093.579},
        }
        bad = []
        for key, want in expect.items():
            got = entries.get(key) or {}
            v4 = got.get("month_premium_cheonwon")
            v8 = got.get("etc_premium_cheonwon")
            if abs((v4 or 0) - want["v4"]) > 0.5 or abs((v8 or 0) - want["v8"]) > 0.5:
                bad.append((key, want, {"v4": v4, "v8": v8}))
        if bad:
            print("[smoke] FAIL:", bad)
            return 2
        print("[smoke] OK -- sample numbers match user-provided values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
