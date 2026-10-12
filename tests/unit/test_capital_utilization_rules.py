# -*- coding: utf-8 -*-
"""자본성증권 인정한도 소진율 규정 근거 산식(2026-10-12 owner 채택) - 단위시험 + 변이시험.

산식: `scripts/capital_utilization_rules.py` (정본 근거 data/_derived/capital_utilization_definition_20261012/
definition_memo.md). 등재부: `data/bonds/capital_tier_registry.json`.

세 가지를 매 push 강제한다(pre-push 훅이 `tests/unit/` 을 통째로 돌린다):
  1. 산식이 owner 가 채택한 메모 재현표(recompute_47.csv + §3.2 표)를 47사 전부 그대로 낸다.
  2. 배포본 `kics_tier{1,2}_utilization.json` 이 그 산식의 결과와 같다 - 옛 빌더(compute_tier2 -> wire -> sync)를
     다시 돌려 옛 정의로 조용히 되돌아가면 여기서 막힌다.
  3. 변이시험: 정규화 규칙 하나를 지우거나(그 규칙의 사례가 다른 값으로 떨어지는지) 등재부의 형(type)을 바꾸면
     결과가 실제로 바뀐다 - 규칙·등재부가 장식이 아니라 숫자를 움직이는 근거임을 확인한다.
"""
from __future__ import annotations

import copy
import csv
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import capital_utilization_rules as R  # noqa: E402
from solvency.validation import kics_json_rules as K  # noqa: E402

MEMO_CSV = ROOT / "data" / "_derived" / "capital_utilization_definition_20261012" / "recompute_47.csv"
QUARTER = "2026.2Q"

# 메모 §3.2 「새 정의로 2026.2Q tier1」 표 (owner 채택 결정 ③) + 2026-10-12 재공개 라운드 재분류(티켓
# 20261012T2030Z, owner 「분류 확정」): 하나생명 제1회(스텝업 구조)·푸본 600억·농협생명 제5회·코리안리 제5/6회가
# 보완자본형으로 확정되어 기본자본 자본증권에서 빠진다 -> KR0097 238.2 -> 0.0 · KR1000 205.1 -> 94.0 ·
# KR0104 72.7 -> 48.5 · KR0083 42.1 -> 17.3 (이 네 값이 바뀐 이유는 전부 이 재분류다 - 느슨하게 푼 것이 아니다).
# 흥국생명은 2022-12 전환우선주로 기본자본형 확정(81.4 불변).
# 2026-10-12 발행사 처리 기준 라운드(티켓 20261012T2115Z, owner 「회사에서 그렇게 분류했으면 회사 분류를 따르는 게 맞다」):
# 증권별 X 검정(data/_derived/capsec_reinstate_20261012/x2_per_security_x_test.txt)에서 하나생명 제1회와 교보 2024-11 은
# 발행사가 기본자본형으로 처리한 것으로 나와 type=tier1 로 바꿨다 -> KR0097 0.0 -> 238.2 (이 한 값이 바뀐 이유는 전부 이
# 재분류다 - 느슨하게 푼 것이 아니다). 교보는 결속하는 쪽이 기발행 70.1 이라 숫자 불변(기본자본형 신규 56.8).
T1_MEMO = {"KR0068": 0.0, "KR0072": 0.0, "KR0050": 0.0, "KR0032": 0.0, "KR0005": 62.4, "KR0073": 70.1,
           "KR0002": 53.1, "KR0011": 151.6, "KR0097": 238.2, "KR0001": 18.9, "KR0003": 14.3, "KR0099": 12.2,
           "KR0076": 221.7, "KR1000": 94.0, "KR0104": 48.5, "KR0083": 17.3, "KR0071": 81.4, "KR0008": 0.5}
# 아직 미확정이 남은 회사 = 푸본의 채권원장에 없는 50억(2024.4Q~)뿐. 결속하지 않아 상한 = 하한.
T1_UNCONFIRMED = {"KR0083": 17.3}   # code -> 보완자본형일 때 값(범위 아래 끝)


@pytest.fixture(scope="module")
def records():
    return json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ledger():
    return R.load_ledger()


@pytest.fixture(scope="module")
def registry():
    return R.load_registry()


@pytest.fixture(scope="module")
def computed(records, ledger, registry):
    return R.compute_quarter(records, QUARTER, ledger, registry)


@pytest.fixture(scope="module")
def memo():
    with MEMO_CSV.open(encoding="utf-8-sig", newline="") as fh:
        return {r["code"]: r for r in csv.DictReader(fh)}


@pytest.fixture(scope="module")
def deployed():
    """배포본 두 파일. 메모 재현은 2026.2Q 에 고정이지만 배포본 대조·census 는 **배포본의 분기**로 한다 -
    다음 분기를 배포해도 이 두 시험이 낡은 분기를 검사하지 않게."""
    t1 = json.loads((ROOT / "kics_tier1_utilization.json").read_text(encoding="utf-8"))
    t2 = json.loads((ROOT / "kics_tier2_utilization.json").read_text(encoding="utf-8"))
    assert t1["quarter"] == t2["quarter"]
    return t1, t2


