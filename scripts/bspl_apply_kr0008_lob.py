#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17, inbox/parser/20261011T1130Z item A1): re-verify the Samsung Fire (KR0008) LOB legs of PL items 2/13/14
from the DART 'YYYY 보험종목별 영업규모, 영업실적' table for every quarter, against the master (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_kr0008_lob.py

Leg = sum over the table's insurance-type rows of (보험수익 - 보험서비스비용) + (재보험수익 - 재보험서비스비용) in 백만원:
  장기손해보험 rows -> item 2 (생명장기 손익), 자동차 row -> item 13, other 일반손해보험 rows -> item 14.   The '합계' row must equal the sum.
Prints the recomputed legs next to the master legs per quarter (YTD).
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


def num(c):
    t = re.sub(r"[\s\u3000\xa0]+", "", str(c))
    if t in ("", "-"):
        return 0
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def legs_of(xml: Path):
    for t in _iter_tables_with_context(xml):
        cap = re.sub(r"\s+", "", t.caption or "")
        hdr = " ".join(" ".join(h) for h in (t.header or []))
        if "보험종목별영업규모" not in cap or "당기" not in cap:
            continue
        if not all(k in hdr for k in ("보험수익", "보험서비스비용", "재보험수익", "재보험서비스비용")):
            continue
        sect = None
        out = {"장기": 0.0, "자동차": 0.0, "일반": 0.0}
        total = None
        for r in t.rows:
            cells = [str(c) for c in r]
            lab = re.sub(r"\s+", "", cells[0])
            nums = [num(c) for c in cells[1:]]
            if lab in ("일반손해보험", "장기손해보험"):
                sect = lab
                cells = cells[1:]
                lab = re.sub(r"\s+", "", cells[0])
                nums = [num(c) for c in cells[1:]]
            nums = [n for n in nums if n is not None]
            if lab == "합계":
                total = (nums[0] - nums[1]) + (nums[2] - nums[3]) if len(nums) >= 4 else None
                continue
            if len(nums) < 4:
                continue
            v = (nums[0] - nums[1]) + (nums[2] - nums[3])
            if sect == "장기손해보험" or (sect is None and lab == "장기"):
                out["장기"] += v
            elif lab == "자동차":
                out["자동차"] += v
            else:
                out["일반"] += v
        return out, total, t.line_no
    return None, None, None


def main():
    pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    mv = {(r["항목번호"], r["공시분기"]): r["값"] for r in pl if r["원보험사코드"] == "KR0008"}
    print(f"{'quarter':<8} {'file':<22} | {'item2 recomputed':>18} {'master':>12} | {'item13 recomp':>14} {'master':>12} | {'item14 recomp':>14} {'master':>12} | total-check")
    for y in (2023, 2024, 2025, 2026):
        for n in (1, 2, 3):
            q = f"{y}.{n}Q"
            base = ROOT / "data" / "dart" / f"FY{y}_Q{n}" / "raw"
            files = sorted(base.glob("KR0008_*/*.xml")) + sorted(base.glob("KR0008_*/xml/*.xml"))
            if not files:
                continue
            res = None
            for f in files:
                res = legs_of(f)
                if res[0] is not None:
                    break
            if res is None or res[0] is None:
                print(f"{q:<8} (no '보험종목별 영업규모' table)  master 2/13/14 = {mv.get((2, q))}/{mv.get((13, q))}/{mv.get((14, q))}")
                continue
            out, total, ln = res
            chk = "OK" if total is not None and abs(sum(out.values()) - total) < 1.5 else f"MISMATCH sum {sum(out.values())} vs 합계 {total}"
            print(f"{q:<8} {f.name:<22} | {out['장기']:>18,.0f} {mv.get((2, q)) or 0:>12,.0f} | {out['자동차']:>14,.0f} {mv.get((13, q)) or 0:>12,.0f} | "
                  f"{out['일반']:>14,.0f} {mv.get((14, q)) or 0:>12,.0f} | {chk} (line {ln})")


if __name__ == "__main__":
    main()
