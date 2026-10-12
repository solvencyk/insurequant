# -*- coding: utf-8 -*-
"""`kics_capital_securities_timeline.json`(채권 단위 발행 내역, 분류 없음) - 변환 규칙 + 배포본 대조 + 변이시험."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_capital_securities_timeline as T  # noqa: E402

FORBIDDEN_FIELDS = {"type", "tier1", "tier2", "recognized", "recognition", "basic_eok", "supplementary", "rule"}


def bond(**kw):
    b = {"tier": "hybrid", "issue_date": "2024-07-17", "call_date": "2029-07-17", "coupon_pct": 4.8,
         "face_amount_mn": 500000, "outstanding_mn": 500000, "as_of": "2026-06-30"}
    b.update(kw)
    return b


def test_unit_conversion_mn_to_eok_two_decimals():
    r = T.bond_record(bond(face_amount_mn=1076175, outstanding_mn=1071969), None)
    assert (r["face_eok"], r["outstanding_eok"]) == (10761.75, 10719.69)


def test_redeemed_bond_is_kept_with_zero_outstanding():
    r = T.bond_record(bond(outstanding_mn=0), None)
    assert r is not None and r["outstanding_eok"] == 0.0 and r["face_eok"] == 5000.0


@pytest.mark.parametrize("patch", [{"issue_date": None}, {"tier": "preferred"}, {"face_amount_mn": None, "outstanding_mn": None},
                                   {"face_amount_mn": None}])
def test_unplaceable_bonds_are_dropped_not_guessed(patch):
    assert T.bond_record(bond(**patch), None) is None


def test_missing_call_and_coupon_stay_null():
    r = T.bond_record(bond(call_date=None, coupon_pct=None), None)
    assert r["call_date"] is None and r["coupon_pct"] is None


def test_as_of_falls_back_to_company_date():
    assert T.bond_record(bond(as_of=None), "2025-12-31")["as_of"] == "2025-12-31"
    assert T.bond_record(bond(), "2025-12-31")["as_of"] == "2026-06-30"


def test_build_sorts_by_issue_date_and_omits_empty_companies():
    src = {"companies": [
        {"code": "KR0001", "as_of": "2026-06-30", "bonds": [bond(issue_date="2025-01-01"), bond(issue_date="2022-01-01")]},
        {"code": "KR0002", "as_of": "2026-06-30", "bonds": []},
        {"code": "KR0003", "as_of": "2026-06-30", "bonds": [bond(issue_date=None)]},
    ]}
    doc = T.build(src, "2026-10-12")
    assert list(doc["securities"]) == ["KR0001"]
    assert [r["issue_date"] for r in doc["securities"]["KR0001"]] == ["2022-01-01", "2025-01-01"]
    assert doc["generated"] == "2026-10-12" and doc["unit"] == "억원"


def _mutant(old, new):
    src = (ROOT / "scripts" / "build_capital_securities_timeline.py").read_text(encoding="utf-8")
    assert src.count(old) == 1, old
    ns: dict = {"__name__": "timeline_mutant", "__file__": str(ROOT / "scripts" / "build_capital_securities_timeline.py")}
    exec(compile(src.replace(old, new), "timeline_mutant", "exec"), ns)
    return ns


@pytest.mark.parametrize("old,new", [
    ("MN_PER_EOK = 100.0", "MN_PER_EOK = 1.0"),                                   # 단위 100 누락
    ('if bond.get("tier") not in TIERS or not bond.get("issue_date"):', 'if bond.get("tier") not in TIERS:'),   # 발행일 없는 증권 포함
    ('"outstanding_eok": eok(out or 0.0),', '"outstanding_eok": eok(face),'),      # 잔액 자리에 권면
])
def test_mutants_are_killed(old, new):
    ns = _mutant(old, new)
    probes = [bond(), bond(issue_date=None), bond(outstanding_mn=0)]
    assert [ns["bond_record"](b, None) for b in probes] != [T.bond_record(b, None) for b in probes]


# --------------------------------------------------------------------------- 배포본
@pytest.fixture(scope="module")
def deployed():
    return json.loads((ROOT / "kics_capital_securities_timeline.json").read_text(encoding="utf-8"))


def test_deployed_equals_rebuild_from_source(deployed):
    src = json.loads(T.SRC.read_text(encoding="utf-8"))
    again = T.build(src, deployed["generated"])
    assert deployed == again


def test_deployed_shape_and_no_classification(deployed):
    assert set(deployed) == {"generated", "unit", "source", "securities"}
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", deployed["generated"])
    for code, recs in deployed["securities"].items():
        assert re.fullmatch(r"KR\d{4}", code) and recs
        for r in recs:
            assert set(r) == {"tier", "issue_date", "call_date", "coupon_pct", "face_eok", "outstanding_eok", "as_of"}
            assert r["tier"] in ("hybrid", "subordinated") and not (set(r) & FORBIDDEN_FIELDS)
            assert r["face_eok"] > 0 and r["outstanding_eok"] >= 0
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["issue_date"]) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["as_of"])


def test_hanwha_life_hybrid_issuance_by_hand(deployed):
    """한화생명 신종 4건: 2024-07-17 5,000억 · 2024-09-24 6,000억 · 2025-03-26 6,000억 · 2025-06-24 외화 13,819억."""
    hy = [(r["issue_date"], r["face_eok"]) for r in deployed["securities"]["KR0068"] if r["tier"] == "hybrid"]
    assert hy == [("2024-07-17", 5000.0), ("2024-09-24", 6000.0), ("2025-03-26", 6000.0), ("2025-06-24", 13819.0)]
