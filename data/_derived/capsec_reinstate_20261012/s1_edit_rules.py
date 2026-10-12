# -*- coding: utf-8 -*-
"""Requests 3 + 8 edits of scripts/capital_utilization_rules.py (CRLF preserved).

Request 3: tier1 limit printed for companies without a legacy leg = 10% of SCR (was 15%); audit finding.
Request 8 (owner final rule 2026-10-12 night): tier2 numerator deducts the LEDGER outstanding of securities issued on or before
2022-12-31 (hybrid and subordinated separately) for all 47 companies; the issuer's printed items 53/54 are kept only as *_printed_eok.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

P = "scripts/capital_utilization_rules.py"

edit(P, [
# ---- module docstring
("""    (선행) 채권원장에 2022년 이전 후순위가 없는데 항목 54 > 0 이면 그 행은 2023년 이후 신규채를 적은 것
           -> 차감하지 않는다(owner 결정 ②: DB생명·미래에셋).
""",
"""    기발행 차감액 = **채권원장의 2022-12-31 이전 발행 잔액**(신종·후순위 따로, 47사 공통; owner 결정 2026-10-12 밤).
           인쇄된 항목 53/54 는 2023년 이후 발행분이 섞여 있을 수 있어 차감액으로 쓰지 않는다(`*_printed_eok` 참고용).
           R2~R4 는 발행사가 적용 후 열에서 인쇄값을 어떻게 뺐는지의 이름이고, 분자는 모두 같은 항등식으로 닫는다:
           분자 = 항목 47(적용 전 열) - 항목 49 - 원장 2022년 이전 신종 - 원장 2022년 이전 후순위
           (R2 = 적용 후 열 + (인쇄값 - 원장), R3 = 적용 전 열 - 원장, R4 = 적용 후 열 + 인쇄 53 - 원장 과 같은 값).
           옛 DB생명·미래에셋 특례(원장 2022년 이전 후순위 0 이라 차감 0)는 이 일반 규칙에 흡수됐다.
"""),
("""NEW_DEBT_ROW_BASIS = (". 「(기발행 후순위채무)」 행은 2023년 이후 발행 신규채(채권원장에 2022년 이전 후순위 없음)라 "
                      "기발행으로 보지 않고 빼지 않는다(owner 결정 ②).")
""",
"""NEW_DEBT_ROW_BASIS = (". 기발행 차감액은 발행사 인쇄값(항목 53·54)이 아니라 채권원장의 2022년까지 발행 잔액이다 - 인쇄값에는 "
                      "2023년 이후 발행 신규채가 섞여 있을 수 있고 신규채는 기발행이 아니라 한도 대상이다"
                      "(owner 결정 2026-10-12: 기발행 차감은 2022년까지 발행분만).")
"""),
("""    "R2": "발행사가 경과조치 적용 후 열에서 기발행 자본증권(항목 53·54)을 이미 뺐다 - 적용 후 열 사용"
          "([별표22] Ⅵ.1.가.(3))",
    "R3": "발행사가 적용 후 열에서 기발행분을 빼지 않았다(적용 후 = 적용 전) - 항목 53·54 를 뺀다"
          "([별표22] Ⅵ.1.가.(3))",
    "R4": "발행사가 기발행 신종만 빼고 기발행 후순위(항목 54)는 빼지 않았다 - 항목 54 를 더 뺀다",
    "R5": "발행사 고유 차감 방식 - 적용 후 열 인쇄값 사용",""",
"""    "R2": "발행사가 경과조치 적용 후 열에서 기발행 자본증권(항목 53·54)을 이미 뺐다 - 적용 후 열에 (인쇄값 - 원장 2022년까지 "
          "발행 잔액)을 되더한다([별표22] Ⅵ.1.가.(3))",
    "R3": "발행사가 적용 후 열에서 기발행분을 빼지 않았다(적용 후 = 적용 전) - 채권원장 2022년까지 발행 잔액(신종·후순위)을 "
          "뺀다([별표22] Ⅵ.1.가.(3))",
    "R4": "발행사가 기발행 신종만 빼고 기발행 후순위(항목 54)는 빼지 않았다 - 적용 후 열에 인쇄 신종을 되더하고 원장 2022년까지 "
          "발행 잔액(신종·후순위)을 뺀다",
    "R5": "발행사 고유 차감 방식 - 적용 전 열에서 채권원장 2022년까지 발행 잔액(신종·후순위)을 뺀다","""),
("""    return basis + NEW_DEBT_ROW_BASIS if t2.get("legacy_row_is_new_debt") else basis
""",
"""    return basis + NEW_DEBT_ROW_BASIS if t2.get("pre2023_adjusted") else basis
"""),
# ---- load_ledger: hybrid_legacy too
("""        e = out.setdefault(r["원보험사코드"], {"hybrid": 0.0, "sub": 0.0, "sub_legacy": 0.0, "as_of": None})
        bal = r.get("잔액_억") or 0.0
        if r.get("종류") == "신종자본증권":
            e["hybrid"] += bal
        else:
