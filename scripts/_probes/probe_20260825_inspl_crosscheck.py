# -*- coding: utf-8 -*-
"""insurance_pl_breakdown.json ↔ PL_breakdown.json 교차대조 타당성 측정.

표 안의 `보험계약마진상각` 행 합계(마지막 숫자열)를 PL 마스터의 `원수CSM상각`(백만원, 연간)과
맞춰 본다. 파일이 어느 회계연도의 표인지 rcept_no 로 추정한다.

사용: python scripts/_probes/probe_20260825_inspl_crosscheck.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALIAS = {"미래에셋생명": "미래에셋생명보험", "삼성생명": "삼성생명보험",
         "코리안리": "코리안리재보험", "아이비케이연금보험": "IBK연금보험",
         "케이비라이프생명보험": "KB라이프생명", "에이아이지손해보험": "AIG손해보험",
         "엠지손해보험": "예별손해보험"}


def j(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _num(s):
    if s is None:
        return None
    s = str(s).strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "–", "—"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("△", "-").replace("▲", "-")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def main() -> int:
    p = j("data/dart/viz/insurance_pl_breakdown.json")
    pl = defaultdict(dict)
    for r in j("PL_breakdown.json"):
        pl[(r["원수사명"], r["공시분기"])][(r["항목명"] or "").replace(" ", "")] = r["값"]

    print(f"{'회사':22s} {'rcept':16s} {'FY추정':8s} {'표 CSM상각합계':>16s} "
          f"{'마스터 원수CSM상각':>18s} {'ratio':>8s}")
    print("-" * 100)
    n_hit = n_miss = 0
    for c in p["companies"]:
        co = ALIAS.get(c["company"], c["company"])
        rc = str(c.get("rcept_no") or "")
        fy = rc[:4] if len(rc) >= 4 else "?"
        # 사업보고서는 직전 사업연도 표 -> FY = rcept 연도 - 1
        try:
            q = f"{int(fy) - 1}.4Q"
        except ValueError:
            q = "?"
        val = None
        for row in (c.get("table") or []):
            if row and re.sub(r"\s+", "", str(row[0])) == "보험계약마진상각":
                nums = [_num(x) for x in row[1:]]
                nums = [x for x in nums if x is not None]
                if nums:
                    val = nums[-1]
                break
        m = pl.get((co, q), {}).get("원수CSM상각")
        r = (abs(val) / abs(m)) if (val and m) else None
        if val is not None and m is not None:
            n_hit += 1
        else:
            n_miss += 1
        f = lambda x: "-" if x is None else f"{x:,.1f}"
        print(f"{co:22s} {rc:16s} {q:8s} {f(val):>16s} {f(m):>18s} "
              f"{('-' if r is None else f'{r:.3f}'):>8s}")
    print(f"\n대조가능 {n_hit} / 불가 {n_miss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
