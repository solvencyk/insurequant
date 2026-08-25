# -*- coding: utf-8 -*-
"""ABL생명(KR0070) PL bridge 수정 — data/_gold/user_pl_cells.json 에 override 10건 추가.

1) item7(기타생명장기원수손익) 재계산 4건 (2023.1Q, 2024.1Q, 2024.2Q, 2024.3Q):
   2026-08-17 gold override 가 item4 를 raw 로 고치면서 item7(=item3-(4+5+6) 설계식 plug,
   scripts/build_pl_breakdown.py assemble() 147-149행)을 다시 계산하지 않아 옛 item4 기준
   plug 로 남아 있었다. PL_BRIDGE 등식이 그 4개 분기에서 실패한 진짜 원인 — item4 는 이미
   맞다. item7 을 새 item4 기준으로 재계산해 등식을 닫는다.

2) item4+item7 정정 6건 (2025.1Q/2Q/3Q):
   배포본 원수CSM상각이 2024.1Q~3Q 값(22447/44994/66762)과 완전 동일 — 우연이 아니라
   당기/전기 열이 뒤바뀐 지문(원문 raw: '전환방법별 CSM 변동표' 표에서 '1) 당분기' 절과
   '2) 전분기' 절의 절대값 비교시 전분기(=전년 동기)가 더 크면 max(abs) 로직이 전분기를
   고른다 — max(|20087|,|22447|)=22447 이 실제로 뽑혔다). raw 원문 '1) 당분기' 절
   '제공된 서비스 관련 당기손익 인식' 합계열이 진짜 2025 값이다(20087/40080/61207,
   scripts/_probes/probe_20260825_abl_transition_csm_table.py 재현). item4 를 내리는 김에
   item7 도 같이 재계산해야 등식이 닫힌다(안 그러면 1)의 결함을 2025 에도 새로 심는 것).

전건 scripts/_probes/probe_20260825_compute_abl_item7_fix.py 로 정밀검산(잔차 0.000000000,
7/7). 티켓: inbox/parser/20260825T1120Z__validation__MULTI__pl_bridge_deployed_master_defects.md

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/fix_20260825_abl_item7_and_2025_item4.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

OVR_PATH = ROOT / "data" / "_gold" / "user_pl_cells.json"
TICKET = ("inbox/parser/20260825T1120Z__validation__MULTI__"
          "pl_bridge_deployed_master_defects.md")

NOTE_ITEM7_2024 = (
    f"{TICKET} (validation, PL_BRIDGE copied_cell/basis_mix_csm_amort): item4(원수CSM상각)는 "
    "2026-08-17 override 로 이미 raw 확정된 값(전환방법별 CSM 변동표 '1) 당분기'절 '제공된 "
    "서비스 관련 당기손익 인식' 합계열)인데, 그 override 가 item7(설계식 residual = "
    "item3-(4+5+6), build_pl_breakdown.py assemble() 147-149행)을 재계산하지 않아 옛 item4 "
    "기준 plug 로 남아 PL_BRIDGE 등식이 깨져 있었다. item3/5/6 은 그대로 두고 item7 만 새 "
    "item4 기준으로 재계산(잔차 0 확인, probe_20260825_compute_abl_item7_fix.py). item4 값 "
    "자체는 변경 없음."
)

NOTE_2025_ITEM4 = (
    f"{TICKET} (validation, PL_BRIDGE copied_cell 조사 중 발견): 배포본 원수CSM상각이 "
    "2024.{Q}Q 값과 완전 동일한 복제 지문 — raw 원문(전환방법별 CSM 변동표 '1) 당분기'절 "
    "'제공된 서비스 관련 당기손익 인식' 합계열, scripts/_probes/"
    "probe_20260825_abl_transition_csm_table.py 재현)으로 확정한 결과 이 분기는 {new:,.0f}. "
    "같은 표의 '2) 전분기'절(=2024 동기 비교값)이 {was:,.0f}로 더 커서 max(abs) 선택 로직이 "
    "전분기 열을 잘못 고른 것으로 보인다(코드 수정은 blast-radius 커서 이번 라운드는 override "
    "로 정정, 핸들러 조사는 별도 후속)."
)

NOTE_2025_ITEM7 = (
    f"{TICKET}: 같은 분기 item4 를 raw 값으로 내리면서 item7(residual=item3-(4+5+6))도 같이 "
    "재계산 — 안 그러면 2024 분기에서 발견된 것과 같은 '옛 item4 기준 stale plug' 결함을 "
    "2025 에도 새로 심게 된다. 잔차 0 확인(probe_20260825_compute_abl_item7_fix.py)."
)

# (quarter, item4_raw_or_None_if_unchanged, item4_was_or_None, item7_new, item7_was)
FIXES = [
    ("2023.1Q", None,      None,      -1767.000000,    17533.000000),
    ("2024.1Q", None,      None,      -3101.757812,    17032.242188),
    ("2024.2Q", None,      None,      -2329.139877,    38012.860123),
    ("2024.3Q", None,      None,     -17990.010136,    41616.989864),
    ("2025.1Q", 20087.0,   22447.0,   -5947.368229,    -8307.368229),
    ("2025.2Q", 40080.0,   44994.0,  -15683.469520,   -20597.469520),
    ("2025.3Q", 61207.0,   66762.0,  -24184.492374,   -29739.492374),
]


def main() -> int:
    ovr = json.loads(OVR_PATH.read_text(encoding="utf-8"))
    s = ovr["set"]
    existing = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in s}

    added = []
    for q, item4_new, item4_was, item7_new, item7_was in FIXES:
        qn = q.split(".")[1][0]  # e.g. "1" from "2025.1Q"
        if item4_new is not None:
            key = ("KR0070", 4, q)
            if key in existing:
                print(f"  SKIP (already present) {key}")
            else:
                s.append({"원보험사코드": "KR0070", "항목번호": 4, "공시분기": q,
                           "값": item4_new, "was": item4_was,
                           "note": NOTE_2025_ITEM4.format(Q=qn, new=item4_new, was=item4_was)})
                added.append(key)
        key7 = ("KR0070", 7, q)
        if key7 in existing:
            print(f"  SKIP (already present) {key7}")
        else:
            note = NOTE_ITEM7_2024 if item4_new is None else NOTE_2025_ITEM7
            s.append({"원보험사코드": "KR0070", "항목번호": 7, "공시분기": q,
                       "값": item7_new, "was": item7_was, "note": note})
            added.append(key7)

    print(f"added {len(added)} override entries:")
    for k in added:
        print(" ", k)

    OVR_PATH.write_text(json.dumps(ovr, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {OVR_PATH}  (total set entries now {len(s)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
