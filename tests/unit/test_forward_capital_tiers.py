# -*- coding: utf-8 -*-
"""Forward Outlook 증권별 계층 반영(2026-10-12 재공개 라운드) - 단위시험 + 변이시험.

정의: scripts/forward_capital_simulation.py 머리말. 계층 정본: data/bonds/capital_tier_registry.json.
  - 보완자본형(tier2) 신종 콜 = 총자본에서만 빠지고 기본자본 불변
  - 기발행(legacy_tfi) 한도 SCR x 15% / 기본자본형(tier1) 한도 SCR x 10% 분리, 매 연말 SCR 로 재계산
  - 한도 초과로 보완자본에 재분류된 부분이 먼저 빠지고 그다음 기본자본
  - 발행사 처리(issuer_type)가 우리 분류와 다르면 baseline_basis_flag + 대체 경로
  - 총자본 경로는 계층과 무관
"""
from __future__ import annotations

import copy
import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import scripts.forward_capital_simulation as F  # noqa: E402
import capital_utilization_rules as R  # noqa: E402

AS_OF = date(2026, 6, 30)


def _ev(amount, call, ty, basis=None, unconf=False, name="b"):
    return {"isin": name, "name": name, "call_date": call, "legal_maturity": None, "amount_eok": float(amount),
            "tier": "tier1_hybrid", "issue_date": "2024-01-01",
            "hybrid_class": {"type": ty, "basis_type": basis or ty, "type_unconfirmed": unconf, "source": "test"}}


def _bond(amount, call, ty, basis=None, unconf=False, tier="hybrid"):
    b = {"isin": "x", "name": "x", "issue_date": "2024-01-01", "tier": "tier1_hybrid" if tier == "hybrid" else "tier2_subordinated",
         "issue_amount_won": amount * 1e8, "effective_call_date": call, "legal_maturity": None, "status": "outstanding"}
    b["hybrid_class"] = ({"type": ty, "basis_type": basis or ty, "type_unconfirmed": unconf, "source": "test"}
                         if tier == "hybrid" else None)
    return b


@pytest.fixture(autouse=True)
def _as_of_2026_2q(monkeypatch):
    monkeypatch.setattr(F, "BASELINE_QUARTER", "2026.2Q")


def _baseline(scr_post=1000.0, scr_pre=1000.0, capital=2000.0, basic=500.0):
    return {"insurer_name": "T", "items": {1: {"pre": capital, "post": capital}, 2: {"pre": basic, "post": basic},
                                           14: {"pre": scr_pre, "post": scr_post}}}


# --------------------------------------------------------------------------- 기여 계산
def test_buckets_use_separate_limits_and_tier2_contributes_zero():
    ev = [_ev(200, "2030-01-01", "legacy_tfi"), _ev(150, "2030-01-01", "tier1"), _ev(900, "2030-01-01", "tier2")]
    out = F._hybrid_basic(ev, "type", AS_OF, AS_OF, 1000.0)
    assert out["basic"] == 150.0 + 100.0            # min(200, 15%) + min(150, 10%)
    assert out["overflow"] == 50.0 + 50.0           # 각 한도 초과분 -> 보완자본 재분류
    assert out["remaining"] == 1250.0 and out["by_type"]["tier2"] == 900.0


def test_limit_recomputed_with_scr_and_overflow_goes_first():
    # 잔액 300 > 한도 150: 100 콜 -> 잔액 200 이라도 한도 150 안이 아니므로 기본자본 불변(초과분만 줄어듦)
    a = F._hybrid_basic([_ev(300, "2030-01-01", "legacy_tfi")], "type", AS_OF, AS_OF, 1000.0)
    b = F._hybrid_basic([_ev(200, "2030-01-01", "legacy_tfi")], "type", AS_OF, AS_OF, 1000.0)
    c = F._hybrid_basic([_ev(100, "2030-01-01", "legacy_tfi")], "type", AS_OF, AS_OF, 1000.0)
    assert a["basic"] == b["basic"] == 150.0 and a["overflow"] == 150.0 and b["overflow"] == 50.0
    assert c["basic"] == 100.0 and c["overflow"] == 0.0     # 한도 밑으로 내려가면 그때부터 기본자본이 줄어든다


# --------------------------------------------------------------------------- 시뮬 전체
def test_tier2_type_call_cuts_total_not_basic():
    row = F.simulate_one("T", _baseline(), [_bond(300, "2028-06-01", "tier2")])
    p27, p29 = row["projections"][1], row["projections"][3]
    assert p27["basic_capital_eok"] == p29["basic_capital_eok"] == 500.0       # 2028-06 콜 전후 기본자본 불변
    assert p27["capital_eok"] == 2000.0 and p29["capital_eok"] == 1700.0       # 총자본은 300 빠진다
    assert "baseline_basis_flag" not in row and "baseline_basis_note" not in row   # 어긋남이 없으면 필드 자체가 없다


