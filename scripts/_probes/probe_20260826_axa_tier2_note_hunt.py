# -*- coding: utf-8 -*-
"""악사손해보험 2023.4Q 감사보고서에 PL Tier-2 노트가 정말 없는가 (validation, 2026-08-26).

오케스트레이터 티켓은 '어느 DART 문서에도 없다'고 단정했으나, 마커 census 는 2024.4Q(추출 성공)와
거의 같은 프로필을 보인다. 면제를 박기 전에 **표 자체를 눈으로 확인**한다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "2023.4Q(RED)": "data/dart/FY2023_Q4/raw/KR0049_악사손해보험_20240402002008/20240402002008_00760.xml",
    "2024.4Q(성공)": "data/dart/FY2024_Q4/raw/KR0049_악사손해보험_20250407003441/20250407003441_00760.xml",
}


def _text(p: Path) -> str:
    b = p.read_bytes()
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    raise SystemExit(f"decode fail {p}")


def main() -> None:
    needle = sys.argv[1] if len(sys.argv) > 1 else "보험계약마진 상각"
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 900
    for label, rel in FILES.items():
        p = ROOT / rel
        raw = _text(p)
        flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw))
        print(f"\n{'=' * 78}\n{label}  {p.name}  ({len(flat):,d}자)\n{'=' * 78}")
        for m in re.finditer(re.escape(needle), flat):
            s = max(0, m.start() - width // 3)
            print(f"\n--- @{m.start()}\n{flat[s:m.start() + width]}")


if __name__ == "__main__":
    main()