@pytest.fixture(scope="module")
def computed_deployed(records, ledger, registry, deployed, computed):
    q = deployed[0]["quarter"]
    return computed if q == QUARTER else R.compute_quarter(records, q, ledger, registry)


def _f(v):
    return None if v in (None, "") else float(v)


# --------------------------------------------------------------------------- 1. 메모 재현
def test_scope_map_is_the_gate_function_not_a_copy():
    assert R._tier2_i47_scope_map is K._tier2_i47_scope_map
    assert R.TIER2_LIMIT_RATIO == K.TIER2_LIMIT_RATIO == 0.5


# owner 결정 2026-10-12 밤(요청 8): 기발행 차감액 = 채권원장의 2022-12-31 이전 발행 잔액(신종·후순위 각각), 인쇄값 항목 53/54 아님.
# 메모 재현표(recompute_47.csv)는 인쇄값 기준이라 아래 19사는 이 결정으로 숫자가 바뀐다 - (규칙, 분자, 소진율) 정확값을 박제한다
# (느슨하게 푼 것이 아니다: 이 19개 값 밖의 28사는 메모 값 그대로). 근거 표 data/_derived/capsec_reinstate_20261012/z3_tier2_before_after_47.*
# 2026-10-13 coordinator 정정: 콜일이 지났는데 상환 안 한 채권(past_call_outstanding)은 차감액에서 뺀다 -> 현대해상·DB손해는 메모 값 그대로로 복귀,
# 농협생명 21.1(콜 경과 2,800 제외)·롯데 58.6·흥국화재 53.3·악사 29.2.
# 미래에셋·DB생명은 숫자 불변이고 규칙 이름만 R1/R-none -> R3 (옛 특례가 이 일반 규칙에 흡수됨).
T2_OWNER_20261012_NIGHT = {
    "KR0001": ("R2", 9724.88, 30.8), "KR0002": ("R2", 8288.25, 46.6), "KR0003": ("R2", 6188.4, 58.6),
    "KR0005": ("R2", 6039.32, 53.3), "KR0010": ("R2", 7384.19, 20.5),
    "KR0032": ("R2", 6908.29, 102.8), "KR0049": ("R2", 370.65, 29.2),
    "KR0068": ("R3", 56155.44, 74.8), "KR0070": ("R2", 6081.29, 70.4), "KR0071": ("R2", 5227.17, 37.0),
    "KR0073": ("R2", 27137.98, 51.5), "KR0076": ("R5", 2109.54, 56.9), "KR0079": ("R3", 2930.93, 24.5),
    "KR0082": ("R3", 2563.95, 31.6), "KR0083": ("R2", 5639.79, 73.1), "KR0099": ("R2", 0.0, 0.0),
    "KR0104": ("R4", 3625.57, 21.1), "KR1000": ("R2", 7105.18, 60.9), "KR1011": ("R2", 2749.46, 76.2),
}


def test_tier2_reproduces_memo_for_all_47(computed, memo):
    assert len(memo) == 47
    bad = []
    for code, m in memo.items():
        t2 = computed[code]["t2"]
        exp_num, exp_pct = _f(m["t2_num_reg"]), _f(m["t2_pct_reg"])
        exp_rule = m["t2_rule"]
        if code in T2_OWNER_20261012_NIGHT:
            exp_rule, exp_num, exp_pct = T2_OWNER_20261012_NIGHT[code]
        if t2["rule"] != exp_rule:
            bad.append((code, "rule", exp_rule, t2["rule"]))
        if (exp_num is None) != (t2["numerator"] is None) or (exp_num is not None and abs(exp_num - t2["numerator"]) > 0.011):
            bad.append((code, "numerator", exp_num, t2["numerator"]))
        if (exp_pct is None) != (t2["pct"] is None) or (exp_pct is not None and abs(exp_pct - t2["pct"]) > 0.051):
            bad.append((code, "pct", exp_pct, t2["pct"]))
        if t2["scope"] != m["gate_item47_scope"]:
            bad.append((code, "item47 scope", m["gate_item47_scope"], t2["scope"]))
    assert not bad, bad


def test_tier1_reproduces_memo_table_for_all_47(computed, memo):
    bad = [(c, T1_MEMO.get(c, 0.0), computed[c]["t1"]["pct"]) for c in memo
           if abs(T1_MEMO.get(c, 0.0) - computed[c]["t1"]["pct"]) > 0.051]
    assert not bad, bad


