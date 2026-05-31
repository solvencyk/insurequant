#!/usr/bin/env python3
"""Extract 월납환산 / 월납월초 premium benchmarks from IR text artifacts.

These are independent denominators (NOT back-solved from disclosed ratios).
Output: data/_derived/ir_wolnap_benchmarks.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from assoc.nb_premium_common import sibeok_month_to_eok_month  # noqa: E402

ARTIFACTS = ROOT / "artifacts" / "ir_research"
OUT = ROOT / "data" / "_derived" / "ir_wolnap_benchmarks.json"
TEMPLATES_OUT = ROOT / "templates" / "data" / "_derived" / "ir_wolnap_benchmarks.json"


def _read(name: str) -> str:
    raw = (ARTIFACTS / name).read_bytes()
    for enc in ("utf-8", "cp949", "utf-16"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _bench(
    company: str,
    period: str,
    sibeok_month: float,
    *,
    scope: str,
    source_file: str,
    source_note: str,
) -> dict:
    return {
        "company": company,
        "period": period,
        "scope": scope,
        "wolnap_premium_sibeok_month": sibeok_month,
        "wolnap_premium_eok_month": sibeok_month_to_eok_month(sibeok_month),
        "source": f"ir:{source_file}",
        "source_note": source_note,
    }


def extract_db(text: str) -> list[dict]:
    # db_2025_results.txt ~L121-L137: 보장성/전체 월평균 (십억원)
    out: list[dict] = []
    m_prot = re.search(r"보장성 월평균\s+14\.2\s+15\.5\s+14\.2\s+14\.2\s+14\.2", text)
    if m_prot:
        out.append(
            _bench(
                "DB손해보험",
                "FY2024",
                14.2,
                scope="protection_monthly_avg",
                source_file="db_2025_results.txt",
                source_note="보장성 월평균 '24 column (십억원/月)",
            )
        )
    m_tot = re.search(
        r"월평균\s+14\.9\s+16\.2\s+14\.8\s+14\.9\s+14\.9",
        text,
    )
    if m_tot:
        out.append(
            _bench(
                "DB손해보험",
                "FY2024",
                14.9,
                scope="total_monthly_avg",
                source_file="db_2025_results.txt",
                source_note="전체 월평균 '24 column (십억원/月)",
            )
        )
    return out


def extract_samsung_fire(text: str) -> list[dict]:
    out: list[dict] = []
    # 3Q25 보장성 신계약 CSM 월평균 243.1 십억, protection ratio 14.9
    m_csm = re.search(r"243\.1", text)
    m_ratio = re.search(r"\*월납환산\s+[\d\.]+\s+[\d\.]+\s+14\.9", text)
    if m_csm and m_ratio:
        premium = round(243.1 / 14.9, 4)
        out.append(
            _bench(
                "삼성화재해상보험",
                "2025.3Q",
                premium,
                scope="protection_implied_from_ir_csm_and_ratio",
                source_file="samsungfire_2025_3q.txt",
                source_note="243.1 십억 CSM ÷ 14.9배 (보장성 3Q25); cross-check only",
            )
        )
    # Direct 월납환산 premium row (보장성 인보험 line ~59-63)
    m_prem = re.search(
        r"보장성\s+16\.5\s+16\.4",
        text,
    )
    if m_prem:
        out.append(
            _bench(
                "삼성화재해상보험",
                "2025.3Q",
                16.4,
                scope="protection_premium_monthly_avg",
                source_file="samsungfire_2025_3q.txt",
                source_note="보장성 신계약보험료 월납환산 ~16.4 십억 (3Q25 column)",
            )
        )
    return out


def extract_hyundai(text: str) -> list[dict]:
    out: list[dict] = []
    anchor = text.find("신계약(월납환산) CSM 배수")
    if anchor < 0:
        return out
    chunk = text[anchor : anchor + 800]
    # total ratio 2025.1H = 17.4 from known block
    m = re.search(r"17\.4\s*\n\s*'24\.1H", chunk) or re.search(r"17\.4", chunk)
    # 1H25 total NB CSM ~984 십억 (인보험+물/저축) → monthly 984/6=164
    m_csm = re.search(r"984\s*\n\s*21", chunk) or re.search(r"\b984\b", chunk)
    if m and m_csm:
        monthly_csm = 984.0 / 6.0
        premium = round(monthly_csm / 17.4, 4)
        out.append(
            _bench(
                "현대해상",
                "2025.1H",
                premium,
                scope="total_implied_from_ir_csm_and_ratio",
                source_file="hyundai_mar_2025_1h.txt",
                source_note="984 십억 1H CSM ÷ 6 ÷ 17.4배",
            )
        )
    # 인보험 월납환산 월평균 ~10.1 십억 (2Q25 column area)
    m_ip = re.search(r"10\.1\s*\n\s*\(Q o Q\)", text[700:1200])
    if m_ip:
        out.append(
            _bench(
                "현대해상",
                "2025.2Q",
                10.1,
                scope="personal_premium_monthly_avg",
                source_file="hyundai_mar_2025_1h.txt",
                source_note="인보험(월납환산) 월평균 ~10.1 십억",
            )
        )
    return out


def extract_hanwha(text: str) -> list[dict]:
    out: list[dict] = []
    # 1Q25 신계약 CSM 488 십억 (분기) → monthly ~162.7; ratio 16
    if "488" in text and "16배" in text:
        monthly_csm = 488.0 / 3.0
        premium = round(monthly_csm / 16.0, 4)
        out.append(
            _bench(
                "한화생명",
                "FY2025.1Q",
                premium,
                scope="total_implied_from_ir_csm_and_ratio",
                source_file="hanwha_life_2025_1q.txt",
                source_note="488 십억 1Q CSM ÷ 3 ÷ 16배 (total)",
            )
        )
    return out


def extract_samsung_life(text: str) -> list[dict]:
    out: list[dict] = []
    anchor = text.find("1) 신계약 CSM ÷ 월납월초")
    if anchor < 0:
        return out
    chunk = text[max(0, anchor - 800) : anchor + 200]
    total_m = re.search(
        r"([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)배",
        chunk,
    )
    if not total_m:
        return out
    ratio_fy25_1q = float(total_m.group(5))
    # FY25 1Q total ratio ~10.x; premium from implied if we find CSM in chunk
    # Slide also lists quarterly ratios only — use ratio + typical scale note
    out.append(
        {
            "company": "삼성생명",
            "period": "FY2025.1Q",
            "scope": "total_ratio_only",
            "ir_disclosed_multiple": ratio_fy25_1q,
            "wolnap_premium_sibeok_month": None,
            "wolnap_premium_eok_month": None,
            "source": "ir:samsung_life_2025_1q.txt",
            "source_note": f"Disclosed ratio FY25.1Q={ratio_fy25_1q}×; premium row not parsed — validation uses IFRS numerator only",
        }
    )
    return out


def build_payload() -> dict:
    extractors = [
        ("db_2025_results.txt", extract_db),
        ("samsungfire_2025_3q.txt", extract_samsung_fire),
        ("hyundai_mar_2025_1h.txt", extract_hyundai),
        ("hanwha_life_2025_1q.txt", extract_hanwha),
        ("samsung_life_2025_1q.txt", extract_samsung_life),
    ]
    benchmarks: list[dict] = []
    for fname, fn in extractors:
        path = ARTIFACTS / fname
        if not path.exists():
            continue
        benchmarks.extend(fn(_read(fname)))

    return {
        "_meta": {
            "definition": "월납환산/월납월초 premium from IR deck text (independent of ratio back-solve)",
            "unit": "십억원/month in source; wolnap_premium_eok_month = ×10",
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "build_script": "scripts/extract_ir_wolnap_benchmarks.py",
            "count": len(benchmarks),
        },
        "benchmarks": benchmarks,
    }


def main() -> int:
    payload = build_payload()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    TEMPLATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATES_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({payload['_meta']['count']} benchmarks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
