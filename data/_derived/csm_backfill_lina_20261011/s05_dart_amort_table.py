# -*- coding: utf-8 -*-
"""Step 5 (read-only): print the TD cell text rows of the first expected-amortisation table (issued contracts) in the DART
FY2025 annual filings of KR0074 (separate 감사보고서 4538, consolidated 4539)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")

for rc in ["20260406004538", "20260406004539"]:
    d = ROOT / "data" / "dart" / "FY2025_Q4" / "raw" / f"KR0074_라이나생명보험_{rc}"
    text = next(d.glob("*.xml")).read_bytes().decode("utf-8", errors="replace")
    # first occurrence of the issued-contracts caption
    m = re.search(r"기대상각기간별 보험계약마진 금액은 다음과 같습니다\(단위:천원\)\.", text)
    start = m.start()
    seg = text[start: start + 60000]
    # cut at the next caption of the same kind (reinsurance held) if any
    nxt = re.search(r"보유하고 있는 출재보험계약의 기대상각기간별", seg)
    if nxt:
        seg = seg[: nxt.start()]
    rows = re.findall(r"<TR[^>]*>(.*?)</TR>", seg, flags=re.S)
    print("=====", rc, "rows", len(rows))
    for r in rows:
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<T[DHU][^>]*>(.*?)</T[DHU]>", r, flags=re.S)]
        print(" | ".join(cells))
