# -*- coding: utf-8 -*-
"""Batch diagnostic: for a list of (code, quarter), dump BOTH the TFI table
(1)공통적용경과조치 raw pre/post rows AND the master's core(2,3,4,12,13,14)+tier2(47,48,49)
values side by side, plus the bridge/composition formula check -- to classify each
RED cell fast without re-deriving the methodology per company.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from fix_20260821_tier2_limit_lines import _pdf, q2p, extract_tier2  # noqa: E402
# (import above rewraps stdout to utf-8)

TARGET = REPO / "kics_disclosure.json"

CASES = [
    ("KR0072", "2024.3Q"), ("KR0072", "2024.4Q"), ("KR0072", "2025.1Q"), ("KR0072", "2025.2Q"),
    ("KR0076", "2024.4Q"),
    ("KR0003", "2023.1Q"), ("KR0003", "2024.4Q"), ("KR0003", "2025.1Q"), ("KR0003", "2026.1Q"),
    ("KR0075", "2024.3Q"), ("KR0075", "2024.4Q"), ("KR0075", "2025.1Q"),
    ("KR0080", "2023.2Q"),
    ("KR1098", "2025.1Q"),
    ("KR0073", "2024.4Q"),
    ("KR0087", "2026.1Q"),
]


def main():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    by_cq: dict[tuple, dict] = {}
    for r in data:
        key = (r["원보험사코드"], r["공시분기"])
        by_cq.setdefault(key, {})[int(r["항목번호"])] = r

    for code, q in CASES:
        print(f"\n########## {code} {q} ##########")
        items = by_cq.get((code, q), {})
        for it in (1, 2, 3, 4, 12, 13, 14, 47, 48, 49):
            r = items.get(it)
            if r is None:
                print(f"  item{it:>2}: (마스터에 없음)")
            else:
                print(f"  item{it:>2} {r.get('항목명',''):<12} 값={r.get('값')!s:>12} 값_적용후={r.get('값_적용후')!s:>12}")

        pdf = _pdf(q2p(q), code)
        if pdf is None:
            print("  [TFI raw] PDF 없음")
            continue
        found, anchor, reason = extract_tier2(pdf)
        print(f"  [TFI raw 47/48/49 as found by extract_tier2] found={found} anchor={anchor} reason={reason}")


if __name__ == "__main__":
    raise SystemExit(main())
