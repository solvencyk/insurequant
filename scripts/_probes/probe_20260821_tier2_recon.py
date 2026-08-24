# -*- coding: utf-8 -*-
"""tier2 적재 후 검산: (a) 중복키 없음 (b) 보완자본=min(한도적용전,한도)+item49
(c) item2=item4-(item12-한도초과)-item13 (양 컬럼 다) 잔차 분포."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def _num(x):
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main() -> int:
    rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    by_cq: dict = {}
    dupe_check: dict = {}
    dupes = []
    for r in rows:
        c, q, it = r["원보험사코드"], r["공시분기"], int(r["항목번호"])
        key = (c, q, it)
        if key in dupe_check:
            dupes.append(key)
        dupe_check[key] = True
        by_cq.setdefault((c, q), {})[it] = r

    print(f"중복 (회사,분기,항목) 키 = {len(dupes)}")
    if dupes:
        print(dupes[:20])

    # (b) 보완자본 = min(47전,48전) + 49전  (전/후 둘다)
    b_checked, b_bad = 0, []
    for (c, q), items in by_cq.items():
        if 47 not in items or 48 not in items:
            continue
        r3, r47, r48 = items.get(3), items[47], items[48]
        r49 = items.get(49)
        if r3 is None:
            continue
        for col in ("값", "값_적용후"):
            v3 = _num(r3.get(col))
            v47 = _num(r47.get(col))
            v48 = _num(r48.get(col))
            v49 = _num((r49 or {}).get(col))
            if v3 is None or v47 is None or v48 is None or v49 is None:
                continue  # 49가 미검출이면 이 항등식은 검산 불가(0으로 대체 금지) — 스킵
            expect = min(v47, v48) + v49
            b_checked += 1
            if abs(v3 - expect) > 0.5:
                b_bad.append((c, q, col, v3, expect, v3 - expect))
    print(f"\n(b) 보완자본=min(47,48)+49 검산: {b_checked}건 중 잔차>0.5 = {len(b_bad)}건")
    tiny = sum(1 for *_x, d in b_bad if abs(d) <= 2.0)
    big = [r for r in b_bad if abs(r[-1]) > 2.0]
    print(f"    반올림급(|잔차|<=2.0억) {tiny}건  |  실질잔차(>2.0억) {len(big)}건")
    for row in big[:20]:
        print("   BIG", row)

    # (c) item2 = item4 - (item12 - max(0,47-48)) - item13
    c_checked, c_bad = 0, []
    for (c, q), items in by_cq.items():
        if 47 not in items or 48 not in items:
            continue
        r2, r4, r12, r13 = items.get(2), items.get(4), items.get(12), items.get(13)
        if r2 is None or r4 is None or r12 is None or r13 is None:
            continue
        r47, r48 = items[47], items[48]
        for col in ("값", "값_적용후"):
            v2 = _num(r2.get(col))
            v4 = _num(r4.get(col))
            v12 = _num(r12.get(col))
            v13 = _num(r13.get(col))
            v47 = _num(r47.get(col))
            v48 = _num(r48.get(col))
            if None in (v2, v4, v12, v13, v47, v48):
                continue
            excess = max(0.0, v47 - v48)
            expect = v4 - (v12 - excess) - v13
            c_checked += 1
            if abs(v2 - expect) > 1.0:
                c_bad.append((c, q, col, v2, expect, v2 - expect))
    print(f"\n(c) item2=item4-(item12-한도초과)-item13 검산: {c_checked}건 중 잔차>1.0 = {len(c_bad)}건")
    for row in c_bad[:20]:
        print("  ", row)
    if c_bad:
        agg = {}
        for cc, qq, col, *_r in c_bad:
            agg[(cc, col)] = agg.get((cc, col), 0) + 1
        print("  회사별 집계:", agg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
