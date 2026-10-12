# -*- coding: utf-8 -*-
"""Request 8 correction (coordinator): the ledger pre-2023 deduction must exclude bonds that are outstanding but already past
their first call date (ledger flag past_call_outstanding=true). Effective maturity of a capital security = its call date (forward
model rolls it off then), so a past-call bond is no longer recognized capital and the issuers do not print it in their 기발행 line."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

edit("scripts/capital_utilization_rules.py", [
("""    기발행 차감액 = **채권원장의 2022-12-31 이전 발행 잔액**(신종·후순위 따로, 47사 공통; owner 결정 2026-10-12 밤).
""",
"""    기발행 차감액 = **채권원장의 2022-12-31 이전 발행 잔액**(신종·후순위 따로, 47사 공통; owner 결정 2026-10-12 밤). 단 **콜일이 이미
           지났는데 상환 안 한 채권(원장 `past_call_outstanding`=true)은 뺀다** - 자본증권의 실효 만기는 콜일이라(forward 도 콜일에 롤오프)
           콜 경과분은 더는 인정 자본이 아니고 발행사도 자기 기발행 줄에 넣지 않는다(coordinator 정정 2026-10-13).
"""),
("""LEDGER_PATH = ROOT / "kics_capital_securities.json"
""",
"""LEDGER_PATH = ROOT / "kics_capital_securities.json"
BONDS_PATH = ROOT / "data" / "bonds" / "capital_securities_fy2026h1.json"
"""),
("""NEW_DEBT_ROW_BASIS = (". 기발행 차감액은 발행사 인쇄값(항목 53·54)이 아니라 채권원장의 2022년까지 발행 잔액이다 - 인쇄값에는 "
                      "2023년 이후 발행 신규채가 섞여 있을 수 있고 신규채는 기발행이 아니라 한도 대상이다"
                      "(owner 결정 2026-10-12: 기발행 차감은 2022년까지 발행분만).")""",
"""NEW_DEBT_ROW_BASIS = (". 기발행 차감액은 발행사 인쇄값(항목 53·54)이 아니라 채권원장의 2022년까지 발행 잔액이다(콜일이 지났는데 "
                      "상환 안 한 채권 제외) - 인쇄값에는 2023년 이후 발행 신규채가 섞여 있을 수 있고 신규채는 기발행이 아니라 한도 "
                      "대상이다(owner 결정 2026-10-12: 기발행 차감은 2022년까지 발행분만).")"""),
("""    sub_legacy·hybrid_legacy 는 s4 와 같은 판정이다: 발행일이 없거나 2023-01-01 전이면 기발행(= 2022-12-31 이전 발행 잔액).""",
"""    sub_legacy·hybrid_legacy 는 s4 와 같은 판정이다: 발행일이 없거나 2023-01-01 전이면 기발행(= 2022-12-31 이전 발행 잔액).
    단 둘은 행(`kics_capital_securities.json`)이 아니라 채권원장 원본(`data/bonds/...fy2026h1.json`)에서 직접 내며, **콜일 경과 후
    미상환(`past_call_outstanding`=true) 채권은 뺀다**(coordinator 정정 2026-10-13)."""),
])
