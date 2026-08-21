# -*- coding: utf-8 -*-
"""AIA(KR0080) 2023.3Q core headline cluster -- discovered as a side effect of the
adversarial-reverification item19 fix (`fix_20260821_adversarial_reverification.py`).

That fix corrected item19(시장위험액) 3643->3779 using 3 independent raw citations
(headline p9, ②표 p11, ③표 p12, all agreeing). Re-running the gate afterward surfaced
2 NEW REDs (rule4, rule6) for this same (company,quarter) that were not there before --
because item19=3643 had been *self-consistent* with an entire cluster of other wrong
headline cells (items 1,2,3,14,15,16,20,22,27,28), which had silently reconciled with
EACH OTHER (via R1/R4/R5/R6) using the wrong numbers, hiding the fact that none of them
matched the actual filing. Fixing item19 alone broke that false internal consistency.

Raw citations (data/disclosure/FY2023_Q3/raw/KR0080_에이아이에이생명보험.pdf), all for
the "해당 분기(23.3Q)" column, cross-verified via both fitz plain text and pdfplumber
word-position reconstruction (identical reading both ways -- no column-order ambiguity):
  p8  [지급여력비율 총괄]: 경과조치 전 == 경과조치 후 in every field this quarter
      (234.0 / 34,896 / 14,914 both rows) -- this company applies NO transitional
      measure at all in 2023.3Q, so 전=후 mirror throughout is correct.
  p9  [경과조치 적용 전 지급여력비율 세부] (억원):
      가.지급여력금액 34,896 / 기본자본 29,340 / 보완자본 5,556 /
      나.지급여력기준금액 14,914 / Ⅰ.기본요구자본 19,344 / 분산효과 3,381 /
      생명장기 16,785(already correct in master) / 시장위험액 3,779(already fixed) /
      신용위험액 1,347 / 운영위험액 812(already correct) / 법인세조정액 4,430 /
      다.지급여력비율 234.0
  p10 "(1) 공통적용 경과조치 관련" (백만원): 지급여력금액 3,489,594=34,895.94 /
      기본자본 2,933,961=29,339.61 / 보완자본 555,633=5,556.33 /
      지급여력기준금액 1,491,400=14,914.00 -- agrees with p9 to the cent.
  p11 ②표 (백만원): 기본요구자본 1,934,371=19,343.71 / 신용위험액 134,741=1,347.41 --
      agrees with p9.

Full reconciliation after this fix (scratchpad verify_aia_cluster.py):
  R1 item1==item2+item3: 34896==34896 exact.
  R5 item14==item15-item22+item23: 14914==14914 exact.
  R4(item15) expected 19342.96 vs stated 19344, diff -1.04 (normal filing rounding).
  R6(item16) expected 3379 vs stated 3381, diff -2 (normal filing rounding).
  item27 = item1/item14*100 = 233.98 (rounds to disclosed 234.0).
  item28 = item2/item14*100 = 196.73.

items 4-13(순자산 구성요소), 17/18/21/29-40 were already correct in master and are left
untouched (not part of this cluster, not causing any RED).

Usage: ...python scripts/fix_20260821_aia_kr0080_2023q3_headline.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "kics_disclosure.json"

CODE, QUARTER = "KR0080", "2023.3Q"

# item -> (guard, new). Applied identically to 값 and 값_적용후 (전=후 mirror, confirmed p8).
FIXES = {
    1: ("35173", "34896"),
    2: ("30788", "29340"),
    3: ("4385", "5556"),
    14: ("14865", "14914"),
    15: ("19280", "19344"),
    16: ("3300", "3381"),
    20: ("1339", "1347"),
    22: ("4415", "4430"),
    27: ("236.61621258", "233.98149389835052"),
    28: ("207.11738984", "196.72790666487862"),
}


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    done, skip = [], []
    for r in data:
        if r.get("원보험사코드") != CODE or r.get("공시분기") != QUARTER:
            continue
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        if it not in FIXES:
            continue
        guard, new = FIXES[it]
        for col in ("값", "값_적용후"):
            cur = r.get(col)
            if cur != guard and str(cur) != guard:
                skip.append((it, col, cur, guard))
                continue
            done.append((it, col, cur, new))
            if not dry:
                r[col] = new
    print(f"{'DRY-RUN ' if dry else ''}적용 {len(done)} · 건너뜀 {len(skip)}")
    for it, col, cur, new in done:
        print(f"  item{it}[{col}]: {cur!r} -> {new}")
    for it, col, cur, guard in skip:
        print(f"  SKIP item{it}[{col}]: 현재값 {cur!r} != guard {guard!r}")
    if not dry and skip:
        print("ABORT: guard mismatch, refusing partial write")
        return 1
    if not dry and done:
        TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
