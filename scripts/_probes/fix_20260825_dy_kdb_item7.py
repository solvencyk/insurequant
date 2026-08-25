# -*- coding: utf-8 -*-
"""동양생명(KR0087) 2024.2Q/3Q, 케이디비생명보험(KR0072) 2023.2Q/3Q item7 재계산 override 추가.

메커니즘은 에이비엘생명(KR0070)과 동일 — 2026-08-17 item4 override(raw 재검증 +
CSM_waterfall 교차대조로 확정, data/_gold/user_pl_cells.json 기존 항목 참조) 가
item7(=item3-(4+5+6), scripts/build_pl_breakdown.py assemble() 147-149행)을 재계산하지
않아 stale plug 로 남았다. item3/5/6 은 그대로 두고 item7 만 재계산.
값은 scripts/_probes/probe_20260825_compute_dy_kdb_item7_fix.py 로 정밀검산(잔차 0, 4/4).

티켓: inbox/parser/20260825T1120Z__validation__MULTI__pl_bridge_deployed_master_defects.md

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/fix_20260825_dy_kdb_item7.py
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
NOTE = (
    f"{TICKET} (validation, PL_BRIDGE basis_mix_csm_amort): item4(원수CSM상각)는 2026-08-17 "
    "override 로 이미 raw+CSM_waterfall 교차검증으로 확정된 값인데, 그 override 가 "
    "item7(설계식 residual = item3-(4+5+6), build_pl_breakdown.py assemble() 147-149행)을 "
    "재계산하지 않아 옛 item4 기준 plug 로 남아 PL_BRIDGE 등식이 깨져 있었다(에이비엘생명 "
    "KR0070 에서 발견한 것과 동일 메커니즘 — 해당 티켓의 fix_20260825_abl_item7_and_2025_"
    "item4.py 참조). item3/5/6 은 변경 없음, item7 만 새 item4 기준으로 재계산(잔차 0 확인, "
    "probe_20260825_compute_dy_kdb_item7_fix.py). item4 값 자체는 변경 없음."
)

FIXES = [
    ("KR0087", "2024.2Q", -3670.662495, 60525.337505),
    ("KR0087", "2024.3Q", 40979.623446, 170417.623446),
    ("KR0072", "2023.2Q", -18990.000000, -7865.000000),
    ("KR0072", "2023.3Q", -44935.275872, -21520.275872),
]


def main() -> int:
    ovr = json.loads(OVR_PATH.read_text(encoding="utf-8"))
    s = ovr["set"]
    existing = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in s}

    added = []
    for code, q, new7, was7 in FIXES:
        key = (code, 7, q)
        if key in existing:
            print(f"  SKIP (already present) {key}")
            continue
        s.append({"원보험사코드": code, "항목번호": 7, "공시분기": q,
                   "값": new7, "was": was7, "note": NOTE})
        added.append(key)

    print(f"added {len(added)} override entries:")
    for k in added:
        print(" ", k)

    OVR_PATH.write_text(json.dumps(ovr, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {OVR_PATH}  (total set entries now {len(s)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
