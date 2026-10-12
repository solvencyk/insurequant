# -*- coding: utf-8 -*-
from pathlib import Path
P = Path("tests/unit/test_forward_capital_tiers.py")
t = P.read_text(encoding="utf-8")
a = t.index("def test_mutation_limit_ratio_matters")
b = t.index("def test_mutation_type_flip_changes_basic_but_not_total")
new = '''def test_mutation_limit_ratio_matters(monkeypatch):
    """기본자본형 한도 10% -> 15% 로 바꾸면 같은 콜의 기본자본 감소폭이 달라진다(한도가 숫자를 움직인다)."""
    bonds = [_bond(300, "2026-09-01", "tier1")]               # 잔액 300 > 한도 -> 콜로 한도만큼 기여가 빠진다
    d10 = F.simulate_one("T", _baseline(), bonds)["projections"][0]["basic_capital_eok"]
    monkeypatch.setattr(F, "TIER1_TYPE_LIMIT_RATIO", 0.15)
    d15 = F.simulate_one("T", _baseline(), bonds)["projections"][0]["basic_capital_eok"]
    assert d10 == 400.0 and d15 == 350.0                      # 10% 한도 100 이 빠진다 / 15% 한도면 150


'''
P.write_text(t[:a] + new + t[b:], encoding="utf-8", newline="\n")
