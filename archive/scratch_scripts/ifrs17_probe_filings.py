# -*- coding: utf-8 -*-
"""For companies marked no_annual_filing, list every disclosure in 2025
to see what they actually publish (감사보고서·반기·분기 etc.)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.opendart_client import OpenDARTClient  # noqa: E402


COMPANIES = {
    "교보라이프플래닛생명보험": "교보라이프플래닛생명보험",
    "라이나생명보험": "라이나생명보험",
    "메트라이프생명보험": "메트라이프생명보험",
    "비엔피파리바카디프생명보험": "비엔피파리바카디프생명보험",
    "신한이지손해보험": "신한이지손해보험",
    "아이엠라이프생명보험": "아이엠라이프생명보험",
    "악사손해보험": "악사손해보험",
    "처브라이프생명보험": "처브라이프생명보험",
    "카카오페이손해보험": "카카오페이손해보험",
    "하나생명보험": "하나생명보험",
    "하나손해보험": "하나손해보험",
    "IBK연금보험": "아이비케이연금보험",
}


def main():
    client = OpenDARTClient.from_settings()
    for k, q in COMPANIES.items():
        print(f"\n=== {k} (query={q!r}) ===")
        matches = client.find_corp_codes_by_name(q)
        if not matches:
            print("  no match")
            continue
        exact = [m for m in matches if m["corp_name"] == q]
        chosen = (exact or matches)[0]
        cc = chosen["corp_code"]
        print(f"  corp_code={cc}  name={chosen['corp_name']!r}")
        # All periodic disclosures in 2025
        filings = client.list_filings(cc, "20250101", "20250601")
        for f in filings[:8]:
            print(f"    {f.get('rcept_dt')}  {f.get('report_nm')}  rcept={f.get('rcept_no')}")
        # Also fetch annual reports from 2024 in case they file late.
        late = client.list_filings(cc, "20240601", "20250101")
        for f in late[:3]:
            print(f"    [2024]  {f.get('rcept_dt')}  {f.get('report_nm')}")


if __name__ == "__main__":
    main()