""",
"""        e = out.setdefault(r["원보험사코드"], {"hybrid": 0.0, "sub": 0.0, "sub_legacy": 0.0, "hybrid_legacy": 0.0, "as_of": None})
        bal = r.get("잔액_억") or 0.0
        if r.get("종류") == "신종자본증권":
            e["hybrid"] += bal
            if (r.get("발행일") or "") < LEGACY_CUTOFF:
                e["hybrid_legacy"] += bal
        else:
"""),
("""    sub_legacy 는 s4 와 같은 판정이다: 발행일이 없거나 2023-01-01 전이면 기발행.""",
"""    sub_legacy·hybrid_legacy 는 s4 와 같은 판정이다: 발행일이 없거나 2023-01-01 전이면 기발행(= 2022-12-31 이전 발행 잔액)."""),
# ---- tier2_limit_subject signature + body
("""def tier2_limit_subject(pre: dict, post: dict, bond_sub_legacy_eok: float | None) -> dict:
    \"\"\"보완자본 한도 적용 대상(분자)과 적용 규칙. 메모 s5_final_recompute.py 와 같은 계산이다.

    반환: rule · numerator(경과조치 적용 후 = 현행 규정) · numerator_tfi_off(경과조치 종료 시 관점) ·
          numerator_source · flags · legacy_row_is_new_debt · gross_printing
    \"\"\"
""",
"""def tier2_limit_subject(pre: dict, post: dict, bond_sub_legacy_eok: float | None,
                        bond_hybrid_legacy_eok: float | None = None) -> dict:
    \"\"\"보완자본 한도 적용 대상(분자)과 적용 규칙. 메모 s5_final_recompute.py 와 같은 계산이다.

    기발행 차감액 = 채권원장의 2022-12-31 이전 발행 잔액(신종 `bond_hybrid_legacy_eok` + 후순위 `bond_sub_legacy_eok`) -
    인쇄값 항목 53/54 가 아니다(owner 결정 2026-10-12 밤, 47사 공통). 규칙 판별(R2~R4)만 인쇄값으로 한다 - 발행사가 적용 후 열에서
    무엇을 뺐는지 읽는 것이라서.

    반환: rule · numerator(경과조치 적용 후 = 현행 규정) · numerator_tfi_off(경과조치 종료 시 관점) ·
          numerator_source · flags · pre2023_adjusted(인쇄값 != 원장) · gross_printing ·
          grandfathered_{hybrid,subordinated}_eok(= 차감액, 원장) · *_printed_eok(발행사 인쇄값, 참고)
    \"\"\"
"""),
("""    leg_sub = bond_sub_legacy_eok or 0.0
    flags: list[str] = []

    s54 = s54_printed
    new_debt_row = False
    if s54_printed > TOL and leg_sub <= TOL:
        s54 = 0.0
        new_debt_row = True
        flags.append(f"「(기발행 후순위채무)」 행 {s54_printed:,.2f}억 = 채권원장에 2022년 이전 후순위가 없다 "
                     f"(2023년 이후 신규채) - 차감하지 않음")
    legacy = h53 + s54
""",
"""    led_sub = bond_sub_legacy_eok or 0.0
    led_hyb = bond_hybrid_legacy_eok or 0.0
    flags: list[str] = []

    legacy_printed = h53 + s54_printed           # 발행사 인쇄값(참고; 규칙 판별에만 쓴다)
    legacy = led_hyb + led_sub                   # 차감액 = 채권원장 2022년까지 발행 잔액
    adjusted = abs(legacy_printed - legacy) > TOL
    if adjusted:
        flags.append(f"기발행 차감액 = 채권원장 2022년까지 발행 잔액 {legacy:,.2f}억(신종 {led_hyb:,.2f} + 후순위 {led_sub:,.2f}); "
                     f"발행사 인쇄값 {legacy_printed:,.2f}억(항목 53 {h53:,.2f} + 54 {s54_printed:,.2f})과 다름")
