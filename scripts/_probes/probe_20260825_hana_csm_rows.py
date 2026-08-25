# -*- coding: utf-8 -*-
"""하나생명(KR0097) CSM_waterfall 행 + 항등식 + FY 경계 + **원문 대조표** (read-only).

배경(2026-08-25, validation 재확인). 2024.4Q 행이 **두 filing 기준을 섞고** 있고 item4
(가정및경험조정)가 그 차이를 잔차로 흡수한다:

  * 기초 = FY2024 사업보고서 원본(3,016.1)
  * 이자/상각/기말 = FY2025 사업보고서의 **재작성 전기** 열(181.3 / -403.7 / 4,446.8)
  * item4 = -1,587.2  <- 어느 공시에도 없는 수. 원본 -1,647.4 도 재작성 -1,660.2 도 아니다.

item4 는 빌더 설계상 잔차(`assum = clo - (기초+신계약+이자+상각)`)이므로, 나머지 다섯 칸이
**한 표에서** 올 때만 발행사 값과 같아진다. 그 전제가 깨지면 항등식은 닫히는데 화면 숫자는
원문에 없는 값이 된다 = false-green.

원문 근거는 아래 RAW 표에 박아 두었다(단위 천원, CSM = 수정소급법+공정가치법+이외 합).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = "KR0097"

# 원문에서 직접 읽은 값 (단위 천원). 출처는 각 filing 의 차이조정표.
RAW = {
    # FY2023 사업보고서 20240329000112_00760.xml 주석 13-3 (1) 보험, 당기 열
    ("2023.4Q", "FY2023 원본"): {
        1: 79_437_972 + 63_930_243 + 44_369_098,
        2: 209_183_792,
        3: 1_447_046 + 1_575_838 + 4_684_001,
        4: (-4_297_561) + (-20_013_688) + (-50_752_331) + (-41_413),   # 조정 + 기타
        5: (-7_665_870) + (-9_109_822) + (-11_138_016),
        6: 68_921_587 + 36_341_157 + 196_346_544,
    },
    # FY2024 사업보고서 20250331000222_00760.xml 주석 13-4 (1) 보험, 당기 열
    ("2024.4Q", "FY2024 원본"): {
        1: 68_921_318 + 36_345_016 + 196_346_545,
        2: 324_034_743,
        3: 1_561_124 + 991_497 + 15_349_112,
        4: (-9_320_910) + 11_494_728 + (-166_910_019),
        5: (-7_147_587) + (-3_156_554) + (-29_553_350),
        6: 54_013_945 + 45_674_687 + 339_267_030,
    },
    # FY2025 사업보고서 20260325000201_00760.xml 주석 14-4 (1) 보험, 전기 열 (재작성)
    ("2024.4Q", "FY2025 재작성전기"): {
        1: 308_905_720, 2: 324_034_743, 3: 18_132_607,
        4: -166_022_230, 5: -40_368_775, 6: 444_682_065,
    },
    # 같은 filing, 당기 열
    ("2025.4Q", "FY2025 당기"): {
        1: 444_682_065, 2: 408_616_322, 3: 21_711_507,
        4: -94_270_587, 5: -53_843_619, 6: 726_895_688,
    },
}
LABEL = {1: "기초", 2: "신계약", 3: "이자부리", 4: "가정및경험조정", 5: "CSM상각", 6: "기말"}


def main() -> int:
    wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
    by: dict = {}
    for r in wf:
        if r["원보험사코드"] == CODE:
            by.setdefault(r["공시분기"], {})[r["항목번호"]] = r

    print("=" * 96)
    print("마스터 CSM_waterfall.json (억원)")
    print("=" * 96)
    for q in sorted(by):
        g = lambda n: (by[q].get(n) or {}).get("값")   # noqa: E731
        cells = "  ".join(f"{LABEL[n]}={g(n)}" for n in range(1, 7))
        print(f"  {q}  {cells}")
        if all(g(n) is not None for n in range(1, 7)):
            lhs = sum(g(n) for n in (1, 2, 3, 4, 5))
            print(f"      항등식 Σ={round(lhs, 2)}  vs 기말 {g(6)}   Δ={round(lhs - g(6), 3)}")
    qs = sorted(by)
    print("\n  FY 경계 (직전 기말 -> 기초):")
    for a, b in zip(qs, qs[1:]):
        ca = (by[a].get(6) or {}).get("값")
        ob = (by[b].get(1) or {}).get("값")
        if ca is not None and ob is not None:
            print(f"    {a} 기말={ca}  ->  {b} 기초={ob}   Δ={round(ob - ca, 2)}")

    print()
    print("=" * 96)
    print("원문 대조 (천원 -> 억원, /100,000)")
    print("=" * 96)
    for (q, src), vals in RAW.items():
        cur = by.get(q, {})
        print(f"\n  [{q}] {src}")
        for n in range(1, 7):
            raw_ok = vals[n] / 100_000.0
            mv = (cur.get(n) or {}).get("값")
            mark = ""
            if mv is not None:
                mark = "  <== 일치" if abs(mv - raw_ok) <= 0.15 else f"  <== 마스터 {mv} (Δ{round(mv - raw_ok, 2)})"
            print(f"    {LABEL[n]:<12s} {vals[n]:>16,} 천원 = {raw_ok:>10.2f} 억{mark}")
    print("\n  2024.4Q 는 두 원문 어느 쪽으로도 통일돼 있지 않다 — 그게 이 프로브의 요점이다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
