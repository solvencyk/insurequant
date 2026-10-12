# -*- coding: utf-8 -*-
"""Request 1, final form: the designer's committed K-ICS.html (75234ddf) already shows only the date when a call candidate's
outstanding_eok is null. So for call_date_unconfirmed bonds the timeline feed blanks the amount (null) next to the possibly
mis-paired date; the flag stays as the explicit reason. Validator allows null outstanding_eok only together with the flag."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

edit("scripts/build_capital_securities_timeline.py", [
('''    if bond.get("call_date_unconfirmed"):
        rec["call_date_unconfirmed"] = True      # 발행사 공시끼리 콜일이 엇갈려 어느 회차의 콜인지 미확정(DB손해 제1·2회)
''',
'''    if bond.get("call_date_unconfirmed"):
        rec["call_date_unconfirmed"] = True      # 발행사 공시끼리 콜일이 엇갈려 어느 회차의 콜인지 미확정(DB손해 제1·2회)
        rec["outstanding_eok"] = None            # 틀릴 수 있는 날짜 옆에 금액을 싣지 않는다 - 화면은 잔액이 null 이면 날짜만 그린다
'''),
('''* 선택 표지(True 일 때만 존재): `call_date_unconfirmed`(공시끼리 콜일이 엇갈려 회차별 콜일-금액 짝 미확정 - 화면은 그 콜일 옆에 금액을
  싣지 않는다), `estimated`(원장 미갱신으로 공시 증가분에서 넣은 추정 행 - 금리·콜일 미상)''',
'''* 선택 표지(True 일 때만 존재): `call_date_unconfirmed`(공시끼리 콜일이 엇갈려 회차별 콜일-금액 짝 미확정 - 이 건은 outstanding_eok 를
  null 로 비워 화면이 콜일 옆에 금액을 싣지 않게 한다; face_eok 는 그대로), `estimated`(원장 미갱신으로 공시 증가분에서 넣은 추정 행 -
  금리·콜일 미상)'''),
])
edit("scripts/validate_live_artifacts.py", [
('''            miss = [f for f in CAPTL_REQUIRED if b.get(f) is None]
''',
'''            # 잔액 null 은 콜일 미확정 표지와 함께일 때만 허용(날짜-금액 짝을 화면에 싣지 않으려고 의도적으로 비운 칸)
            blank_ok = b.get("call_date_unconfirmed") is True and b.get("outstanding_eok") is None
            miss = [f for f in CAPTL_REQUIRED if b.get(f) is None and not (blank_ok and f == "outstanding_eok")]
'''),
('''            for f in ("face_eok", "outstanding_eok"):
                v = b.get(f)
                if isinstance(v, bool)''',
'''            for f in ("face_eok", "outstanding_eok"):
                v = b.get(f)
                if blank_ok and f == "outstanding_eok":
                    continue
                if isinstance(v, bool)'''),
])
edit("tests/unit/test_capital_securities_timeline.py", [
('''    assert T.bond_record(bond(call_date_unconfirmed=True), None)["call_date_unconfirmed"] is True
''',
'''    unc = T.bond_record(bond(call_date_unconfirmed=True), None)
    assert unc["call_date_unconfirmed"] is True
    assert unc["outstanding_eok"] is None and unc["face_eok"] == 5000.0      # 금액은 비우고 권면은 그대로
'''),
('''            assert r["face_eok"] > 0 and r["outstanding_eok"] >= 0
''',
'''            assert r["face_eok"] > 0
            assert (r["outstanding_eok"] is None and r.get("call_date_unconfirmed") is True) or r["outstanding_eok"] >= 0
'''),
])
