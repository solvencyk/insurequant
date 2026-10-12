# -*- coding: utf-8 -*-
"""자본성증권 인정한도 소진율 - 규정 근거 산식 (owner 채택 2026-10-12).

정본 근거: `data/_derived/capital_utilization_definition_20261012/definition_memo.md`
(보험업감독업무시행세칙 [별표22] Ⅲ.2.다·마, Ⅵ.1.가·라 / 재현 스크립트 s1~s6). 이 모듈은 그 메모의
§3.1(보완자본 R0~R5)과 §3.2(기본자본 결속 시험 + 증권별 계층 등재부)를 **그대로** 옮긴 순수 함수다.
파일을 쓰지 않는다 - 쓰는 쪽은 `scripts/apply_disclosure_utilization.py`(배포본 47사)와
`scripts/add_reinsurers_to_capsec_panels.py`(재보사 행 신설)다.

## 보완자본(tier2) 인정한도 소진율

    분자 = 보완자본 - Ⅲ.2.다.(3) 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분
                    - Ⅵ.1.가.(2) 기발행 자본증권            (= 경과조치 표 「보완자본 한도 적용 전」 적용 후 열)
    분모 = 총요구자본(항목 14, 경과조치 적용 **전**) x 50%     [Ⅲ.2.마, Ⅵ.1.라]

발행사마다 「보완자본 한도 적용 전」 행의 인쇄 관행이 달라 다음 규칙으로 정규화한다(메모 §3.1, s5):

    R0      보완자본(항목 3) = 0                                  -> 0
    NA      항목 47 원문 부재(경과조치 표 미공시)                   -> 값 없음 + reason
    R1      항목 47 = 보완자본 총액(항목 3) 이고 항목 49 > 0       -> 항목 49 차감
    R2      적용후 = 적용전 - 항목 53 - 항목 54                    -> 적용후 열
    R3      적용후 = 적용전 (기발행분 안 뺌)                        -> 적용전 - 항목 53 - 항목 54
    R4      적용후 = 적용전 - 항목 53 (후순위만 안 뺌)              -> 적용후 - 항목 54
    R5      그 밖의 발행사 고유 차감                                -> 적용후 열 인쇄값
    R-none  기발행분 없음                                           -> 인쇄값 그대로
    (선행) 채권원장에 2022년 이전 후순위가 없는데 항목 54 > 0 이면 그 행은 2023년 이후 신규채를 적은 것
           -> 차감하지 않는다(owner 결정 ②: DB생명·미래에셋).

## 기본자본(tier1) 자본증권 인정한도 소진율 (두 한도 중 먼저 차는 쪽)

    기발행 = min(항목 53, 항목 6)                                  한도 총요구자본 x 15% (Ⅵ.1.가.(1), 2032 까지)
    기본자본형 신규 = 항목 6 - 기발행 - 보완자본형 금액(등재부)    한도 총요구자본 x 10% (Ⅲ.2.다.(1)②)
    소진율 = max(기발행 / 15% 한도, 기본자본형 신규 / 10% 한도)

보완자본형(Ⅲ.2.다.(2), 스텝업 등) 신종은 기본자본 자본증권이 아니므로 분자에서 뺀다. 증권별 형 판정은
`data/bonds/capital_tier_registry.json` 이 정본이다 - 확정 못 한 증권은 기본자본형으로 보고(보수적 상한)
`type_unconfirmed` 를 단다.

항목 47 스코프(발행사가 항목 49 를 항목 47 안에 넣어 인쇄하는가)는 게이트의 판정 함수
`kics_json_rules._tier2_i47_scope_map` 을 **import** 해서 대조한다(다시 타이핑하지 않는다).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from solvency.validation.kics_json_rules import (  # noqa: E402  (import, do not retype)
    TIER2_LIMIT_RATIO,
    _group_records,
    _tier2_i47_scope_map,
)

TOL = 2.0                  # 억원 - kics_json_rules.evaluate 기본 허용오차와 같다(s5 와 동일)
TIER1_LEGACY_RATE = 0.15   # Ⅵ.1.가.(1) 기발행분(공통적용 경과조치, 2032-12-31 까지)
TIER1_RATE = 0.10          # Ⅲ.2.다.(1)② 원칙 한도(조건부자본증권 15% - 보험사 발행 사례 없음)
LEGACY_CUTOFF = "2023-01-01"   # K-ICS 시행일. 이 날 전 발행 = 기발행
REASON_NO_TFI_TABLE = "경과조치 표 미공시"
REGISTRY_PATH = ROOT / "data" / "bonds" / "capital_tier_registry.json"
LEDGER_PATH = ROOT / "kics_capital_securities.json"

RULE_BASIS = {
    "R0": "보완자본(항목 3)이 0 이라 한도 적용 대상도 0",
    "R1": "발행사가 「보완자본 한도 적용 전」 행에 보완자본 총액을 인쇄 - [별표22] Ⅲ.2.마 단서대로 "
          "해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분(항목 49)을 뺀다",
    "R2": "발행사가 경과조치 적용 후 열에서 기발행 자본증권(항목 53·54)을 이미 뺐다 - 적용 후 열 사용"
          "([별표22] Ⅵ.1.가.(3))",
    "R3": "발행사가 적용 후 열에서 기발행분을 빼지 않았다(적용 후 = 적용 전) - 항목 53·54 를 뺀다"
          "([별표22] Ⅵ.1.가.(3))",
    "R4": "발행사가 기발행 신종만 빼고 기발행 후순위(항목 54)는 빼지 않았다 - 항목 54 를 더 뺀다",
    "R5": "발행사 고유 차감 방식 - 적용 후 열 인쇄값 사용",
    "R-none": "기발행 자본증권 없음 - 인쇄값 그대로",
    "NA": "항목 47~54(공통적용 경과조치 표) 원문 부재 - 산출 불가",
}
NEW_DEBT_ROW_BASIS = (". 「(기발행 후순위채무)」 행은 2023년 이후 발행 신규채(채권원장에 2022년 이전 후순위 없음)라 "
                      "기발행으로 보지 않고 빼지 않는다(owner 결정 ②).")


def rule_basis(t2: dict) -> str:
    """행의 rule_basis 문장. 기발행 후순위 행을 신규채로 본 경우(DB생명·미래에셋) 그 사실을 덧붙인다."""
    basis = RULE_BASIS[t2["rule"]]
    return basis + NEW_DEBT_ROW_BASIS if t2.get("legacy_row_is_new_debt") else basis


def num(v):
    """경영공시 셀 -> float. '△' 는 음수, 빈 칸·'-'·'nan' 은 None (s5 의 f() 와 같다)."""
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s in ("", "-", "None", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def close(a, b, tol: float = TOL) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def pct(n, d):
    return None if n is None or not d or d <= 0 else round(n / d * 100.0, 1)


# --------------------------------------------------------------------------- 입력
def load_disclosure(records, quarter: str) -> tuple[dict, dict, dict]:
    """(pre, post, names) - pre/post = {code: {항목번호: float|None}}. post 는 `값_적용후` 키가 있는 행만."""
    pre: dict[str, dict] = {}
    post: dict[str, dict] = {}
    names: dict[str, str] = {}
    for r in records:
        if r.get("공시분기") != quarter:
            continue
        code = r["원보험사코드"]
        names.setdefault(code, r.get("원수사명"))
        pre.setdefault(code, {})[r["항목번호"]] = num(r.get("값"))
        if "값_적용후" in r:
            post.setdefault(code, {})[r["항목번호"]] = num(r.get("값_적용후"))
    return pre, post, names


def item47_scope_map(records) -> dict[str, str]:
    """게이트(`kics_json_rules`)와 같은 함수로 낸 회사별 항목 47 스코프. 없는 회사는 'EXCL'."""
    return _tier2_i47_scope_map(_group_records(records), TOL)


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, dict]:
    """채권원장(증권 한 건 단위) -> 회사별 {hybrid, sub, sub_legacy, as_of}.

    sub_legacy 는 s4 와 같은 판정이다: 발행일이 없거나 2023-01-01 전이면 기발행.
    as_of 는 그 회사 행 중 가장 오래된 잔액기준일(코멘트가 정직할 수 있는 한계).
    """
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    for r in json.loads(path.read_text(encoding="utf-8")).get("rows", []):
        e = out.setdefault(r["원보험사코드"], {"hybrid": 0.0, "sub": 0.0, "sub_legacy": 0.0, "as_of": None})
        bal = r.get("잔액_억") or 0.0
        if r.get("종류") == "신종자본증권":
            e["hybrid"] += bal
        else:
            e["sub"] += bal
            if (r.get("발행일") or "") < LEGACY_CUTOFF:
                e["sub_legacy"] += bal
        ao = r.get("잔액기준일")
        if ao and (e["as_of"] is None or ao < e["as_of"]):
            e["as_of"] = ao
    return out


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- 보완자본
def tier2_limit_subject(pre: dict, post: dict, bond_sub_legacy_eok: float | None) -> dict:
    """보완자본 한도 적용 대상(분자)과 적용 규칙. 메모 s5_final_recompute.py 와 같은 계산이다.

    반환: rule · numerator(경과조치 적용 후 = 현행 규정) · numerator_tfi_off(경과조치 종료 시 관점) ·
          numerator_source · flags · legacy_row_is_new_debt · gross_printing
    """
    i3 = pre.get(3)
    p0 = pre.get(47)
    p1 = post.get(47)
    if p1 is None:
        p1 = p0
    l49 = pre.get(49)
    h53 = pre.get(53) or 0.0
    s54_printed = pre.get(54) or 0.0
    leg_sub = bond_sub_legacy_eok or 0.0
    flags: list[str] = []

    s54 = s54_printed
    new_debt_row = False
    if s54_printed > TOL and leg_sub <= TOL:
        s54 = 0.0
        new_debt_row = True
        flags.append(f"「(기발행 후순위채무)」 행 {s54_printed:,.2f}억 = 채권원장에 2022년 이전 후순위가 없다 "
                     f"(2023년 이후 신규채) - 차감하지 않음")
    legacy = h53 + s54

    rule = None
    n2 = None
    n2_pre = None
    source = None
    gross = False
    if i3 is not None and abs(i3) <= TOL:
        rule, n2, n2_pre, source = "R0", 0.0, 0.0, "보완자본(항목 3) = 0"
    elif p0 is None:
        rule = "NA"
    else:
        gross = l49 is not None and l49 > TOL and close(p0, i3)
        d0 = p0 - l49 if gross else p0
        post_is_gross = gross and (close(p1, i3) or close(p1, p0))
        d1 = (p1 - l49) if post_is_gross else p1
        src_post = "항목 47 적용후" + (" - 항목 49" if post_is_gross else "")
        src_pre = "항목 47 적용전" + (" - 항목 49" if gross else "")
        if post.get(47) is None:
            src_post = src_post.replace("적용후", "적용후(미인쇄 -> 적용전 값)")
        if gross:
            flags.append("R1 발행사가 한도 적용 전 행에 보완자본 총액 인쇄(해약환급금 초과분 포함) - 항목 49 차감")
        n2_pre = max(0.0, d0)
        if legacy <= TOL:
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
    return {
        "rule": rule,
        "numerator": None if n2 is None else round(n2, 2),
        "numerator_tfi_off": None if n2_pre is None else round(n2_pre, 2),
        "numerator_source": source,
        "flags": flags,
        "legacy_row_is_new_debt": new_debt_row,
        "gross_printing": gross,
    }


# --------------------------------------------------------------------------- 기본자본
def registry_entry(registry: dict, code: str) -> dict:
    return (registry.get("companies") or {}).get(code) or {}


def tier1_binding(item6, item53, scr, entry: dict) -> dict | None:
    """기본자본 자본증권 소진율(두 한도 중 먼저 차는 쪽). 항목 6·SCR 이 없으면 None."""
    if item6 is None or not scr or scr <= 0:
        return None
    sec = max(item6, 0.0)                      # 스위스리 -3 = 자본잉여금 음수, 자본증권 아님
    legacy = min(item53 or 0.0, sec)
    secs = entry.get("securities") or []
    t2_amt = sum(((s.get("amount_eok") or 0.0) for s in secs if s.get("type") == "tier2"), 0.0)
    excluded = min(t2_amt, max(0.0, sec - legacy))
    new_basic = max(0.0, sec - legacy - t2_amt)
    lim15 = scr * TIER1_LEGACY_RATE
    lim10 = scr * TIER1_RATE
    p_leg = legacy / lim15 * 100.0
    p_new = new_basic / lim10 * 100.0
    if legacy <= 0 and new_basic <= 0:
        leg, num_b, lim_b = None, 0.0, lim15
    elif p_leg >= p_new:
        leg, num_b, lim_b = "legacy_15", legacy, lim15
    else:
        leg, num_b, lim_b = "basic_10", new_basic, lim10
    unconfirmed = [s for s in secs if s.get("type_unconfirmed")]
    unconf_t1 = sum(((s.get("amount_eok") or 0.0) for s in unconfirmed if s.get("type") == "tier1"), 0.0)
    is_unconfirmed = bool(unconfirmed and new_basic > TOL)
    # 미확정 증권이 보완자본형으로 판명될 때의 값(범위의 아래 끝) - 상한(pct)과 함께 보여 줄 수 있게
    pct_low = round(max(p_leg, max(0.0, new_basic - unconf_t1) / lim10 * 100.0), 1) if is_unconfirmed else None
    return {
        "securities_eok": round(sec, 2),
        "legacy_eok": round(legacy, 2),
        "legacy_limit_eok": round(lim15, 2),
        "legacy_pct": round(p_leg, 1),
        "basic_new_eok": round(new_basic, 2),
        "basic_new_limit_eok": round(lim10, 2),
        "basic_new_pct": round(p_new, 1),
        "excluded_tier2_type_eok": round(excluded, 2),
        "binding_leg": leg,
        "binding_numerator_eok": round(num_b, 2),
        "binding_limit_eok": round(lim_b, 2),
        "overflow_eok": round(max(0.0, legacy - lim15) + max(0.0, new_basic - lim10), 2),
        "pct": round(max(p_leg, p_new), 1),
        "type_unconfirmed": is_unconfirmed,
        "pct_if_unconfirmed_tier2": pct_low,
        "unconfirmed_names": [s.get("name") for s in unconfirmed],
    }


def no_capital_securities(item6, item53, item54, ledger_entry: dict | None) -> bool:
    """「발행 없음」 - 보통주 이외 자본증권(항목 6)·기발행 행(53·54)·채권원장 잔액이 모두 0."""
    led = ledger_entry or {}
    return ((item6 or 0.0) <= TOL and (item53 or 0.0) <= TOL and (item54 or 0.0) <= TOL
            and (led.get("hybrid") or 0.0) <= TOL and (led.get("sub") or 0.0) <= TOL)


def compute_quarter(records, quarter: str, ledger: dict, registry: dict) -> dict[str, dict]:
    """한 분기 전 회사의 tier1·tier2 결과. {code: {"name", "scr", "t1": dict|None, "t2": dict, ...}}.

    apply_disclosure_utilization.py(배포본 쓰기)와 tests/unit/test_capital_utilization_rules.py(배포본 재현
    검사)가 같은 함수를 부른다 - 산식을 두 곳에 두지 않는다.
    """
    pre, post, names = load_disclosure(records, quarter)
    scope = item47_scope_map(records)
    out: dict[str, dict] = {}
    for code, p in pre.items():
        led = ledger.get(code) or {}
        scr = p.get(14)
        lim2 = round(scr * TIER2_LIMIT_RATIO, 2) if scr else None
        t2 = tier2_limit_subject(p, post.get(code, {}), led.get("sub_legacy"))
        t2["limit"] = lim2
        t2["pct"] = pct(t2["numerator"], lim2)
        t2["pct_tfi_off"] = pct(t2["numerator_tfi_off"], lim2)
        t2["scope"] = scope.get(code, "EXCL")
        out[code] = {
            "name": names.get(code),
            "scr": scr,
            "item3": p.get(3), "item6": p.get(6), "item49": p.get(49), "item53": p.get(53), "item54": p.get(54),
            "t1": tier1_binding(p.get(6), p.get(53), scr, registry_entry(registry, code)),
            "t2": t2,
            "no_capital_securities": no_capital_securities(p.get(6), p.get(53), p.get(54), led),
        }
    return out
