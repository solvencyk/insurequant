# -*- coding: utf-8 -*-
"""Verify the item48-zero scale-shortcut fix computes scale=0.01 for KR1098 2025.1Q
(replicates the relevant snippet of fix_20260821_tier2_limit_lines.main() for one cell)."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from fix_20260821_tier2_limit_lines import _pdf, q2p, extract_tier2, _trivial, _num  # noqa: E402

TARGET = REPO / "kics_disclosure.json"


def main():
    code, q = "KR1098", "2025.1Q"
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    m14_pre = m14_post = None
    for r in data:
        if r["원보험사코드"] == code and r["공시분기"] == q and int(r["항목번호"]) == 14:
            m14_pre, m14_post = _num(r.get("값")), _num(r.get("값_적용후"))

    pdf = _pdf(q2p(q), code)
    found, anchor, reason = extract_tier2(pdf)
    f47, f48, f49 = found.get(47), found.get(48), found.get(49)
    print(f"m14_pre={m14_pre}  found={found}  anchor={anchor}")

    scale = None
    if (f48 is not None and f48[0] is not None and abs(f48[0]) < 0.005
            and _trivial(f47) and _trivial(f49)):
        scale = 1.0
    elif f48 is not None and f48[0] is not None and abs(f48[0]) >= 0.005 and m14_pre:
        expect48 = m14_pre * 0.5
        if expect48:
            ratio = f48[0] / expect48
            if 0.98 < ratio < 1.02:
                scale = 1.0
            elif 98 < ratio < 102:
                scale = 0.01
    if scale is None and anchor is not None and anchor[0] and m14_pre:
        ratio2 = anchor[0] / m14_pre
        print(f"  anchor ratio vs item14_pre = {ratio2}")
        if 0.98 < ratio2 < 1.02:
            scale = 1.0
        elif 98 < ratio2 < 102:
            scale = 0.01

    print(f"resolved scale = {scale}")
    if scale is not None:
        print(f"item47 corrected = {tuple(round(v*scale,2) if v is not None else None for v in f47)}")
        print(f"item48 corrected = {tuple(round(v*scale,2) if v is not None else None for v in f48)}")
        print(f"item49 corrected = {tuple(round(v*scale,2) if v is not None else None for v in f49)}")


if __name__ == "__main__":
    raise SystemExit(main())
