# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit
edit("scripts/capital_utilization_rules.py", [
("""        ao = r.get("잔액기준일")
        if ao and (e["as_of"] is None or ao < e["as_of"]):
            e["as_of"] = ao
    return out
""",
"""        ao = r.get("잔액기준일")
        if ao and (e["as_of"] is None or ao < e["as_of"]):
            e["as_of"] = ao
    # 기발행 차감액(2022-12-31 이전 발행 잔액)은 채권원장 원본에서 직접 낸다: 콜일이 지났는데 상환 안 한 채권(past_call_outstanding)은
    # 실효 만기(= 콜일)가 지났으므로 인정 자본이 아니다 -> 차감액에서 뺀다. 발행일 없음 = 기발행(위 판정과 같다).
    if BONDS_PATH.exists():
        for c in json.loads(BONDS_PATH.read_text(encoding="utf-8")).get("companies", []):
            e = out.get(c["code"])
            if e is None:
                continue
            e["hybrid_legacy"] = e["sub_legacy"] = 0.0
            for b in c.get("bonds") or []:
                if b.get("past_call_outstanding") or (b.get("issue_date") or "") >= LEGACY_CUTOFF:
                    continue
                key = "hybrid_legacy" if b.get("tier") == "hybrid" else "sub_legacy"
                e[key] += (b.get("outstanding_mn") or 0) / 100.0
    return out
"""),
("""        src_led = f" - 채권원장 2022년까지 발행 잔액(신종 {led_hyb:,.2f} + 후순위 {led_sub:,.2f})\"""",
 """        src_led = f" - 채권원장 2022년까지 발행 잔액(콜 경과 미상환 제외; 신종 {led_hyb:,.2f} + 후순위 {led_sub:,.2f})\""""),
])
