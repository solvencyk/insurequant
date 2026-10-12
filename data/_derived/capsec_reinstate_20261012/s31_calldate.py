# -*- coding: utf-8 -*-
"""Validation ticket 20261013T0205Z / coordinator: exclude ledger bonds by effective maturity = first call date vs the numerator date
(call_date <= numerator date), derived from call_date directly; the ledger flag past_call_outstanding (computed against each row's own
as_of) is still honored but is no longer the only test."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

P = "scripts/capital_utilization_rules.py"
LEGACY_STOCK = '''def legacy_stock(bonds: list[dict], numerator_date: str) -> tuple[float, float]:
    """(신종, 후순위) 기발행 차감액(억원) = 2022-12-31 이전 발행 잔액 중 첫 콜일이 분자 기준일 이후인 채권.
    실효 만기 = 콜일이므로 콜일 <= 기준일 인 채권은 인정 자본이 아니다(원장 표지가 false 여도 뺀다). 발행일 없음 = 기발행."""
    hyb = sub = 0.0
    for b in bonds:
        cd = b.get("call_date") or ""
        if b.get("past_call_outstanding") or (cd and cd <= numerator_date):
            continue
        amt = (b.get("outstanding_mn") or 0) / 100.0
        if b.get("tier") == "hybrid":
            hyb += amt
        else:
            sub += amt
    return hyb, sub


def quarter_end(quarter: str) -> str:
    y, q = quarter.split(".")
    return y + "-" + {"1Q": "03-31", "2Q": "06-30", "3Q": "09-30", "4Q": "12-31"}[q]


def load_ledger(path: Path = LEDGER_PATH, numerator_date: str = "2026-06-30") -> dict[str, dict]:'''

edit(P, [
("           지났는데 상환 안 한 채권(원장 `past_call_outstanding`=true)은 뺀다** - 자본증권의 실효 만기는 콜일이라(forward 도 콜일에 롤오프)",
 "           지났는데 상환 안 한 채권은 뺀다**(콜일 <= 분자 기준일이면 제외 - 콜일에서 직접 판정; 원장 `past_call_outstanding` 표지는 채권 행마다 그\n"
 "           행의 as_of 로 계산돼 분자 기준일과 어긋날 수 있어 보조로만 쓴다) - 자본증권의 실효 만기는 콜일이라(forward 도 콜일에 롤오프)"),
("    미상환(`past_call_outstanding`=true) 채권은 뺀다**(coordinator 정정 2026-10-13).\n",
 "    (`numerator_date`, 기본 2026-06-30) 이전이거나 같은 채권은 뺀다**(coordinator 정정 2026-10-13, validation 20261013T0205Z; 콜일 없음은\n"
 "    날짜로 못 거른다). 원장 `past_call_outstanding`=true 도 뺀다. `compute_quarter` 가 분기 말일로 다시 계산한다.\n"),
("def load_ledger(path: Path = LEDGER_PATH) -> dict[str, dict]:", LEGACY_STOCK),
("""            e["hybrid_legacy"] = e["sub_legacy"] = 0.0
            for b in c.get("bonds") or []:
                if b.get("past_call_outstanding") or (b.get("issue_date") or "") >= LEGACY_CUTOFF:
                    continue
                key = "hybrid_legacy" if b.get("tier") == "hybrid" else "sub_legacy"
                e[key] += (b.get("outstanding_mn") or 0) / 100.0
    return out
""",
"""            e["legacy_bonds"] = [b for b in c.get("bonds") or [] if (b.get("issue_date") or "") < LEGACY_CUTOFF]
            e["hybrid_legacy"], e["sub_legacy"] = legacy_stock(e["legacy_bonds"], numerator_date)
    return out
"""),
("""        t2 = tier2_limit_subject(p, post.get(code, {}), led.get("sub_legacy"), led.get("hybrid_legacy"))""",
"""        if "legacy_bonds" in led:       # 분자 기준일 = 이 분기 말일로 콜 경과 여부를 다시 판정한다
            led_hyb, led_sub = legacy_stock(led["legacy_bonds"], quarter_end(quarter))
        else:
            led_hyb, led_sub = led.get("hybrid_legacy"), led.get("sub_legacy")
        t2 = tier2_limit_subject(p, post.get(code, {}), led_sub, led_hyb)"""),
])
