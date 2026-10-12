# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

edit("inbox/designer/20261013T0030Z__publishing__MULTI_2026.2Q__capsec_timeline_flags_and_tier2_fields.md", [
("""### 1. (필수) DB손해보험 제1·2회 콜일-금액 짝 — `kics_capital_securities_timeline.json`""",
"""### 1. (확인만 - HTML 변경 불필요) DB손해보험 제1·2회 콜일-금액 짝 — `kics_capital_securities_timeline.json`"""),
("""JSON 에 선택 표지 `call_date_unconfirmed: true` 를 붙인 행: KR0011 `issue_date` 2025-09-01(face 7,470억, `call_date` 2030-09-25)과 2025-09-25(face 1,200억, `call_date` 2030-09-01) 두 건. 키는 True 일 때만 있다.
- 지금 화면은 「신종자본증권 / 콜 상환 도래일 : 2030-09-01 (1,200억)」 을 그린다 = 날짜-금액 짝이 틀릴 수 있다(09-01 은 제1회 7,470억일 수도, 제2회 1,200억일 수도, 둘 다 8,670억일 수도 있다).
- 요청: `capsecCells()` 가 `nextDate` 를 고를 때 그 날짜에 합산되는 증권 중 하나라도 `call_date_unconfirmed` 이면 **날짜만 싣고 금액 괄호를 뺀다**(`next_call_eok = null`; 렌더러는 이미 null 이면 괄호를 안 그린다). 어느 시나리오에서도 가장 이른 콜일은 2030-09-01 이라 날짜는 맞다. 전망·소진율은 영향 없음(두 콜 모두 2030년).""",
"""JSON 에서 KR0011 `issue_date` 2025-09-01(face 7,470억, `call_date` 2030-09-25)과 2025-09-25(face 1,200억, `call_date` 2030-09-01) 두 건의 **`outstanding_eok` 를 null 로 비웠고** 선택 표지 `call_date_unconfirmed: true` 를 붙였다(표지 키는 True 일 때만 있다; `face_eok` 는 그대로).
- 커밋된 K-ICS.html(`75234ddf`)의 `capsecCells()` 가 이미 잔액 null 인 콜 후보는 날짜만 그린다 -> 화면은 「콜 상환 도래일 : 2030-09-01」 (금액 괄호 없음)이 된다. 어느 시나리오에서도 가장 이른 콜일은 2030-09-01 이라 날짜는 맞다. 이전에는 「2030-09-01 (1,200억)」 이라 날짜-금액 짝이 틀릴 수 있었다.
- 부작용 확인: 이 두 건은 잔액이 null 이라 같은 함수의 「최근 발행금리」 후보(`outstanding_eok > 0`)에서 빠지지만, DB손해의 더 늦은 발행(제3~5회)이 있어 금리 값은 안 바뀐다. `scripts/check_kics_callcell.py` 는 후순위 변형으로 검사하므로 신종 DB손해 사례를 한 번 눈으로 확인해 달라(선택).
- 전망·소진율은 영향 없음(두 콜 모두 2030년)."""),
])
