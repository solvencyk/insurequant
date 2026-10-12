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
# 흥국생명은 2022-12 전환우선주로 기본자본형 확정(81.4 불변). 교보 2024 건은 type=tier2(발행조건 스텝업)로
# 바뀌었지만 결속하는 쪽이 기발행 70.1 이라 숫자 불변.
T1_MEMO = {"KR0068": 0.0, "KR0072": 0.0, "KR0050": 0.0, "KR0032": 0.0, "KR0005": 62.4, "KR0073": 70.1,
           "KR0002": 53.1, "KR0011": 151.6, "KR0097": 0.0, "KR0001": 18.9, "KR0003": 14.3, "KR0099": 12.2,
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


def test_tier2_reproduces_memo_for_all_47(computed, memo):
    assert len(memo) == 47
    bad = []
    for code, m in memo.items():
        t2 = computed[code]["t2"]
        exp_num, exp_pct = _f(m["t2_num_reg"]), _f(m["t2_pct_reg"])
        if t2["rule"] != m["t2_rule"]:
            bad.append((code, "rule", m["t2_rule"], t2["rule"]))
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
        if (c["rule"] == "NA") != (row.get("reason") == R.REASON_NO_TFI_TABLE):
            bad.append(("t2", row["code"], "reason", c["rule"], row.get("reason")))
    assert not bad, bad


# --------------------------------------------------------------------------- 3a. 규칙 변이시험(합성 사례)
# 각 규칙의 사례는 그 규칙이 없으면(다음 분기로 떨어지면) 다른 숫자가 나오도록 고른다 - `fallback` 이
# 규칙을 지웠을 때 나올 값(인쇄값 그대로)이고, 결과는 그것과 달라야 한다.
RULE_CASES = [
    # id, pre, post, ledger_legacy_sub, rule, numerator, fallback(규칙이 없을 때)
    ("R0", {3: 0.0, 47: 500.0, 49: 0.0}, {47: 500.0}, 0.0, "R0", 0.0, 500.0),
    ("NA", {3: 364.0}, {}, 0.0, "NA", None, 0.0),
    ("R1", {3: 1000.0, 47: 1000.0, 49: 600.0}, {47: 1000.0}, 0.0, "R1", 400.0, 1000.0),
    ("R2", {3: 5000.0, 47: 3000.0, 49: 1000.0, 53: 500.0, 54: 1500.0}, {47: 1000.0}, 1500.0, "R2", 1000.0, 3000.0),
    ("R3", {3: 5000.0, 47: 5000.0, 49: 2000.0, 53: 300.0, 54: 700.0}, {47: 5000.0}, 700.0, "R3", 2000.0, 3000.0),
    ("R4", {3: 9000.0, 47: 4000.0, 49: 3000.0, 53: 500.0, 54: 1000.0}, {47: 3500.0}, 1000.0, "R4", 2500.0, 3500.0),
    ("R5", {3: 9000.0, 47: 4000.0, 49: 3000.0, 53: 500.0, 54: 0.0}, {47: 2000.0}, 0.0, "R5", 2000.0, 4000.0),
    ("R-none", {3: 9000.0, 47: 2000.0, 49: 7000.0}, {47: 2000.0}, 0.0, "R-none", 2000.0, None),
]


@pytest.mark.parametrize("cid,pre,post,leg_sub,rule,num,fallback", RULE_CASES, ids=[c[0] for c in RULE_CASES])
def test_each_rule_fires_and_is_load_bearing(cid, pre, post, leg_sub, rule, num, fallback):
    out = R.tier2_limit_subject(pre, post, leg_sub)
    assert out["rule"] == rule
    assert out["numerator"] == num
    if fallback is not None:
        assert out["numerator"] != fallback, f"{cid}: 규칙을 지워도 같은 값 - 장식 규칙"


def test_new_debt_legacy_row_precheck_is_load_bearing():
    # DB생명형: 「(기발행 후순위채무)」 행 3,000 인데 채권원장에 2022년 이전 후순위가 없다 -> 빼지 않는다.
    pre, post = {3: 9000.0, 47: 2500.0, 49: 6000.0, 54: 3000.0}, {47: 2500.0}
    kept = R.tier2_limit_subject(pre, post, 0.0)
    assert kept["rule"] == "R-none" and kept["numerator"] == 2500.0 and kept["legacy_row_is_new_debt"]
    # 변이: 원장에 기발행 후순위가 있다고 바꾸면 그 행을 빼게 되어 숫자가 바뀐다(= 결정 ② 가 숫자를 움직인다)
    subtracted = R.tier2_limit_subject(pre, post, 3000.0)
    assert subtracted["numerator"] != kept["numerator"]


def test_real_new_debt_companies_follow_owner_decision_2(computed, memo):
    for code in ("KR0082", "KR0079"):           # DB생명 31.6 · 미래에셋 24.5 (빼면 둘 다 0)
        t2 = computed[code]["t2"]
        assert t2["legacy_row_is_new_debt"], code
        assert t2["pct"] == _f(memo[code]["t2_pct_reg"]), code
        assert t2["pct"] != _f(memo[code]["t2_pct_alt_if_printed_legacy_row_subtracted"]), code


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
    ("KR0097", "tier2", "tier1", 0.0, 238.2),     # 하나생명: 스텝업 구조 -> 보완자본형. 기본자본형이면 종전 238.2
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


def test_unconfirmed_flag_comes_from_registry(records, ledger, registry):
    reg = copy.deepcopy(registry)
    for s in reg["companies"]["KR0083"]["securities"]:
        s["type_unconfirmed"] = False
    assert _t1(records, ledger, reg, "KR0083")["type_unconfirmed"] is False
    assert _t1(records, ledger, registry, "KR0083")["type_unconfirmed"] is True


def test_reclassified_securities_are_confirmed_and_flag_cleared(registry):
    """2026-10-12 재분류: 이 네 회사의 신규 신종은 보완자본형 확정 - 미확정 표지가 남아 있으면 안 된다."""
    for code, issue in (("KR0097", "2023-03-31"), ("KR0083", "2023-02-28"), ("KR0104", "2023-01-31"),
                        ("KR1000", "2023-03-16"), ("KR1000", "2024-10-11")):
        hit = [s for s in registry["companies"][code]["securities"] if s.get("issue_date") == issue]
        assert len(hit) == 1, (code, issue)
        assert hit[0]["type"] == "tier2" and hit[0]["type_unconfirmed"] is False, (code, issue)
        assert "unconfirmed_reason" not in hit[0], (code, issue)


def test_issuer_type_only_where_it_differs_and_is_documented(registry):
    """issuer_type 은 type 과 다를 때만 적는다(forward 기본자본 경로가 이 필드로 갈린다) - 하나생명·교보 둘뿐."""
    found = {}
    for code, ent in registry["companies"].items():
        for s in ent["securities"]:
            if "issuer_type" in s:
                assert s["issuer_type"] in ("legacy_tfi", "tier1", "tier2"), (code, s["name"])
                assert s["issuer_type"] != s["type"], (code, s["name"])
                assert s.get("evidence"), (code, s["name"])
                found.setdefault(code, []).append(s["issue_date"])
    assert found == {"KR0097": ["2023-03-31"], "KR0073": ["2024-11-12"]}, found


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