def test_unconfirmed_companies_carry_upper_bound_flag_and_range(computed):
    for code, low in T1_UNCONFIRMED.items():
        t1 = computed[code]["t1"]
        assert t1["type_unconfirmed"] is True, code
        assert t1["pct"] == T1_MEMO[code], code                    # 상한(기본자본형, 분모 10%)
        assert t1["pct_if_unconfirmed_tier2"] == low, code         # 보완자본형이면 = 기발행 쪽
    confirmed = [c for c in T1_MEMO if c not in T1_UNCONFIRMED]
    assert not [c for c in confirmed if computed[c]["t1"]["type_unconfirmed"]]


def test_no_tfi_table_is_null_with_reason_not_zero(computed):
    t2 = computed["KR1010"]["t2"]      # 교보라이프플래닛: 47~54 원문 부재
    assert t2["rule"] == "NA" and t2["numerator"] is None and t2["pct"] is None


def test_swiss_re_is_zero_not_undisclosed(computed):
    t2 = computed["KR1102"]["t2"]      # 결정 ⑤: 항목 47 인쇄값 0 그대로
    assert t2["rule"] == "R-none" and t2["numerator"] == 0.0 and t2["pct"] == 0.0


# --------------------------------------------------------------------------- 2. 배포본 == 산식
def test_deployed_json_equals_rules(deployed, computed_deployed):
    t1, t2 = deployed
    computed = computed_deployed
    bad = []
    for row in t1["results"]:
        c = computed[row["code"]]["t1"]
        for fld, exp in (("utilization_pct", c["pct"]), ("tier1_hybrid_recognized_eok", c["binding_numerator_eok"]),
                         ("tier1_hybrid_limit_eok", c["binding_limit_eok"]), ("binding_leg", c["binding_leg"]),
                         ("type_unconfirmed", c["type_unconfirmed"])):
            if row.get(fld) != exp:
                bad.append(("t1", row["code"], fld, exp, row.get(fld)))
    for row in t2["results"]:
        c = computed[row["code"]]["t2"]
        for fld, exp in (("utilization_pct", c["pct"]), ("numerator_eok", c["numerator"]), ("rule", c["rule"]),
                         ("tier2_limit_eok", c["limit"])):
            if row.get(fld) != exp:
                bad.append(("t2", row["code"], fld, exp, row.get(fld)))
        # 화면이 읽는 필드는 차감액(원장 2022년 이전 잔액), 인쇄값은 *_printed_eok (owner 결정 2026-10-12 밤)
        for fld, key in (("grandfathered_subordinated_eok", "grandfathered_subordinated_eok"),
                         ("grandfathered_hybrid_eok", "grandfathered_hybrid_eok"),
                         ("grandfathered_subordinated_printed_eok", "grandfathered_subordinated_printed_eok"),
                         ("grandfathered_hybrid_printed_eok", "grandfathered_hybrid_printed_eok")):
            if fld in row and row[fld] != c[key]:
                bad.append(("t2", row["code"], fld, c[key], row[fld]))
        if (c["rule"] == "NA") != (row.get("reason") == R.REASON_NO_TFI_TABLE):
            bad.append(("t2", row["code"], "reason", c["rule"], row.get("reason")))
    assert not bad, bad


# --------------------------------------------------------------------------- 3a. 규칙 변이시험(합성 사례)
# 각 규칙의 사례는 그 규칙이 없으면(다음 분기로 떨어지면) 다른 숫자가 나오도록 고른다 - `fallback` 이
# 규칙을 지웠을 때 나올 값(인쇄값 그대로)이고, 결과는 그것과 달라야 한다.
RULE_CASES = [
    # id, pre, post, ledger_legacy_sub, ledger_legacy_hybrid, rule, numerator, fallback(규칙이 없을 때)
    ("R0", {3: 0.0, 47: 500.0, 49: 0.0}, {47: 500.0}, 0.0, 0.0, "R0", 0.0, 500.0),
    ("NA", {3: 364.0}, {}, 0.0, 0.0, "NA", None, 0.0),
    ("R1", {3: 1000.0, 47: 1000.0, 49: 600.0}, {47: 1000.0}, 0.0, 0.0, "R1", 400.0, 1000.0),
    ("R2", {3: 5000.0, 47: 3000.0, 49: 1000.0, 53: 500.0, 54: 1500.0}, {47: 1000.0}, 1500.0, 500.0, "R2", 1000.0, 3000.0),
    ("R3", {3: 5000.0, 47: 5000.0, 49: 2000.0, 53: 300.0, 54: 700.0}, {47: 5000.0}, 700.0, 300.0, "R3", 2000.0, 3000.0),
    ("R4", {3: 9000.0, 47: 4000.0, 49: 3000.0, 53: 500.0, 54: 1000.0}, {47: 3500.0}, 1000.0, 500.0, "R4", 2500.0, 3500.0),
    ("R5", {3: 9000.0, 47: 4000.0, 49: 3000.0, 53: 500.0, 54: 0.0}, {47: 2000.0}, 1500.0, 500.0, "R5", 2000.0, 4000.0),
    ("R-none", {3: 9000.0, 47: 2000.0, 49: 7000.0}, {47: 2000.0}, 0.0, 0.0, "R-none", 2000.0, None),
]


