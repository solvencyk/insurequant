"""Per-quarter dump of 코리안리재보험's 보험손익 closure, all 14 quarters that carry
the extra-LOB item "2-1", under both the current 3-leg equation and the proposed
3-leg + extra-LOB equation.  Written because the full-bucket simulation reported
only 12 verdict changes while the master carries 14 quarters of item "2-1" — the
other two must be accounted for explicitly rather than assumed benign.

Read-only.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FLOOR = 200.0
LOB_KEYS = ("생명장기손익", "자동차손익", "일반손익")
EXTRA_LOB_NO = re.compile(r"^2-\d+$")
CO = "코리안리재보험"


def norm(s: str) -> str:
    return (s or "").replace(" ", "")


def main() -> None:
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    pl: dict = defaultdict(dict)
    extra: dict = defaultdict(float)
    seen_extra: dict = defaultdict(list)
    for r in rows:
        if r["원수사명"] != CO:
            continue
        q = r["공시분기"]
        pl[q][norm(r["항목명"])] = r["값"]
        no = r.get("항목번호")
        if isinstance(no, str) and EXTRA_LOB_NO.match(no):
            seen_extra[q].append((no, r["값"]))
            if r["값"] is not None:
                extra[q] += r["값"]

    hdr = f"{'분기':<9s}{'item1':>12s}{'item2':>11s}{'13':>8s}{'14':>11s}{'2-1':>11s}{'15':>10s}{'16':>10s}{'diff(3leg)':>12s}{'diff(+2-1)':>12s}"
    print(hdr)
    print("-" * len(hdr))
    for q in sorted(pl):
        m = pl[q]
        bo = m.get("보험손익")
        raw = [m.get(k) for k in LOB_KEYS]
        bare = sum(0.0 if v is None else v for v in raw)
        oi, oe = m.get("기타영업수익"), m.get("기타사업비용")

        def best(b):
            cands = [b]
            if oi is not None and oe is not None:
                cands.append(b + oi - oe)
            return min((c - bo for c in cands), key=abs)

        ex = extra.get(q, 0.0)
        if bo is None:
            d3 = da = None
        else:
            d3, da = best(bare), best(bare + ex)

        def f(v, w=11):
            return ("None" if v is None else f"{v:,.1f}").rjust(w)

        print(f"{q:<9s}{f(bo,12)}{f(raw[0])}{f(raw[1],8)}{f(raw[2])}{f(ex if seen_extra.get(q) else None)}"
              f"{f(m.get('기타영업수익'),10)}{f(m.get('기타사업비용'),10)}{f(d3,12)}{f(da,12)}")

    print()
    print("quarters carrying item 2-N:", len(seen_extra))
    for q in sorted(seen_extra):
        bo = pl[q].get("보험손익")
        print(f"  {q}  2-N={seen_extra[q]}  item1={'None' if bo is None else f'{bo:,.1f}'}")


if __name__ == "__main__":
    main()
