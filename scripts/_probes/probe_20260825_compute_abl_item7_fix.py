# -*- coding: utf-8 -*-
"""ABL생명(KR0070) item7(기타생명장기원수손익) 재계산값을 정밀 산출.

근거: scripts/build_pl_breakdown.py assemble() 의 설계식 item7 = item3 - (item4+item5+item6)
(147-149행). 2026-08-17 gold override 가 item4 를 raw 재검증으로 고치면서 item7 을 다시
계산하지 않아 그 4개 분기(2023.1Q, 2024.1Q~3Q)의 item7 이 옛 item4 기준 plug 로 남았다
(수치로 재현: 현재 item7 == item3 - item4_구값 - item5 - item6, 소수 6자리까지 일치).

2025.1Q~3Q 는 반대 방향 결함 — item4 자체가 raw 로 확인한 2024 값과 동일하게 복제돼 있다
(당기/전기 max(abs) 뒤바뀜, '전환방법별 CSM 변동표' 표에서 확인:
data/dart/FY2025_Q{1,2,3}/raw 의 '1) 당분기' 절 합계가 각각 20,087/40,080/61,207).
item4 를 raw 값으로 내리면 item7 도 같이 재계산해야 등식이 닫힌다.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_compute_abl_item7_fix.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

# raw-confirmed true item4 (원수CSM상각) YTD, from '전환방법별 CSM 변동표' -> '1) 당분기' ->
# '제공된 서비스 관련 당기손익 인식' 행의 합계열(부호 반전, abs)
RAW_ITEM4 = {
    "2023.1Q": 22664.0,   # already correct in root (matches override)
    "2024.1Q": 22447.0,   # already correct in root (matches override)
    "2024.2Q": 44994.0,   # already correct in root (matches override)
    "2024.3Q": 66762.0,   # already correct in root (matches override)
    "2025.1Q": 20087.0,   # root currently WRONG (22447, = 2024.1Q dupe) -> needs correction
    "2025.2Q": 40080.0,   # root currently WRONG (44994, = 2024.2Q dupe) -> needs correction
    "2025.3Q": 61207.0,   # root currently WRONG (66762, = 2024.3Q dupe) -> needs correction
}


def main() -> int:
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    by_q = defaultdict(dict)
    row_by_key = {}
    for r in rows:
        if r.get("원보험사코드") == "KR0070":
            by_q[r["공시분기"]][r["항목번호"]] = r.get("값")
            row_by_key[(r["항목번호"], r["공시분기"])] = r

    print(f"{'quarter':9s} {'item4_root':>12s} {'item4_raw':>12s} {'item4_change':>6s} "
          f"{'item3':>14s} {'item5':>10s} {'item6':>8s} {'item7_old':>14s} {'item7_new':>14s}")
    out = {}
    for q, raw4 in RAW_ITEM4.items():
        m = by_q[q]
        i3, i4, i5, i6, i7 = m.get(3), m.get(4), m.get(5), m.get(6), m.get(7)
        new7 = i3 - (raw4 + i5 + i6)
        changed4 = "YES" if abs((i4 or 0) - raw4) > 0.01 else "no"
        print(f"{q:9s} {i4:12,.1f} {raw4:12,.1f} {changed4:>6s} "
              f"{i3:14,.6f} {i5:10,.1f} {i6:8,.1f} {i7:14,.6f} {new7:14,.6f}")
        out[q] = {"item4_new": raw4, "item7_new": round(new7, 6),
                   "item4_changed": changed4 == "YES"}

    outp = ROOT / "scripts" / "_probes" / "_compute_abl_item7_fix_out.json"
    outp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {outp}")

    # sanity: recompute the equation with the NEW values, confirm closes to ~0
    print("\n-- sanity check: item3 - (item4_new+item5+item6+item7_new) should be ~0 --")
    for q, raw4 in RAW_ITEM4.items():
        m = by_q[q]
        i3, i5, i6 = m[3], m[5], m[6]
        new7 = out[q]["item7_new"]
        resid = i3 - (raw4 + i5 + i6 + new7)
        print(f"  {q}: resid={resid:.9f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