@pytest.mark.parametrize("cid,pre,post,leg_sub,leg_hyb,rule,num,fallback", RULE_CASES, ids=[c[0] for c in RULE_CASES])
def test_each_rule_fires_and_is_load_bearing(cid, pre, post, leg_sub, leg_hyb, rule, num, fallback):
    out = R.tier2_limit_subject(pre, post, leg_sub, leg_hyb)
    assert out["rule"] == rule
    assert out["numerator"] == num
    if fallback is not None:
        assert out["numerator"] != fallback, f"{cid}: 규칙을 지워도 같은 값 - 장식 규칙"


def test_new_debt_row_is_the_general_ledger_rule_not_a_special_case():
    # owner 결정 2026-10-12 밤: DB생명형 「(기발행 후순위채무)」 행 3,000 인데 채권원장에 2022년 이전 후순위가 없다 -> 차감액 0.
    # 옛 특례(항목 54 인쇄값을 0 으로 보는 선행 판정)는 "차감액 = 원장 2022년 이전 잔액" 이라는 일반 규칙에 흡수됐다.
    pre, post = {3: 9000.0, 47: 2500.0, 49: 6000.0, 54: 3000.0}, {47: 2500.0}
    kept = R.tier2_limit_subject(pre, post, 0.0, 0.0)
    assert kept["rule"] == "R3" and kept["numerator"] == 2500.0 and kept["pre2023_adjusted"]
    assert kept["grandfathered_subordinated_eok"] == 0.0 and kept["grandfathered_subordinated_printed_eok"] == 3000.0
    # 변이: 원장에 2022년 이전 후순위가 있다고 바꾸면 그만큼 빼게 되어 숫자가 바뀐다(= 원장이 숫자를 움직인다)
    subtracted = R.tier2_limit_subject(pre, post, 3000.0, 0.0)
    assert subtracted["numerator"] == 0.0 != kept["numerator"]


def test_printed_53_54_never_set_the_deduction():
    # R3 형(발행사가 적용 후 열에서 안 뺌): 인쇄값을 바꿔도 분자는 같다 - 차감액은 오직 원장이다.
    base = {3: 5000.0, 47: 5000.0, 49: 2000.0, 53: 300.0, 54: 700.0}
    a = R.tier2_limit_subject(base, {47: 5000.0}, 700.0, 300.0)
    b = R.tier2_limit_subject({**base, 53: 900.0, 54: 100.0}, {47: 5000.0}, 700.0, 300.0)
    assert a["rule"] == b["rule"] == "R3" and a["numerator"] == b["numerator"] == 2000.0
    assert b["grandfathered_hybrid_printed_eok"] == 900.0 and b["grandfathered_hybrid_eok"] == 300.0
    # 반대로 원장이 바뀌면 분자가 바뀐다
    assert R.tier2_limit_subject(base, {47: 5000.0}, 1700.0, 300.0)["numerator"] == 1000.0


def _bond_ledger_pre2023():
    """채권원장 원본(data/bonds)에서 독립적으로 낸 {code: (신종, 후순위)} 2022-12-31 이전 발행 잔액(억원). 빌더(kics_capital_securities.json)를 거치지 않는다."""
    doc = json.loads((ROOT / "data" / "bonds" / "capital_securities_fy2026h1.json").read_text(encoding="utf-8"))
    out = {}
    for c in doc["companies"]:
        h = s = 0.0
        for b in c.get("bonds") or []:
            # 콜일이 지났는데 상환 안 한 채권(past_call_outstanding)은 실효 만기(콜일)가 지났으므로 뺀다(coordinator 정정 2026-10-13)
            if (b.get("issue_date") or "") < "2023-01-01" and not b.get("past_call_outstanding"):
                amt = (b.get("outstanding_mn") or 0) / 100.0
                if b.get("tier") == "hybrid":
                    h += amt
                else:
                    s += amt
        out[c["code"]] = (h, s)
    return out


def test_tier2_numerator_is_item47_minus_49_minus_ledger_pre2023_for_all_47(computed, records):
    """owner 결정 2026-10-12 밤: 분자 = 항목 47(적용 전 열) - 항목 49(총액 인쇄 시) - 원장 2022년 이전 신종 - 원장 2022년 이전 후순위.
    같은 값을 원장 원본과 마스터에서 따로 다시 계산해 47사 전부 대조한다(R2~R4 의 되더하기 경로가 이 항등식을 깨지 않았는지)."""
    led = _bond_ledger_pre2023()
    pre, _post, _n = R.load_disclosure(records, QUARTER)
    bad, n = [], 0
    for code, c in computed.items():
        t2 = c["t2"]
        if t2["rule"] in ("R0", "NA"):
            continue
        p = pre[code]
        gross = p.get(49) is not None and p[49] > R.TOL and R.close(p.get(47), p.get(3))
        d0 = p[47] - p[49] if gross else p[47]
        h, s = led.get(code, (0.0, 0.0))
        exp = max(0.0, d0 - h - s)
        n += 1
        if abs(exp - t2["numerator"]) > 0.011:
            bad.append((code, exp, t2["numerator"]))
        if abs(h - t2["grandfathered_hybrid_eok"]) > 0.011 or abs(s - t2["grandfathered_subordinated_eok"]) > 0.011:
            bad.append((code, "deduction", (h, s), (t2["grandfathered_hybrid_eok"], t2["grandfathered_subordinated_eok"])))
    assert n >= 20 and not bad, bad


