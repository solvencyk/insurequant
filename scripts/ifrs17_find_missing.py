# -*- coding: utf-8 -*-
"""Find OpenDART corp_name for K-ICS insurers that returned no_corp_match."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.opendart_client import OpenDARTClient  # noqa: E402


PROBES = {
    "AIG손해보험": ["AIG", "에이아이지", "AIG손해"],
    "IBK연금보험": ["IBK연금", "IBK", "연금보험"],
    "KB라이프생명": ["KB라이프", "라이프생명", "케이비라이프"],
    "코리안리재보험": ["코리안리", "Korean Re", "재보험"],
    # Sanity:
    "AIA생명보험": ["AIA"],
    "메트라이프생명보험": ["메트라이프"],
    "라이나생명보험": ["라이나"],
    "처브라이프생명보험": ["처브"],
    "비엔피파리바카디프생명보험": ["비엔피", "카디프", "BNP"],
    "악사손해보험": ["악사", "AXA"],
    "하나생명보험": ["하나생명"],
    "하나손해보험": ["하나손해"],
    "신한이지손해보험": ["신한이지", "신한 이지", "신한손해"],
    "카카오페이손해보험": ["카카오페이손해", "카카오페이"],
    "교보라이프플래닛생명보험": ["교보라이프플래닛", "라이프플래닛"],
    "아이엠라이프생명보험": ["아이엠라이프", "iM라이프", "아이엠"],
    "에이비엘생명보험": ["에이비엘", "ABL", "ABL생명"],
}


def main():
    client = OpenDARTClient.from_settings()
    for kics_name, queries in PROBES.items():
        print(f"\n=== {kics_name} ===")
        for q in queries:
            m = client.find_corp_codes_by_name(q)
            print(f"  [{q!r}] {len(m)} match(es):")
            for x in m[:5]:
                print(f"    {x['corp_code']}  {x['corp_name']!r}  stock={x['stock_code']!r}")


if __name__ == "__main__":
    main()