def test_tier1_type_call_cuts_basic_and_total():
    row = F.simulate_one("T", _baseline(), [_bond(80, "2028-06-01", "tier1")])    # 80 < 한도 100
    p27, p29 = row["projections"][1], row["projections"][3]
    assert p27["basic_capital_eok"] == 500.0 and p29["basic_capital_eok"] == 420.0
    assert p29["capital_eok"] == 1920.0


def test_total_path_independent_of_classification():
    base = _baseline()
    paths = []
    for ty in ("legacy_tfi", "tier1", "tier2"):
        r = F.simulate_one("T", base, [_bond(120, "2027-06-01", ty), _bond(60, "2029-03-01", "legacy_tfi")])
        paths.append([(p["capital_eok"], p["ratio_pct"], p["cumulative_bond_dedu_eok"]) for p in r["projections"]])
    assert paths[0] == paths[1] == paths[2]


def test_all_legacy_reproduces_previous_single_15pct_formula():
    """종전 식: basic = base + min(H_y, 15% SCR_y) - min(H_0, 15% SCR_post). 전부 기발행이면 같아야 한다."""
    bonds = [_bond(220, "2027-06-01", "legacy_tfi"), _bond(70, "2029-03-01", "legacy_tfi")]
    base = _baseline(scr_post=1000.0, scr_pre=1300.0)
    row = F.simulate_one("T", base, bonds)
    for p in row["projections"]:
        ye = date(p["year"], 12, 31)
        h_y = sum(b["issue_amount_won"] / 1e8 for b in bonds if date.fromisoformat(b["effective_call_date"]) > ye)
        scr_y = 1000.0 + 300.0 * min(max((p["year"] - 2026) / 6, 0), 1)
        exp = 500.0 + min(h_y, 0.15 * scr_y) - min(290.0, 0.15 * 1000.0)
        assert p["basic_capital_eok"] == round(exp, 1), p["year"]


def test_issuer_type_difference_sets_flag_and_alt_path():
    bonds = [_bond(80, "2028-06-01", "tier2", basis="tier1")]     # 하나생명·교보형: 우리 분류 tier2, 발행사 tier1
    row = F.simulate_one("T", _baseline(), bonds)
    assert row["baseline_basis_flag"] is True and "발행사 실제 처리" in row["baseline_basis_note"]
    p29 = row["projections"][3]
    assert p29["basic_capital_eok"] == 420.0              # 기본자본 경로 = 발행사 처리 기준(기본자본형으로 빠진다)
    assert p29["basic_capital_by_type_eok"] == 500.0      # 우리 분류 기준 대체 경로 = 불변
    assert p29["basic_ratio_by_type_pct"] == 50.0 and p29["basic_ratio_pct"] == 42.0
    assert p29["capital_eok"] == 1920.0                   # 총자본은 분류와 무관
    plain = F.simulate_one("T", _baseline(), [_bond(80, "2028-06-01", "tier2")])
    assert "basic_ratio_by_type_pct" not in plain["projections"][3] and "basic_capital_by_type_eok" not in plain["projections"][3]
    assert "baseline_basis_flag" not in plain         # 어긋남이 없으면 대체 경로·플래그를 싣지 않는다(2026-10-12: 지금은 0사)


def test_unconfirmed_security_carries_flag_and_tier2_alternative():
    row = F.simulate_one("T", _baseline(), [_bond(80, "2028-06-01", "tier1", unconf=True)])
    assert row["type_unconfirmed"] is True
    p29 = row["projections"][3]
    assert p29["basic_ratio_pct"] == 42.0 and p29["basic_ratio_if_tier2_type_pct"] == 50.0
    clean = F.simulate_one("T", _baseline(), [_bond(80, "2028-06-01", "tier1")])
    assert clean["type_unconfirmed"] is False and clean["projections"][3]["basic_ratio_if_tier2_type_pct"] is None


# --------------------------------------------------------------------------- 변이시험
def test_mutation_limit_ratio_matters(monkeypatch):
    """기본자본형 한도 10% -> 15% 로 바꾸면 같은 콜의 기본자본 감소폭이 달라진다(한도가 숫자를 움직인다)."""
    bonds = [_bond(300, "2026-09-01", "tier1")]               # 잔액 300 > 한도 -> 콜로 한도만큼 기여가 빠진다
    d10 = F.simulate_one("T", _baseline(), bonds)["projections"][0]["basic_capital_eok"]
    monkeypatch.setattr(F, "TIER1_TYPE_LIMIT_RATIO", 0.15)
    d15 = F.simulate_one("T", _baseline(), bonds)["projections"][0]["basic_capital_eok"]
    assert d10 == 400.0 and d15 == 350.0                      # 10% 한도 100 이 빠진다 / 15% 한도면 150


