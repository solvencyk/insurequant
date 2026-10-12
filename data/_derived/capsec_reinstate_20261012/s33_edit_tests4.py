# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit
edit("tests/unit/test_capital_utilization_rules.py", [
("""            # 콜일이 지났는데 상환 안 한 채권(past_call_outstanding)은 실효 만기(콜일)가 지났으므로 뺀다(coordinator 정정 2026-10-13)
            if (b.get("issue_date") or "") < "2023-01-01" and not b.get("past_call_outstanding"):""",
 """            # 첫 콜일이 분자 기준일(2026-06-30) 이전이거나 같은 채권은 실효 만기(콜일)가 지났으므로 뺀다(coordinator 정정 2026-10-13,
            # validation 20261013T0205Z: 날짜에서 직접 판정). 원장 표지 past_call_outstanding=true 도 뺀다.
            if ((b.get("issue_date") or "") < "2023-01-01" and not b.get("past_call_outstanding")
                    and not ((b.get("call_date") or "") and b["call_date"] <= "2026-06-30")):"""),
("메리츠 0.2 -> 30.8 · 흥국생명 10.6 -> 37.0 ·", "메리츠 0.2 -> 37.5(콜일 기준 정정 후) · 흥국생명 10.6 -> 37.0 ·"),
("== (30.8, 37.0, 102.8, 74.8, 73.1)", "== (37.5, 37.0, 102.8, 74.8, 73.1)"),
])
