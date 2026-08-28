"""Verify the orchestrator's hand-check on KB손해보험 (KR0010) in the ticket
inbox/validation/20260829T1500Z: item16 is None every quarter and the bare form closes.

Read-only.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CO = "KB손해보험"


def norm(s: str) -> str:
    return (s or "").replace(" ", "")


def main() -> None:
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    idx = defaultdict(dict)
    for r in rows:
        if r["원수사명"] != CO:
            continue
        idx[r["공시분기"]][norm(r["항목명"])] = r["값"]

    print("%-9s %10s %10s %10s %10s %8s %10s %10s" %
          ("분기", "1보험손익", "2생명장기", "13자동차", "14일반", "15기타수", "16기타비", "bare-diff"))
    n16_none = 0
    for q in sorted(idx):
        m = idx[q]
        v = [m.get(k) for k in ("보험손익", "생명장기손익", "자동차손익",
                                "일반손익", "기타영업수익", "기타사업비용")]
        if v[5] is None:
            n16_none += 1
        d = "n/a"
        if None not in v[1:4] and v[0] is not None:
            d = "%+.1f" % (sum(v[1:4]) - v[0])
        print("%-9s %10s %10s %10s %10s %8s %10s %10s" % (
            q, *["None" if x is None else "%.1f" % x for x in v], d))
    print()
    print("quarters=%d, item16(기타사업비용) is None in %d of them" % (len(idx), n16_none))


if __name__ == "__main__":
    main()
