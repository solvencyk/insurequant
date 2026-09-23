# -*- coding: utf-8 -*-
"""자본비율전망(forward)과 자본성증권 인정액이 같은 기준 위에 있는지 대조한다.

owner 질의 2026-09-23: "법정만기일 기준으로 인정비율 바꿨으면 forward outlook 도 바꿔야
하는 거 아니냐."

forward(`forward_capital_simulation.py`)는 `kics_capital_securities.json` 을 읽지 않는다.
`data/bonds/*.json` 에서 `effective_call_date = call_date or legal_maturity` 를 뽑아 그 날짜에
`outstanding_mn` **전액**을 가용자본에서 뺀다(체감 없음, 절벽). 즉 forward 의 전제는
"콜 전까지 100% · 콜에 전액 이탈" 이다.

그래서 물어야 할 것은 "두 모델의 산식이 같은가" 가 아니라 **"콜 시점에 인정율이 1.0 인가"**
다. 1.0 이면 forward 의 절벽과 체감이 맞물리고(이중계상도 공백도 없다), 1.0 이 아니면 어긋난다.

각 후순위채의 **자기 콜 날짜**에서 구(콜 기준)·신(법정만기 기준) 인정율을 계산해 대조한다.
"""
from __future__ import annotations

import io
import json
import math
import sys
from collections import Counter
from datetime import date
from pathlib import Path

_ORIG = sys.stdout
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.build_capital_securities_recognition import _pdate  # noqa: E402

_keep = sys.stdout            # 빌더가 import 때 갈아끼운 래퍼 — GC 되면 버퍼가 닫힌다
sys.stdout = _ORIG
sys.stdout.reconfigure(encoding="utf-8")


def ladder(maturity: date | None, as_of: date) -> float:
    """[별표22] III.3.다.(2)(1) 계단식 체감 — 빌더의 tier2_recognition_rate 와 같은 산식."""
    if maturity is None:
        return 1.0
    years = (maturity - as_of).days / 365.25
    if years >= 5:
        return 1.0
    if years <= 0:
        return 0.0
    return max(0.0, 1.0 - 0.20 * math.ceil(5 - years))


doc = json.loads((REPO / "data/bonds/capital_securities_fy2026h1.json").read_text(encoding="utf-8"))
AS_OF = date(2026, 6, 30)
old_at_call, new_at_call = Counter(), Counter()
past_call, n = [], 0

for c in doc["companies"]:
    for b in c.get("bonds") or []:
        if (b.get("outstanding_mn") or 0) <= 0 or b.get("tier") == "hybrid":
            continue
        call, legal = _pdate(b.get("call_date")), _pdate(b.get("legal_maturity"))
        n += 1
        if call is None:
            continue
        # forward 가 이 채권을 전액 빼는 바로 그 날짜에서 두 규칙의 인정율
        old_at_call[ladder(call, call)] += 1          # 구: 경제적 만기 = 콜
        new_at_call[ladder(legal, call)] += 1         # 신: 경제적 만기 = 법정만기
        if call <= AS_OF:
            past_call.append((c["company"], b["name"][:36], b["call_date"],
                              b.get("legal_maturity"), (b["outstanding_mn"] or 0) / 100.0,
                              ladder(legal, AS_OF)))

print(f"후순위 {n}건 (콜 있는 건만 대조)\n")
print("forward 가 전액 차감하는 '콜 날짜' 에서의 인정율 분포")
print(f"  구 규칙(경제적 만기=콜)      : {dict(old_at_call)}")
print(f"  신 규칙(경제적 만기=법정만기) : {dict(new_at_call)}")
print("\n  -> 신 규칙에서 1.0 이면 forward 의 절벽과 체감이 정확히 맞물린다"
      "(콜까지 100%, 콜에 이탈).")
print("     구 규칙에서는 콜 시점에 이미 0.0 이었다 = forward 는 100%로 세는데"
      " 인정표는 0 으로 세고 있었다.\n")

print(f"콜이 이미 지났는데 잔액이 남은 후순위 {len(past_call)}건 "
      f"— forward 는 이미 전액 뺐고, 인정표는 아직 인정한다")
tot = 0.0
for co, nm, cd, lm, amt, rate in sorted(past_call, key=lambda x: -x[4]):
    tot += amt * rate
    print(f"  {co:<12}{nm:<38} 콜{cd} 법정{lm} 잔액{amt:>8,.0f}억 "
          f"현재인정율{rate:.1f} -> 인정액{amt * rate:>8,.0f}억")
print(f"  forward 가 0 으로 보는데 규정상 아직 인정되는 금액 합계: {tot:,.0f}억")
