# -*- coding: utf-8 -*-
"""사각 12버킷의 **원천에 Tier-2 노트가 실제로 있는가** 를 회사별로 확인 (validation, 2026-08-26).

카테고리('비상장이라 감사보고서만')로 단정하지 않기 위한 실측이다. 같은 회사의 성공 분기와
실패 분기를 나란히 재서, 마커가 양쪽 다 있으면 파서 구멍 / 실패 쪽에만 없으면 원천 부재로 가른다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_master_tables import load_long  # noqa: E402

# PL Tier-2(계약유형별 보험수익/보험서비스비용 분석) 를 특정하는 마커.
# '보험계약마진상각' 은 표 안 행 라벨, '계약유형별'/'유형별 분석' 은 표 캡션 계열.
MARKERS = ["계약유형별", "유형별", "보험계약마진", "보험계약마진 상각", "보험수익",
           "보험서비스비용", "예상손해", "위험조정"]

CASES = [
    # (라벨, 회사명, 분기, raw 디렉터리)
    ("AIA 2023.4Q [사각]", "에이아이에이생명보험", "2023.4Q",
     "data/dart/FY2023_Q4/raw/KR0080_에이아이에이생명보험_20240409002583"),
    ("AIA 2024.4Q [사각]", "에이아이에이생명보험", "2024.4Q",
     "data/dart/FY2024_Q4/raw/KR0080_에이아이에이생명보험_20250401000094"),
    ("AIA 2025.4Q [PL 有]", "에이아이에이생명보험", "2025.4Q",
     "data/dart/FY2025_Q4/raw"),
    ("아이엠라이프 2024.4Q [사각]", "아이엠라이프생명보험", "2024.4Q",
     "data/dart/FY2024_Q4/raw/KR0076_아이엠라이프생명보험_20250404003437"),
    ("아이엠라이프 2025.4Q [사각]", "아이엠라이프생명보험", "2025.4Q",
     "data/dart/FY2025_Q4/raw/KR0076_아이엠라이프생명보험_20260406004393"),
    ("하나손해 2023.4Q [사각]", "하나손해보험", "2023.4Q",
     "data/dart/FY2023_Q4/raw"),
    ("하나손해 2024.4Q [사각]", "하나손해보험", "2024.4Q",
     "data/dart/FY2024_Q4/raw"),
    ("하나손해 2025.4Q [사각]", "하나손해보험", "2025.4Q",
     "data/dart/FY2025_Q4/raw/KR0050_하나손해보험_20260325000538"),
    ("교보라플 2023.4Q [사각]", "교보라이프플래닛생명보험", "2023.4Q",
     "data/dart/FY2023_Q4/raw"),
    ("교보라플 2024.4Q [PL 有]", "교보라이프플래닛생명보험", "2024.4Q",
     "data/dart/FY2024_Q4/raw"),
    ("악사 2023.4Q [RED]", "악사손해보험", "2023.4Q",
     "data/dart/FY2023_Q4/raw/KR0049_악사손해보험_20240402002008"),
    ("악사 2024.4Q [PL 有]", "악사손해보험", "2024.4Q",
     "data/dart/FY2024_Q4/raw/KR0049_악사손해보험_20250407003441"),
]

PREFIX = {"에이아이에이생명보험": "KR0080", "아이엠라이프생명보험": "KR0076",
          "하나손해보험": "KR0050", "교보라이프플래닛생명보험": "KR1010",
          "악사손해보험": "KR0049"}


def _text(p: Path) -> str:
    b = p.read_bytes()
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return re.sub(r"<[^>]+>", " ", b.decode(enc))
        except Exception:
            continue
    return ""


def main() -> None:
    pl = load_long("PL_breakdown.json")
    wf = load_long("CSM_waterfall.json")
    for label, co, q, d in CASES:
        p = ROOT / d
        pre = PREFIX[co]
        if p.is_dir() and p.name == "raw":
            xmls = sorted(x for sub in p.glob(f"{pre}_*") for x in sub.rglob("*.xml"))
        else:
            xmls = sorted(p.rglob("*.xml")) if p.exists() else []
        m = pl.get((co, q)) or {}
        w = wf.get((co, q)) or {}
        print(f"\n=== {label}")
        print(f"    PL bucket={'YES' if (co, q) in pl else 'NO':3s} "
              f"원수CSM상각={m.get('원수CSM상각')!s:>14s}  WF상각={w.get('CSM상각')!s}")
        if not xmls:
            print(f"    raw XML 없음: {d}")
            continue
        for x in xmls:
            t = _text(x)
            if not t:
                print(f"    {x.name}: decode fail")
                continue
            hits = "  ".join(f"{k}={t.count(k)}" for k in MARKERS)
            print(f"    {x.name:38s} {len(t):9,d}자  {hits}")


if __name__ == "__main__":
    main()
