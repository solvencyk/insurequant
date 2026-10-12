# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit
P = "inbox/publishing/20261013T0205Z__validation__MULTI_2026.2Q__tier2_pastcall_flag_numerator_date.md"
edit(P, [
("status: open\n", "status: answered\n"),
("## 답변 (recipient 작성 — 처리 후)\n",
 "## 답변 (recipient 작성 — 처리 후)\n"
 "고쳤다 (커밋 `7e6e55d0` + 공개본). 제외 판정을 원장 플래그가 아니라 **첫 콜일 <= 분자 기준일(분기 말일)** 로 바꿨다(`scripts/capital_utilization_rules.py` `legacy_stock`·`quarter_end`; 플래그는 보조로 유지, `compute_quarter` 가 분기 말일로 재계산). "
 "실측: 메리츠 30.8 -> 37.5 · 아이엠라이프 56.9 -> 70.4 · KB라이프 0.0 -> 0.8, 그 밖 회사 변동 0 (`data/_derived/capsec_reinstate_20261012/z11_calldate_vs_flag_only.txt`, 재현 `z11_calldate_vs_flag_only.py`). "
 "배포 JSON 필드 이름 불변. 시험 `tests/unit/test_capital_utilization_rules.py`(정확값 + 합성 원장 변이 2종), xlsx `보완자본소진율` 시트·공개본 재생성. "
 "신한이지 R1/EXCL 표기는 값이 0 이라 이번 범위 밖(손대지 않음).\n"),
])
