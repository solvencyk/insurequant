# -*- coding: utf-8 -*-
"""Public/master xlsx notes for the tier2 sheet (request 8). Only note text changes in scripts/build_master_xlsx.py
(no schema change: no new rows/columns)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

edit("scripts/build_master_xlsx.py", [
('''_TIER2_UTIL_NOTE = ("분자 = 보완자본 - 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 - 기발행 "
                    "자본증권(공통적용 경과조치), 분모 = 총요구자본(경과조치 적용 전) × 50% "
                    "([별표22] Ⅲ.2.마·Ⅵ.1.가.(3)·Ⅵ.1.라).")''',
'''_TIER2_UTIL_NOTE = ("분자 = 보완자본 - 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 - 기발행 "
                    "자본증권(공통적용 경과조치; 2022년 12월 31일까지 발행한 신종·후순위의 채권원장 잔액만 뺀다 - 발행사가 "
                    "인쇄한 기발행 금액에는 2023년 이후 발행분이 섞여 있을 수 있어 쓰지 않는다), 분모 = 총요구자본"
                    "(경과조치 적용 전) × 50% ([별표22] Ⅲ.2.마·Ⅵ.1.가.(3)·Ⅵ.1.라).")'''),
('''            if field == "tier1_overflow_into_tier2_eok":
                note = _TIER2_OVERFLOW_NOTE
''',
'''            if field == "tier1_overflow_into_tier2_eok":
                note = _TIER2_OVERFLOW_NOTE
            if field in ("grandfathered_hybrid_eok", "grandfathered_subordinated_eok") and r.get(field) is not None:
                printed = r.get(field.replace("_eok", "_printed_eok"))
                note = ("보완자본 분자에서 뺀 기발행 금액 = 채권원장의 2022년 12월 31일까지 발행한 "
                        + ("신종" if "hybrid" in field else "후순위") + "자본증권 잔액"
                        + (f" (발행사가 경영공시에 인쇄한 금액 {printed:,.2f}억원은 2023년 이후 발행분이 섞여 있을 수 있어 쓰지 않음)"
                           if printed is not None else ""))
'''),
])
