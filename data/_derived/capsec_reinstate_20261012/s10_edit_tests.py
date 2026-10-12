# -*- coding: utf-8 -*-
"""Update tests/unit/test_capital_utilization_rules.py for requests 3 and 8 (reason: independent audit finding / owner decision
2026-10-12 night). Expectations are made EXACT, not looser."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

T = "tests/unit/test_capital_utilization_rules.py"

edit(T, [
# ---- memo reproduction with owner-decision overrides
('''def test_tier2_reproduces_memo_for_all_47(computed, memo):
    assert len(memo) == 47
    bad = []
    for code, m in memo.items():
        t2 = computed[code]["t2"]
        exp_num, exp_pct = _f(m["t2_num_reg"]), _f(m["t2_pct_reg"])
        if t2["rule"] != m["t2_rule"]:
            bad.append((code, "rule", m["t2_rule"], t2["rule"]))
''',
'''# owner 결정 2026-10-12 밤(요청 8): 기발행 차감액 = 채권원장의 2022-12-31 이전 발행 잔액(신종·후순위 각각), 인쇄값 항목 53/54 아님.
# 메모 재현표(recompute_47.csv)는 인쇄값 기준이라 아래 21사는 이 결정으로 숫자가 바뀐다 - (규칙, 분자, 소진율) 정확값을 박제한다
# (느슨하게 푼 것이 아니다: 이 21개 값 밖의 26사는 메모 값 그대로). 근거 표 data/_derived/capsec_reinstate_20261012/z3_tier2_before_after_47.*
# 미래에셋·DB생명은 숫자 불변이고 규칙 이름만 R1/R-none -> R3 (옛 특례가 이 일반 규칙에 흡수됨).
T2_OWNER_20261012_NIGHT = {
    "KR0001": ("R2", 9724.88, 30.8), "KR0002": ("R2", 8288.25, 46.6), "KR0003": ("R2", 5289.77, 50.1),
    "KR0005": ("R2", 5119.32, 45.2), "KR0009": ("R-none", 23522.36, 64.2), "KR0010": ("R2", 7384.19, 20.5),
    "KR0011": ("R-none", 20692.16, 36.0), "KR0032": ("R2", 6908.29, 102.8), "KR0049": ("R2", 0.0, 0.0),
    "KR0068": ("R3", 56155.44, 74.8), "KR0070": ("R2", 6081.29, 70.4), "KR0071": ("R2", 5227.17, 37.0),
    "KR0073": ("R2", 27137.98, 51.5), "KR0076": ("R5", 2109.54, 56.9), "KR0079": ("R3", 2930.93, 24.5),
    "KR0082": ("R3", 2563.95, 31.6), "KR0083": ("R2", 5639.79, 73.1), "KR0099": ("R2", 0.0, 0.0),
    "KR0104": ("R4", 825.57, 4.8), "KR1000": ("R2", 7105.18, 60.9), "KR1011": ("R2", 2749.47, 76.2),
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
'''),
# ---- rule cases with ledger hybrid legacy as 4th argument
('''RULE_CASES = [
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
''',
'''RULE_CASES = [
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
            if (b.get("issue_date") or "") < "2023-01-01":
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
'''),
])

edit(T, [
('''        for fld, exp in (("utilization_pct", c["pct"]), ("numerator_eok", c["numerator"]), ("rule", c["rule"]),
                         ("tier2_limit_eok", c["limit"])):
            if row.get(fld) != exp:
                bad.append(("t2", row["code"], fld, exp, row.get(fld)))
''',
'''        for fld, exp in (("utilization_pct", c["pct"]), ("numerator_eok", c["numerator"]), ("rule", c["rule"]),
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
'''),
])