def test_past_call_outstanding_bonds_are_not_deducted(ledger, computed):
    """coordinator 정정 2026-10-13: 콜일이 이미 지났는데 상환 안 한 2022년 이전 채권은 인정 자본이 아니므로 기발행 차감액에서 뺀다
    (자본증권의 실효 만기 = 콜일; 발행사도 DB손해·현대해상·농협생명의 기발행 줄에 넣지 않는다). 원장 플래그만 쓴다."""
    assert ledger["KR0011"]["sub_legacy"] == 0.0 and ledger["KR0009"]["sub_legacy"] == 0.0          # 1,700 · 2,330 (2022 콜 경과)
    assert ledger["KR0104"]["sub_legacy"] == 8300.0                                                  # 11,100 - 공모채 1-2회 2,800
    assert ledger["KR0003"]["sub_legacy"] == 1390.55                                                 # 2,289.18 - 08차 898.63 (콜 2025-05)
    assert ledger["KR0005"]["hybrid_legacy"] == 1200.0                                               # 2,120 - 제1회 920 (콜 2021-12)
    assert ledger["KR0004"]["sub_legacy"] == 0.0 and ledger["KR0049"]["sub_legacy"] == 0.0         # 엠지손해 680 · 악사 JPY 458.8
    assert (computed["KR0011"]["t2"]["pct"], computed["KR0009"]["t2"]["pct"], computed["KR0104"]["t2"]["pct"]) == (38.9, 70.5, 21.1)


def test_past_call_exclusion_is_load_bearing(tmp_path, monkeypatch):
    """변이: 콜 경과 미상환 표지를 무시하면 차감액이 늘어난다(합성 원장)."""
    doc = {"companies": [{"code": "KR9999", "bonds": [
        {"tier": "subordinated", "issue_date": "2017-05-25", "outstanding_mn": 100000, "past_call_outstanding": True},
        {"tier": "subordinated", "issue_date": "2019-05-25", "outstanding_mn": 50000, "past_call_outstanding": False},
        {"tier": "hybrid", "issue_date": "2016-12-29", "outstanding_mn": 92000, "past_call_outstanding": True},
        {"tier": "hybrid", "issue_date": "2022-03-01", "outstanding_mn": 30000},
        {"tier": "subordinated", "issue_date": "2023-03-01", "outstanding_mn": 70000}]}]}
    p = tmp_path / "bonds.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps({"rows": [{"원보험사코드": "KR9999", "종류": "후순위채", "잔액_억": 1.0, "발행일": "2019-05-25",
                                          "잔액기준일": "2026-06-30"}]}), encoding="utf-8")
    monkeypatch.setattr(R, "BONDS_PATH", p)
    got = R.load_ledger(rows)
    assert got["KR9999"]["sub_legacy"] == 500.0 and got["KR9999"]["hybrid_legacy"] == 300.0
    src = (ROOT / "scripts" / "capital_utilization_rules.py").read_text(encoding="utf-8")
    assert src.count('if b.get("past_call_outstanding") or (b.get("issue_date") or "") >= LEGACY_CUTOFF:') == 1
    ns: dict = {"__name__": "rules_mutant", "__file__": str(ROOT / "scripts" / "capital_utilization_rules.py")}
    exec(compile(src.replace('if b.get("past_call_outstanding") or (b.get("issue_date") or "") >= LEGACY_CUTOFF:',
                             'if (b.get("issue_date") or "") >= LEGACY_CUTOFF:'), "rules_mutant", "exec"), ns)
    ns["BONDS_PATH"] = p
    bad = ns["load_ledger"](rows)
    assert bad["KR9999"]["sub_legacy"] == 1500.0 and bad["KR9999"]["hybrid_legacy"] == 1220.0   # 표지를 무시하면 차감이 늘어난다


