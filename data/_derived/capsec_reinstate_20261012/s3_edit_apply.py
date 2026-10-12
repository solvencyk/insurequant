# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit
edit("scripts/apply_disclosure_utilization.py", [
("""    if res.get("item54") is not None:
        row["grandfathered_subordinated_eok"] = res["item54"]
    if res.get("item53") is not None:
        row["grandfathered_hybrid_eok"] = res["item53"]
""",
"""    # 2026-10-12 밤 owner 결정(요청 8): 기발행 차감액 = 채권원장 2022-12-31 이전 발행 잔액. 이 두 필드는 화면(K-ICS.html
    # 「경과조치 기발행 후순위 X억원」)이 읽는 필드라 **차감액(원장)** 을 싣고, 발행사 인쇄값은 *_printed_eok 에 따로 둔다.
    if res.get("item54") is not None or t2["grandfathered_subordinated_eok"] > 0:
        row["grandfathered_subordinated_eok"] = t2["grandfathered_subordinated_eok"]
        row["grandfathered_subordinated_printed_eok"] = t2["grandfathered_subordinated_printed_eok"]
    if res.get("item53") is not None or t2["grandfathered_hybrid_eok"] > 0:
        row["grandfathered_hybrid_eok"] = t2["grandfathered_hybrid_eok"]
        row["grandfathered_hybrid_printed_eok"] = t2["grandfathered_hybrid_printed_eok"]
    row["grandfathered_basis"] = "채권원장 2022-12-31 이전 발행 잔액(신종·후순위 각각). 발행사 인쇄값은 *_printed_eok"
"""),
("""        "numerator": ("보완자본 한도 적용 전 = 보완자본 - 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 - "
                      "기발행 자본증권 (item47 경과조치 적용 후 열, 발행사 인쇄 관행 정규화 R0~R5 = 행의 rule)"),""",
"""        "numerator": ("보완자본 한도 적용 전 = 보완자본(item47 적용 전 열) - 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 "
                      "초과분 - 기발행 자본증권(채권원장의 2022-12-31 이전 발행 잔액, 신종·후순위 각각; 발행사 인쇄 관행 "
                      "정규화 R0~R5 = 행의 rule, 인쇄 항목 53·54 는 차감액으로 쓰지 않음 - owner 2026-10-12)"),"""),
])
