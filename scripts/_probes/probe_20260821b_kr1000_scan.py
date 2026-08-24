# -*- coding: utf-8 -*-
"""Scan every KR1000 (코리안리) quarter: dump item2/3 pre vs post from master, and
extract_tier2's raw findings, to see how far the pre==post(mirrored) pattern extends."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from fix_20260821_tier2_limit_lines import extract_tier2, _pdf, q2p  # noqa: E402
# (import rewraps stdout as utf-8)

TARGET = REPO / "kics_disclosure.json"


def main():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    rows = [r for r in data if r["원보험사코드"] == "KR1000"]
    by_q: dict[str, dict] = {}
    for r in rows:
        by_q.setdefault(r["공시분기"], {})[int(r["항목번호"])] = r
    for q in sorted(by_q):
        items = by_q[q]
        i2 = items.get(2, {})
        i3 = items.get(3, {})
        i4 = items.get(4, {})
        pdf = _pdf(q2p(q), "KR1000")
        raw47 = raw48 = raw49 = None
        if pdf:
            found, anchor, reason = extract_tier2(pdf)
            raw47, raw48, raw49 = found.get(47), found.get(48), found.get(49)
        print(f"{q}: item2(값={i2.get('값')!s:>8}, 후={i2.get('값_적용후')!s:>10})  "
              f"item3(값={i3.get('값')!s:>8}, 후={i3.get('값_적용후')!s:>10})  "
              f"item4(값={i4.get('값')!s:>8})  raw47={raw47}  raw48={raw48}  raw49={raw49}")


if __name__ == "__main__":
    raise SystemExit(main())