def test_owner_decision_effects_named_in_the_ticket(computed):
    """티켓 20261012T2235Z 요청 6(= owner 결정 2026-10-12 밤)이 이름 댄 회사: 메리츠 0.2 -> 30.8 · 흥국생명 10.6 -> 37.0 ·
    농협손해 103.9 -> 102.8 · 한화생명 70.5 -> 74.8 · 푸본 86.6 -> 73.1. 미래에셋·DB생명은 숫자 불변(옛 특례가 일반 규칙에 흡수)."""
    pct = {c: computed[c]["t2"]["pct"] for c in computed}
    assert (pct["KR0001"], pct["KR0071"], pct["KR0032"], pct["KR0068"], pct["KR0083"]) == (30.8, 37.0, 102.8, 74.8, 73.1)
    assert (pct["KR0079"], pct["KR0082"]) == (24.5, 31.6)
    assert computed["KR0079"]["t2"]["pre2023_adjusted"] and computed["KR0082"]["t2"]["pre2023_adjusted"]


# --------------------------------------------------------------------------- 3a-2. 기본자본 인정한도 표시(요청 3)
def test_tier1_printed_limit_is_the_denominator_that_gives_the_percent():
    """독립 감사 지적(티켓 20261012T2235Z 요청 3): 결속 갈래가 없는 회사(기발행 0, 기본자본형 신규 0)가 한도를 SCR x 15% 로 인쇄했다.
    소진율 0.0 은 같지만 화면 부제(「10% 가 원칙, 15% 는 기발행분만」)와 어긋난다. 인쇄 한도 = 소진율의 분모 = 결속 갈래의 한도다."""
    none = R.tier1_binding(0.0, 0.0, 1000.0, {})
    assert none["binding_leg"] is None and none["pct"] == 0.0
    assert none["binding_limit_eok"] == 100.0 != 150.0               # 10% (예전에는 150.0)
    legacy = R.tier1_binding(100.0, 100.0, 1000.0, {})
    assert legacy["binding_leg"] == "legacy_15" and legacy["binding_limit_eok"] == 150.0   # 15% 는 기발행 갈래에만
    new = R.tier1_binding(100.0, 0.0, 1000.0, {})
    assert new["binding_leg"] == "basic_10" and new["binding_limit_eok"] == 100.0


def test_deployed_tier1_printed_limit_matches_binding_leg_for_all_47(deployed):
    t1, _ = deployed
    bad = []
    for r in t1["results"]:
        want = r["tier1_legacy_limit_eok"] if r.get("binding_leg") == "legacy_15" else r["tier1_basic_new_limit_eok"]
        if r["tier1_hybrid_limit_eok"] != want:
            bad.append((r["code"], r.get("binding_leg"), r["tier1_hybrid_limit_eok"], want))
        if r.get("binding_leg") is None and r["tier1_hybrid_limit_eok"] != round(r["scr_eok"] * 0.10, 2):
            bad.append((r["code"], "not 10% of SCR", r["tier1_hybrid_limit_eok"]))
    assert len(t1["results"]) == 47 and not bad, bad


# --------------------------------------------------------------------------- 3b. 등재부 변이시험(실데이터)
def _t1(records, ledger, registry, code):
    return R.compute_quarter(records, QUARTER, ledger, registry)[code]["t1"]


def _flip(registry, code, frm, to):
    reg = copy.deepcopy(registry)
    n = 0
    for s in reg["companies"][code]["securities"]:
        if s["type"] == frm:
            s["type"] = to
            n += 1
    assert n, (code, frm)
    return reg


@pytest.mark.parametrize("code,frm,to,before,after", [
    ("KR0068", "tier2", "tier1", 0.0, 204.4),     # 한화생명: 보완자본형 신종이 분자에 들어가면 204.4
    ("KR0011", "tier1", "tier2", 151.6, 0.0),     # DB손해: 기본자본형을 보완자본형으로 보면 0
    ("KR1000", "tier2", "tier1", 94.0, 205.1),    # 코리안리: 확정된 보완자본형 신규 4,800억을 기본자본형으로 보면 205.1
    ("KR0104", "tier2", "tier1", 48.5, 72.7),     # 농협생명: 제5회 2,500억 (확정 전 상한이던 값)
    ("KR0097", "tier1", "tier2", 238.2, 0.0),     # 하나생명: 발행사가 기본자본형으로 처리(2026-10-12). 보완자본형으로 되돌리면 0
    ("KR0032", "tier2", "tier1", 0.0, 334.7),     # 농협손해
])
def test_registry_type_is_load_bearing(records, ledger, registry, code, frm, to, before, after):
    assert _t1(records, ledger, registry, code)["pct"] == before
    assert _t1(records, ledger, _flip(registry, code, frm, to), code)["pct"] == after


def test_removing_a_registry_entry_changes_the_number(records, ledger, registry):
    reg = copy.deepcopy(registry)
    del reg["companies"]["KR0073"]                 # 교보: 2023 보완자본형 4,985 를 모르면 신규 10,968 / 10%
    assert _t1(records, ledger, reg, "KR0073")["pct"] == 104.1
    assert _t1(records, ledger, registry, "KR0073")["pct"] == 70.1


