# -*- coding: utf-8 -*-
"""`securities_summary`(소진율 도넛 밑 신종·후순위 큰 셀) 값 - 경계 시험 + 변이시험 + 배포본 대조.

산식: `scripts/capital_securities_summary.py`. 입력 `data/bonds/capital_securities_fy2026h1.json`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import capital_securities_summary as S  # noqa: E402

AS_OF = "2026-06-30"


def bond(tier="hybrid", issue="2024-01-10", call="2029-01-10", coupon=4.0, out=100000.0, past=False, src="disclosed",
         as_of="2026-06-30"):
    return {"name": f"{tier}-{issue}", "tier": tier, "issue_date": issue, "call_date": call, "coupon_pct": coupon,
            "outstanding_mn": out, "past_call_outstanding": past, "call_source": src, "as_of": as_of}


# --------------------------------------------------------------------------- 경계
def test_issue_date_boundary_2022_12_31_vs_2023_01_01():
    v = S.summarize_tier([bond(issue="2022-12-31", out=300000.0), bond(issue="2023-01-01", out=200000.0)], "hybrid", AS_OF)
    assert v["issued_since_2023_eok"] == 2000            # 2023-01-01 은 포함, 2022-12-31 은 제외
    assert v["latest_issue_date"] == "2023-01-01"


def test_no_issue_since_2023_is_zero_not_null():
    v = S.summarize_tier([bond(issue="2022-06-01", coupon=3.3)], "hybrid", AS_OF)
    assert v["issued_since_2023_eok"] == 0
    assert v["latest_coupon_pct"] == 3.3                 # 2023년 이전 발행이어도 가장 최근 증권


def test_past_call_outstanding_is_skipped_for_next_call_but_counted_elsewhere():
    b = [bond(issue="2020-01-01", call="2025-01-01", past=True, out=500000.0, coupon=2.0),
         bond(issue="2021-01-01", call="2027-05-05", out=100000.0, coupon=3.0)]
    v = S.summarize_tier(b, "hybrid", AS_OF)
    assert (v["next_call_date"], v["next_call_eok"]) == ("2027-05-05", 1000)
    only_past = S.summarize_tier(b[:1], "hybrid", AS_OF)
    assert only_past["next_call_date"] is None and only_past["next_call_eok"] is None
    assert only_past["latest_coupon_pct"] == 2.0         # 잔액이 남아 있으므로 최근 발행 후보


def test_call_date_before_as_of_is_not_next_and_equal_is_next():
    assert S.summarize_tier([bond(call="2026-06-29")], "hybrid", AS_OF)["next_call_date"] is None
    assert S.summarize_tier([bond(call="2026-06-30")], "hybrid", AS_OF)["next_call_date"] == "2026-06-30"


def test_same_call_date_sums_amounts():
    b = [bond(call="2027-03-31", out=400000.0), bond(call="2027-03-31", out=100000.0), bond(call="2028-01-01", out=900000.0)]
    v = S.summarize_tier(b, "hybrid", AS_OF)
    assert (v["next_call_date"], v["next_call_eok"]) == ("2027-03-31", 5000)


def test_same_issue_day_takes_larger_amount_coupon():
    b = [bond(issue="2025-01-01", coupon=7.3, out=80000.0), bond(issue="2025-01-01", coupon=7.0, out=120000.0)]
    assert S.summarize_tier(b, "hybrid", AS_OF)["latest_coupon_pct"] == 7.0


def test_latest_issue_without_coupon_is_null_not_previous_coupon():
    b = [bond(issue="2024-01-01", coupon=5.5), bond(issue="2026-03-31", coupon=None, call=None)]
    v = S.summarize_tier(b, "hybrid", AS_OF)
    assert v["latest_coupon_pct"] is None and v["latest_issue_date"] == "2026-03-31"


def test_unknown_issue_date_is_excluded_not_guessed():
    b = [bond(issue=None, out=900000.0, coupon=1.57, call="2025-12-31", past=True)]
    v = S.summarize_tier(b, "hybrid", AS_OF)
    assert v["issued_since_2023_eok"] == 0 and v["latest_issue_date"] is None and v["latest_coupon_pct"] is None


def test_tier_without_live_securities_is_null_and_tiers_are_separate():
    b = [bond(tier="hybrid"), bond(tier="subordinated", out=0.0)]
    out = S.summarize_company(b, AS_OF)
    assert out["subordinated"] is None and out["hybrid"] is not None and out["as_of"] == AS_OF
    assert S.summarize_company([], AS_OF) == {"as_of": AS_OF, "hybrid": None, "subordinated": None}


def test_estimated_call_flag_and_oldest_balance_date():
    b = [bond(src="derived_issue_plus_5y", as_of="2025-12-31"), bond(issue="2020-01-01", call="2031-01-01", as_of="2026-06-30")]
    v = S.summarize_tier(b, "hybrid", AS_OF)
    assert v["next_call_estimated"] is True and v["balance_as_of"] == "2025-12-31"


def test_eok_rounding_half_up_and_unit():
    assert S.eok(100.0) == 1 and S.eok(149.0) == 1 and S.eok(150.0) == 2 and S.eok(45881.5) == 459


def test_quarter_end():
    assert S.quarter_end("2026.2Q") == "2026-06-30" and S.quarter_end("2026.1Q") == "2026-03-31"


# --------------------------------------------------------------------------- 변이시험
SYNTH = [
    bond(issue="2022-12-31", call="2027-01-01", out=300000.0),
    bond(issue="2023-01-01", call="2028-01-01", out=200000.0),
    bond(issue="2019-01-01", call="2026-07-01", out=700000.0, past=True),   # 콜일은 미래지만 이미 콜 경과 표시
]


def _run(mod, bonds=SYNTH):
    return mod.summarize_tier(bonds, "hybrid", AS_OF)


def _mutant(old, new):
    src = (ROOT / "scripts" / "capital_securities_summary.py").read_text(encoding="utf-8")
    assert src.count(old) == 1, old
    ns: dict = {"__name__": "capsec_summary_mutant", "__file__": str(ROOT / "scripts" / "capital_securities_summary.py")}
    exec(compile(src.replace(old, new), "capsec_summary_mutant", "exec"), ns)

    class M:
        pass
    m = M()
    m.__dict__.update(ns)
    return m


def test_baseline_values_for_mutation_cases():
    v = _run(S)
    assert v["issued_since_2023_eok"] == 2000 and v["next_call_date"] == "2027-01-01" and v["next_call_eok"] == 3000


@pytest.mark.parametrize("old,new,field", [
    ('b["issue_date"] >= SINCE', 'b["issue_date"] < SINCE', "issued_since_2023_eok"),                       # 날짜 비교 반대
    ('b["call_date"] >= as_of', 'b["call_date"] < as_of', "next_call_date"),                                # 콜 날짜 비교 반대
    ('MN_PER_EOK = 100.0 ', 'MN_PER_EOK = 1.0 ', "issued_since_2023_eok"),                                  # 단위 100 누락
    ('not b.get("past_call_outstanding") and ', '', "next_call_date"),                                      # 콜 경과 무시
    ('min(b["call_date"] for b in callable_)', 'max(b["call_date"] for b in callable_)', "next_call_date"),   # 가장 이른 콜
])
def test_mutants_are_killed(old, new, field):
    assert _run(_mutant(old, new))[field] != _run(S)[field], (old, new)


# --------------------------------------------------------------------------- 실데이터·배포본
@pytest.fixture(scope="module")
def deployed():
    t1 = json.loads((ROOT / "kics_tier1_utilization.json").read_text(encoding="utf-8"))
    t2 = json.loads((ROOT / "kics_tier2_utilization.json").read_text(encoding="utf-8"))
    return t1, t2


def test_hanwha_life_by_hand():
    """한화생명(KR0068) 사람 검산 - 신종 4건: 2024-07-17 4.8% 5,000억 · 2024-09-24 4.8% 6,000억 · 2025-03-26 4.61%
    6,000억 · 2025-06-24 외화 6.30% 13,819억(콜 2030-06-24). 모두 2023 이후 -> 합계 30,819억, 최근 = 외화 6.30%,
    가장 가까운 콜 = 2029-07-17 5,000억. 후순위 2023 이후 = 4(후) 4,988.23 + 7(후) 7,979.32 = 12,967.55 -> 12,968억."""
    out = S.summaries_by_code("2026.2Q")["KR0068"]
    h, s = out["hybrid"], out["subordinated"]
    assert (h["latest_coupon_pct"], h["latest_issue_date"], h["issued_since_2023_eok"]) == (6.3, "2025-06-24", 30819)
    assert (h["next_call_date"], h["next_call_eok"]) == ("2029-07-17", 5000)
    assert (s["latest_coupon_pct"], s["issued_since_2023_eok"]) == (4.45, 12968)
    assert (s["next_call_date"], s["next_call_eok"], s["next_call_estimated"]) == ("2027-02-04", 10720, True)


def test_deployed_rows_carry_identical_summary_in_both_files(deployed):
    t1, t2 = deployed
    q = t1["quarter"]
    expect = S.summaries_by_code(q)
    assert len(t1["results"]) == len(t2["results"]) == 47
    bad = []
    for name, doc in (("t1", t1), ("t2", t2)):
        for row in doc["results"]:
            if row.get("securities_summary") != expect.get(row["code"], S.empty_summary(q)):
                bad.append((name, row["code"]))
    assert not bad, bad
