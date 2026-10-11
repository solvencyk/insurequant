#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 6: Samsung Fire (KR0008) 보험손익 by LOB recomputed from the DART body XML's
'보험종목별 영업규모, 영업실적' table (보험수익 / 보험서비스비용 / 재보험수익 / 재보험서비스비용 per 보험종목), compared with the PL master legs
(items 2 / 13 / 14).  Read-only.  Method validation: the same recomputation must reproduce the master legs in the quarters that close.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_kr0008_lob.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

QS = {"2023.1Q": "FY2023_Q1", "2023.2Q": "FY2023_Q2", "2023.3Q": "FY2023_Q3"}


def num(s):
    s = str(s).strip().replace(",", "")
    if s in ("", "-"):
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def lob_totals(xml: Path):
    for t in _iter_tables_with_context(xml):
        cap = t.caption or ""
        if "영업규모, 영업실적" not in cap or "당기" not in cap:
            continue
        hdr = " ".join(str(c) for r in (t.header or []) for c in r)
        if "보험수익" not in hdr or "재보험서비스비용" not in hdr:
            continue
        tot = {"일반": 0.0, "자동차": 0.0, "장기": 0.0}
        sect = None
        rows = []
        for r in t.rows:
            cells = [str(c).strip() for c in r]
            if len(cells) < 5:
                continue
            nums = [num(c) for c in cells[-4:]]
            if any(n is None for n in nums):
                continue
            lab = cells[0] if len(cells) == 5 else cells[0] + "/" + cells[1]
            head = cells[0]
            if head in ("일반손해보험",):
                sect = "일반"
            elif head in ("장기손해보험",):
                sect = "장기"
            elif head == "합계":
                total = nums
                continue
            name = cells[1] if len(cells) == 6 else cells[0]
            if name == "자동차":
                key = "자동차"
            else:
                key = sect
            if key is None:
                continue
            res = nums[0] - nums[1] + nums[2] - nums[3]
            tot[key] += res
            rows.append((lab, key, res))
        return tot, total, rows, t.line_no
    return None


def main():
    pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    master = {}
    for r in pl:
        if r["원보험사코드"] == "KR0008":
            master[(str(r["항목번호"]), r["공시분기"])] = r["값"]
    out = {}
    for q, fy in QS.items():
        d = ROOT / "data" / "dart" / fy / "raw" / "KR0008_삼성화재해상보험"
        xmls = sorted(p for p in d.glob("*.xml"))
        if not xmls:
            print(q, "no xml")
            continue
        got = None
        for x in xmls:
            got = lob_totals(x)
            if got:
                break
        if not got:
            print(q, "영업실적 table not found in", [p.name for p in xmls])
            continue
        tot, total, rows, line_no = got
        m2, m13, m14 = (master.get((k, q)) for k in ("2", "13", "14"))
        out[q] = {"table_line": line_no, "장기": tot["장기"], "자동차": tot["자동차"], "일반": tot["일반"], "합계_표": total, "master_2": m2, "master_13": m13, "master_14": m14}
        print(f"{q} (xml {xmls[0].name} table@{line_no}): 장기 {tot['장기']:,.0f} (master {m2}) | 자동차 {tot['자동차']:,.0f} (master {m13}) | 일반 {tot['일반']:,.0f} (master {m14}) | 합계표 "
              f"{(total[0] - total[1] + total[2] - total[3]):,.0f} vs 세 레그 합 {tot['장기'] + tot['자동차'] + tot['일반']:,.0f}")
    (ROOT / "data" / "_derived" / "bspl_followup_20261011" / "kr0008_lob_recompute.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