def test_kyobo_2024_security_is_tier1_and_load_bearing_for_the_strict_leg(records, ledger, registry):
    """교보 2024-11 은 발행사 처리대로 기본자본형: 기본자본형 신규 5,983 / SCR x 10% = 56.8%. 결속은 기발행 70.1 이라
    소진율은 그대로지만 이 한 줄이 바뀌면 신규 쪽 숫자가 바뀐다(분류가 숫자를 움직인다)."""
    t1 = _t1(records, ledger, registry, "KR0073")
    assert t1["pct"] == 70.1 and t1["binding_leg"] == "legacy_15"
    assert t1["basic_new_eok"] == 5983.01 and t1["basic_new_pct"] == 56.8
    flipped = _t1(records, ledger, _flip(registry, "KR0073", "tier1", "tier2"), "KR0073")
    assert flipped["basic_new_pct"] == 0.0 and flipped["pct"] == 70.1


def test_unconfirmed_flag_comes_from_registry(records, ledger, registry):
    reg = copy.deepcopy(registry)
    for s in reg["companies"]["KR0083"]["securities"]:
        s["type_unconfirmed"] = False
    assert _t1(records, ledger, reg, "KR0083")["type_unconfirmed"] is False
    assert _t1(records, ledger, registry, "KR0083")["type_unconfirmed"] is True


def test_reclassified_securities_are_confirmed_and_flag_cleared(registry):
    """2026-10-12 재분류: 이 세 회사의 신규 신종은 보완자본형(발행조건 기준; 발행사 처리는 issuer_check 에 기록) - 미확정 표지가
    남아 있으면 안 된다. 하나생명 제1회는 발행사 처리대로 기본자본형이라 따로 본다."""
    for code, issue in (("KR0083", "2023-02-28"), ("KR0104", "2023-01-31"),
                        ("KR1000", "2023-03-16"), ("KR1000", "2024-10-11")):
        hit = [s for s in registry["companies"][code]["securities"] if s.get("issue_date") == issue]
        assert len(hit) == 1, (code, issue)
        assert hit[0]["type"] == "tier2" and hit[0]["type_unconfirmed"] is False, (code, issue)
        assert "unconfirmed_reason" not in hit[0], (code, issue)


def test_issuer_type_only_where_it_differs_and_is_documented(registry):
    """issuer_type 은 type 과 다를 때만 적는다(forward 기본자본 경로가 이 필드로 갈린다). 2026-10-12 owner 결정으로 type 이
    발행사 처리를 따르게 되어 지금은 쓰는 증권이 0건이다 - 누가 다시 어긋난 증권을 등재하면 이 시험이 알린다."""
    found = {}
    for code, ent in registry["companies"].items():
        for s in ent["securities"]:
            if "issuer_type" in s:
                assert s["issuer_type"] in ("legacy_tfi", "tier1", "tier2"), (code, s["name"])
                assert s["issuer_type"] != s["type"], (code, s["name"])
                assert s.get("evidence"), (code, s["name"])
                found.setdefault(code, []).append(s["issue_date"])
    assert found == {}, found


def _issue_quarter(issue_date: str):
    if re.fullmatch(r"\d{4}\.\dQ", issue_date):                          # "2026.2Q" 형 표기(채권원장 미등재 신규 건)
        return issue_date
    m = re.match(r"(\d{4})-(\d{2})-\d{2}", issue_date)
    return f"{m.group(1)}.{(int(m.group(2)) - 1) // 3 + 1}Q" if m else None   # "2016-12-29~..." 같은 묶음 표기는 None


def test_registry_type_matches_issuer_x_test(registry):
    """등재부 type 이 증권별 발행사 처리 검정(x2)과 같다: 확인 = tier2 유지, 반증 = tier1, 판정 불가 = 현 분류 유지 + 그렇게 기록.
    x2 를 다시 돌리지 않고 등재부만 고치거나, 반대로 검정 결과를 바꾸고 등재부를 안 맞추면 여기서 막힌다."""
    x2 = json.loads((ROOT / "data/_derived/capsec_reinstate_20261012/x2_per_security_x_test.json").read_text(encoding="utf-8"))
    n = 0
    for ev in x2["events"]:
        secs = [s for s in registry["companies"][ev["code"]]["securities"]
                if s.get("issue_date") and _issue_quarter(s["issue_date"]) == ev["quarter"] and s["type"] != "legacy_tfi"]
        assert secs, ev["security"]
        for s in secs:
            n += 1
            if ev["verdict"] == "CONFIRMED_T2":
                assert s["type"] == "tier2" and "보완자본형 확인" in s["issuer_check"], (ev["security"], s["name"])
            elif ev["verdict"] == "CONTRADICTED_T2":
                assert s["type"] == "tier1" and "기본자본형 확인" in s["issuer_check"], (ev["security"], s["name"])
            else:
                raise AssertionError(("inconclusive events are not allowed in x2 events list", ev["security"]))
    assert n == 12, n          # 이벤트 11건 = 증권 12건(한화생명 2024.3Q 두 건)
    # 첫 공시 분기가 발행 분기인 증권 · 발행 분기가 다른 변동과 겹친 증권: 수준 시험 결과를 등재부가 그대로 말한다
    expect = {("KR0097", "2023-03-31"): ("tier1", "기본자본형 확인"), ("KR1000", "2023-03-16"): ("tier2", "보완자본형 확인"),
              ("KR0083", "2023-02-28"): ("tier2", "판정 불가"), ("KR0104", "2023-01-31"): ("tier2", "판정 불가"),
              ("KR1000", "2024-10-11"): ("tier2", "판정 불가")}
    for (code, issue), (ty, word) in expect.items():
        hit = [s for s in registry["companies"][code]["securities"] if s.get("issue_date") == issue]
        assert len(hit) == 1 and hit[0]["type"] == ty and word in hit[0]["issuer_check"], (code, issue)
    # 어느 tier2 증권이든 issuer_check 가 있어야 한다(근거 없는 보완자본형 금지)
    bare = [(c, s["name"]) for c, e in registry["companies"].items() for s in e["securities"]
            if s["type"] == "tier2" and not s.get("issuer_check")]
    assert not bare, bare


