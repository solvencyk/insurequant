# -*- coding: utf-8 -*-
"""lob_sum_gap 5건 중 3건 -- item16(기타사업비용) raw 보강/부호정정 override 추가.

DB생명보험 2023.1Q: item16 결측(None) -> raw '(2) 요약포괄손익계산서'(56행) '(3) 기타사업비'
  = 2,577,053,702원 = 2,577.053702백만원 (라벨 변형: "기타사업비" vs 코드가 찾는
  "기타사업비용" -- trailing "용" 없음이라 미매칭). item16 만 채운다.
  주의: 이 값을 넣어도 dual-form 은 완전히 안 닫힌다(잔차 1,601.89 = 정확히 item8
  생명장기재보험손익 크기) -- DB생명 자체 표에서 '1.보험손익'이 '2.재보험손익'과 별도
  최상위 항목이라(같은 표 5-8행 참조), 이 회사 '보험손익' 캡션이 재보험을 구조적으로
  제외한다. item1 은 raw 라벨과 정확히 일치하므로 바꾸지 않는다 -- 잔차는 별도로 박제.

메리츠화재해상보험 2023.1Q/2Q: item16 결측(None) -> raw '(3) 기타사업비용' 행을 그대로
  (부호 보존!) 사용. 2023.1Q 는 원문 자체가 **음수**(-12,370,224,177원 = -12,370.224177백만,
  기타손익이 순이익 방향이라 부호가 뒤집힌 분기)이고 assemble() 의 v[16]=abs(v[16]) 정규화가
  이런 진성 음수를 강제 양전환해 버리는데, override 는 assemble() 을 우회해 root 셀을 직접
  덮으므로 원문 부호를 그대로 보존해 override 한다. 2023.2Q 는 원문이 양수
  (71,546,566,619원 = 71,546.566619백만)로 정상 부호. 둘 다 override 후 adj 잔차
  0.2~0.4백만(허용오차 이내) 로 닫힘 확인(verify_lobsumgap_fix.py).

티켓: inbox/parser/20260825T1120Z__validation__MULTI__pl_bridge_deployed_master_defects.md

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/fix_20260825_lobsumgap_item16.py
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

FIXES = [
    ("KR0082", "DB생명보험", "2023.1Q", 2577.053702,
     f"{TICKET} (validation, PL_BRIDGE lob_sum_gap): item16(기타사업비용) 결측 -> raw "
     "'(2) 요약포괄손익계산서' '(3) 기타사업비' 행 2,577,053,702원=2,577.053702백만원 "
     "(라벨변형: '기타사업비' vs 코드탐색 '기타사업비용', trailing '용' 없음이라 미매칭). "
     "주의: 이 값을 넣어도 dual-form PL_BRIDGE 는 완전히 안 닫힌다(잔차 1,601.89 = 정확히 "
     "item8 생명장기재보험손익). DB생명 원표에서 '1.보험손익'이 '2.재보험손익'과 별도 "
     "최상위 항목으로 병기돼 있어(재보험 제외) 이 회사 '보험손익' 캡션 자체가 구조적으로 "
     "재보험을 뺀다 — item1 은 원문과 정확히 일치하므로 변경하지 않음, 잔차는 별도 박제."),
    ("KR0001", "메리츠화재해상보험", "2023.1Q", -12370.224177,
     f"{TICKET} (validation, PL_BRIDGE lob_sum_gap): item16(기타사업비용) 결측 -> raw "
     "'(3) 기타사업비용' 행 -12,370,224,177원=-12,370.224177백만원(원문 자체가 음수 — "
     "이 분기는 기타손익이 순이익 방향). assemble() 의 v[16]=abs(v[16]) 정규화를 우회해 "
     "부호 보존 override. adj=bare-item16=407,167+12,370.22=419,537.22 ≈ 보험손익 "
     "419,537.0(잔차 0.22, 허용오차 419.5 이내) — 닫힘 확인."),
    ("KR0001", "메리츠화재해상보험", "2023.2Q", 71546.566619,
     f"{TICKET} (validation, PL_BRIDGE lob_sum_gap): item16(기타사업비용) 결측 -> raw "
     "'(3) 기타사업비용' 행 71,546,566,619원=71,546.566619백만원(이 분기는 정상 양수 부호). "
     "adj=bare-item16=894,154-71,546.57=822,607.43 ≈ 보험손익 822,607.0(잔차 0.43, "
     "허용오차 822.6 이내) — 닫힘 확인."),
]


def main() -> int:
    ovr = json.loads(OVR_PATH.read_text(encoding="utf-8"))
    s = ovr["set"]
    existing = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in s}

    added = []
    for code, name, q, val, note in FIXES:
        key = (code, 16, q)
        if key in existing:
            print(f"  SKIP (already present) {key}")
            continue
        s.append({"원보험사코드": code, "항목번호": 16, "공시분기": q,
                   "값": val, "was": None, "note": note})
        added.append(key)

    print(f"added {len(added)} override entries:")
    for k in added:
        print(" ", k)

    OVR_PATH.write_text(json.dumps(ovr, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {OVR_PATH}  (total set entries now {len(s)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