"""),
("""        if legacy <= TOL:
            rule = "R1" if gross else "R-none"
            if s54_printed <= TOL:
                n2, source = max(0.0, d1), src_post
            else:
                n2, source = max(0.0, d0), src_pre
        elif close(p1, p0 - legacy):
            rule, n2, source = "R2", max(0.0, d1), src_post
        elif close(p1, p0):
            rule, n2, source = "R3", max(0.0, d0 - legacy), src_pre + " - 항목 53 - 항목 54"
            flags.append("R3 발행사가 적용후 열에서 기발행분을 안 뺌 - 항목 53+54 차감([별표22] Ⅵ.1.가.(3))")
            if d0 - legacy < -TOL:
                flags.append("항목 53+54 > 한도 적용 전: 기발행 행이 인정액이 아님(액면·오기 가능)")
        elif s54 > TOL and close(p1, p0 - h53):
            rule, n2, source = "R4", max(0.0, d1 - s54), src_post + " - 항목 54"
            flags.append("R4 발행사가 기발행 신종만 뺌 - 기발행 후순위 추가 차감")
        else:
            rule, n2, source = "R5", max(0.0, d1), src_post
            flags.append("R5 발행사 고유 차감 방식(적용후 열 인쇄값 사용)")
""",
"""        # 규칙 이름은 발행사가 인쇄값을 어떻게 뺐는지(인쇄값으로 판별). 분자는 전부 같은 항등식으로 닫는다:
        #   분자 = 적용 전 열(d0) - 원장 2022년까지 발행 잔액(legacy)
        # R2 적용 후 열 d1 = d0 - 인쇄값 이므로 d1 + (인쇄값 - 원장) 과 같은 값이다(허용오차 안에서).
        src_led = f" - 채권원장 2022년까지 발행 잔액(신종 {led_hyb:,.2f} + 후순위 {led_sub:,.2f})"
        if legacy_printed <= TOL:
            rule = "R1" if gross else "R-none"
        elif close(p1, p0 - legacy_printed):
            rule = "R2"
        elif close(p1, p0):
            rule = "R3"
            flags.append("R3 발행사가 적용후 열에서 기발행분을 안 뺌 - 원장 2022년까지 발행분 차감([별표22] Ⅵ.1.가.(3))")
        elif s54_printed > TOL and close(p1, p0 - h53):
            rule = "R4"
            flags.append("R4 발행사가 기발행 신종만 뺌 - 원장 기준 후순위까지 차감")
        else:
            rule = "R5"
            flags.append("R5 발행사 고유 차감 방식 - 적용 전 열에서 원장 2022년까지 발행 잔액을 뺌")
        n2 = max(0.0, d0 - legacy)
        source = src_pre + src_led
        if d0 - legacy < -TOL:
            flags.append("원장 2022년까지 발행 잔액 > 한도 적용 전: 0 으로 둠(원장·인쇄 불일치 확인 필요)")
"""),
("""        "legacy_row_is_new_debt": new_debt_row,
""",
"""        "pre2023_adjusted": adjusted,
        "grandfathered_hybrid_eok": round(led_hyb, 2),
        "grandfathered_subordinated_eok": round(led_sub, 2),
        "grandfathered_hybrid_printed_eok": round(h53, 2),
        "grandfathered_subordinated_printed_eok": round(s54_printed, 2),
"""),
# ---- compute_quarter passes hybrid_legacy
("""        t2 = tier2_limit_subject(p, post.get(code, {}), led.get("sub_legacy"))
""",
"""        t2 = tier2_limit_subject(p, post.get(code, {}), led.get("sub_legacy"), led.get("hybrid_legacy"))
"""),
# ---- request 3: tier1 limit printed
("""    if legacy <= 0 and new_basic <= 0:
        leg, num_b, lim_b = None, 0.0, lim15
""",
"""    if legacy <= 0 and new_basic <= 0:
        # 결속 갈래가 없다(기발행 0 이고 기본자본형 신규도 0): 인쇄되는 인정한도는 원칙 한도 10% 다. 예전에는 15% 를 찍어
        # 화면 부제(「10% 가 원칙, 15% 는 기발행분만」)와 어긋났다 - 독립 감사 지적(티켓 20261012T2235Z 요청 3). 소진율 0.0 은 불변.
        leg, num_b, lim_b = None, 0.0, lim10
"""),
])