def test_x_test_panel_equals_master(records):
    """x2 의 입력 패널(x1_panel.json)이 지금 마스터와 같다 - 마스터가 바뀌었는데 증빙이 낡은 채 남는 것을 막는다."""
    panel = json.loads((ROOT / "data/_derived/capsec_reinstate_20261012/x1_panel.json").read_text(encoding="utf-8"))
    cell = {}
    for r in records:
        if r["원보험사코드"] in panel and r["항목번호"] in (6, 13, 49):
            cell[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = _f(str(r["값"]).replace(",", ""))
    bad = []
    for code, qs in panel.items():
        for q, v in qs.items():
            for key, no in (("i6", 6), ("i13", 13), ("i49", 49)):
                if v[key] != cell.get((code, q, no)):
                    bad.append((code, q, key, v[key], cell.get((code, q, no))))
    assert not bad, bad[:5]


# --------------------------------------------------------------------------- 4. 등재부 위생·census
def test_registry_schema(registry):
    allowed = {"legacy_tfi", "tier1", "tier2"}
    for code, ent in registry["companies"].items():
        assert ent.get("securities"), code
        for s in ent["securities"]:
            assert s["type"] in allowed, (code, s.get("name"))
            assert isinstance(s.get("amount_eok"), (int, float)), (code, s.get("name"))
            assert s.get("evidence"), (code, s.get("name"))
            if s.get("type_unconfirmed"):
                assert s["type"] == "tier1", (code, s["name"])          # 미확정 = 보수적 상한
                assert s.get("unconfirmed_reason"), (code, s["name"])


def test_every_company_with_post_2023_securities_is_registered(computed_deployed, registry):
    """보통주 이외 자본증권 중 기발행이 아닌 금액이 있는 회사는 등재부에 기발행 아닌 증권이 있어야 한다.
    없으면 그 금액이 근거 없이 기본자본형(상한)으로 들어간다 - 새 발행사가 조용히 끼어드는 자리."""
    missing = []
    for code, c in computed_deployed.items():
        t1 = c["t1"]
        if t1 is None or t1["securities_eok"] - t1["legacy_eok"] <= R.TOL:
            continue
        secs = (registry["companies"].get(code) or {}).get("securities") or []
        if not [s for s in secs if s["type"] in ("tier1", "tier2")]:
            missing.append((code, c["name"], round(t1["securities_eok"] - t1["legacy_eok"], 2)))
    assert not missing, missing


def test_tier2_overflow_field_is_the_tier1_overflow_for_all_47(deployed, records):
    """kics_tier2_utilization.json 의 tier1_overflow_into_tier2_eok(공개 시트 「기본자본 한도초과분의 보완자본 재분류」)는
    예전 채권원장 추정(발행액 - SCR x 15%, 하나생명 665.7)이 갱신 없이 남아 있었다. 지금은 기본자본 소진율과 같은 출처의
    한도 초과액(tier1 json 의 tier1_hybrid_overflow_eok)과 47사 전부 같아야 한다. 하나생명은 공시에서 따로 손계산한다."""
    t1, t2 = deployed
    a = {r["code"]: r["tier1_hybrid_overflow_eok"] for r in t1["results"]}
    b = {r["code"]: r["tier1_overflow_into_tier2_eok"] for r in t2["results"]}
    assert set(a) == set(b) and len(b) == 47
    assert {c for c in a if a[c] != b[c]} == set(), {c: (a[c], b[c]) for c in a if a[c] != b[c]}
    q = t1["quarter"]
    item = {r["항목번호"]: float(str(r["값"]).replace(",", "")) for r in records
            if r["원보험사코드"] == "KR0097" and r["공시분기"] == q and r["항목번호"] in (6, 14)}
    assert b["KR0097"] == round(item[6] - item[14] * 0.10, 2) == 1043.6      # 1,799 - 755.4
