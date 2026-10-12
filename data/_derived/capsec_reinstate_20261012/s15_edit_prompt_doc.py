# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

edit("docs/agents/claude-agent-publishing.md", [
("""  새 신종·우선주가 공시에 생기면 등재부에 형을 먼저 적는다(같은 테스트의 census 가 빠진 회사를 막는다).
""",
"""  새 신종·우선주가 공시에 생기면 등재부에 형을 먼저 적는다(같은 테스트의 census 가 빠진 회사를 막는다).
  **tier2 분자의 기발행 차감액 = 채권원장(`data/bonds/capital_securities_fy2026h1.json`)의 2022-12-31 이전 발행 잔액**(owner 2026-10-12 밤,
  47사 공통; 인쇄 항목 53/54 는 `*_printed_eok` 참고용). 원장을 고치면(행 추가·발행일 정정) 소진율이 따라 움직이므로 `kics_capital_securities.json`
  (`build_capital_securities_recognition.py`) -> `apply_disclosure_utilization.py` 순으로 다시 돌린다. tier1 인쇄 한도(`tier1_hybrid_limit_eok`)는
  결속 갈래가 없으면 SCR x 10%, 기발행 갈래일 때만 x 15%. 원장 행의 `call_date_unconfirmed`·`estimated` 표지는 타임라인 JSON 으로 그대로 나간다.
"""),
])
