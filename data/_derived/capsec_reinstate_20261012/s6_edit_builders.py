# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

edit("scripts/build_capital_securities_recognition.py", [
('''    call = _pdate(b.get("call_date"))
    legal = economic_maturity(b)
''',
'''    # 발행사 공시끼리 콜일이 엇갈려 확정 못 한 증권(DB손해 제1·2회, 티켓 20261012T2235Z 요청 1)은 콜일을 비운다 - 짝이 틀린
    # 날짜를 싣는 것보다 낫다. 채권원장의 call_date 는 forward(연 단위)가 계속 읽는다.
    call = None if b.get("call_date_unconfirmed") else _pdate(b.get("call_date"))
    legal = economic_maturity(b)
'''),
('''        "콜근거": b.get("call_source"),''',
'''        "콜근거": "공시 원문 상충(콜일 미확정)" if b.get("call_date_unconfirmed") else b.get("call_source"),'''),
])

edit("scripts/build_capital_securities_timeline.py", [
('''        "call_date": bond.get("call_date") or None,
        "coupon_pct": bond.get("coupon_pct"),
        "face_eok": eok(face),
        "outstanding_eok": eok(out or 0.0),
        "as_of": bond.get("as_of") or company_as_of,
    }
''',
'''        "call_date": bond.get("call_date") or None,
        "coupon_pct": bond.get("coupon_pct"),
        "face_eok": eok(face),
        "outstanding_eok": eok(out or 0.0),
        "as_of": bond.get("as_of") or company_as_of,
    }
    # 선택 표지 두 개(True 일 때만 키가 생긴다): 화면이 날짜-금액 짝을 싣지 말아야 하는 건을 알아보게 한다.
    if bond.get("call_date_unconfirmed"):
        rec["call_date_unconfirmed"] = True      # 발행사 공시끼리 콜일이 엇갈려 어느 회차의 콜인지 미확정(DB손해 제1·2회)
    if bond.get("estimated"):
        rec["estimated"] = True                  # 원장 미갱신으로 공시 증가분에서 추정해 넣은 행(금리·콜일 미상)
    return rec
'''),
('''    return {
        "tier": bond["tier"],
        "issue_date": bond["issue_date"],''',
'''    rec = {
        "tier": bond["tier"],
        "issue_date": bond["issue_date"],'''),
('''* 회사코드는 JSON 키로만 쓴다(화면 노출 금지 규약).''',
'''* 회사코드는 JSON 키로만 쓴다(화면 노출 금지 규약).
* 선택 표지(True 일 때만 존재): `call_date_unconfirmed`(공시끼리 콜일이 엇갈려 회차별 콜일-금액 짝 미확정 - 화면은 그 콜일 옆에 금액을
  싣지 않는다), `estimated`(원장 미갱신으로 공시 증가분에서 넣은 추정 행 - 금리·콜일 미상)'''),
])