def test_mutation_type_flip_changes_basic_but_not_total():
    a = F.simulate_one("T", _baseline(), [_bond(80, "2028-06-01", "tier2")])["projections"][3]
    b = F.simulate_one("T", _baseline(), [_bond(80, "2028-06-01", "tier1")])["projections"][3]
    assert a["basic_capital_eok"] != b["basic_capital_eok"] and a["capital_eok"] == b["capital_eok"]


# --------------------------------------------------------------------------- 분류 도우미
def test_classify_hybrid_registry_and_fallbacks():
    entry = {"securities": [
        {"issue_date": "2024-11-12", "type": "tier2", "issuer_type": "tier1", "type_unconfirmed": False},
        {"issue_date": "2022-03-31", "type": "legacy_tfi"}, {"issue_date": "2022-03-31", "type": "legacy_tfi"}]}
    assert R.classify_hybrid(entry, "2024-11-12") == {"type": "tier2", "basis_type": "tier1",
                                                      "type_unconfirmed": False, "source": "registry"}
    assert R.classify_hybrid(entry, "2022-03-31")["type"] == "legacy_tfi"
    assert R.classify_hybrid({}, "2019-05-01")["type"] == "legacy_tfi"
    assert R.classify_hybrid({}, None)["type"] == "legacy_tfi"
    post = R.classify_hybrid({}, "2024-05-01")                  # 등재부에 없는 2023년 이후 신종 = 보수적 기본자본형 + 미확정
    assert post["type"] == "tier1" and post["type_unconfirmed"] is True
    amb = R.classify_hybrid({"securities": [{"issue_date": "2024-01-01", "type": "tier1"},
                                            {"issue_date": "2024-01-01", "type": "tier2"}]}, "2024-01-01")
    assert amb["source"] == "registry_ambiguous" and amb["type_unconfirmed"] is True


# --------------------------------------------------------------------------- 실데이터: 배포본 == 모델
def _latest_manifest():
    dirs = sorted(p for p in (ROOT / "output" / "kics_forward_capital").iterdir() if (p / "manifest.json").exists())
    return json.loads((dirs[-1] / "manifest.json").read_text(encoding="utf-8"))


def test_deployed_forward_json_equals_model(monkeypatch):
    """배포본(kics_forward_capital.json)이 등재부 + 채권 소스로 지금 다시 돌린 모델과 같다 - 등재부만 고치고
    forward 를 안 돌린 채 push 하면 여기서 막힌다."""
    man = _latest_manifest()
    monkeypatch.setattr(F, "BASELINE_QUARTER", man["baseline_quarter"])
    monkeypatch.setattr(F._args, "bonds_source", man["bonds_source"])
    baselines = F.load_kics_baselines()
    bonds_per, _ = F.load_outstanding_bonds()
    deployed = {r["insurer_code"]: r for r in json.loads((ROOT / "kics_forward_capital.json").read_text(encoding="utf-8"))}
    bad = []
    for code, d in deployed.items():
        if d.get("status") != "ok":
            continue
        row = F.simulate_one(code, baselines[code], bonds_per.get(code, []))
        for k in ("baseline_basis_flag", "baseline_basis_note", "type_unconfirmed", "outstanding_hybrid_by_type_eok",
                  "hybrid_classification"):
            if row.get(k) != d.get(k):                  # 없는 필드끼리도 같아야 한다(.get 으로 비교)
                bad.append((code, k))
            if (k in row) != (k in d):
                bad.append((code, k, "presence"))
        for pm, pd in zip(row["projections"], d["projections"]):
            for k in pm:
                if pm[k] != pd.get(k):
                    bad.append((code, pm["year"], k, pm[k], pd.get(k)))
    assert not bad, bad[:10]


def test_deployed_flags_are_exactly_the_registry_mismatches():
    deployed = {r["insurer_code"]: r for r in json.loads((ROOT / "kics_forward_capital.json").read_text(encoding="utf-8"))}
    flagged = sorted(c for c, r in deployed.items() if r.get("baseline_basis_flag"))
    reg = R.load_registry()["companies"]
    expect = sorted(c for c, e in reg.items() if any(s.get("issuer_type") for s in e["securities"]))
    # 2026-10-12 발행사 처리 기준으로 등재부 type 을 맞춘 뒤 어긋난 증권이 0건 -> 플래그·대체 경로 필드는 어느 회사에도 없다.
    assert flagged == expect == []
    assert not [c for c, r in deployed.items() if "baseline_basis_flag" in r or "baseline_basis_note" in r]
    assert not [c for c, r in deployed.items() for p in r.get("projections", []) or []
                if "basic_ratio_by_type_pct" in p or "basic_capital_by_type_eok" in p]
    assert all(deployed[c]["baseline_basis_note"] for c in flagged)
    assert not [c for c, r in deployed.items() if r.get("status") == "ok" and r.get("type_unconfirmed")]
