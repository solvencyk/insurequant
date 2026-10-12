# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

T = "tests/unit/test_capital_securities_timeline.py"
edit(T, [
('''        for r in recs:
            assert set(r) == {"tier", "issue_date", "call_date", "coupon_pct", "face_eok", "outstanding_eok", "as_of"}
''',
'''        for r in recs:
            # 선택 표지 두 개는 True 일 때만 키가 있다(2026-10-12 독립 감사 요청 1·2): call_date_unconfirmed · estimated
            assert set(r) - OPTIONAL_FLAGS == {"tier", "issue_date", "call_date", "coupon_pct", "face_eok", "outstanding_eok", "as_of"}
            assert all(r[f] is True for f in OPTIONAL_FLAGS & set(r))
'''),
('''FORBIDDEN_FIELDS = {"type", "tier1", "tier2", "recognized", "recognition", "basic_eok", "supplementary", "rule"}
''',
'''FORBIDDEN_FIELDS = {"type", "tier1", "tier2", "recognized", "recognition", "basic_eok", "supplementary", "rule"}
OPTIONAL_FLAGS = {"call_date_unconfirmed", "estimated"}
'''),
('''def _mutant(old, new):''',
'''def test_optional_flags_exist_only_when_true_in_source():
    """독립 감사(티켓 20261012T2235Z) 요청 1·2: 원천 채권에 표지가 있을 때만 출력에 키가 생긴다(없으면 키 자체가 없다)."""
    plain = T.bond_record(bond(), None)
    assert not (set(plain) & OPTIONAL_FLAGS)
    assert T.bond_record(bond(call_date_unconfirmed=True), None)["call_date_unconfirmed"] is True
    assert T.bond_record(bond(estimated=True, call_date=None, coupon_pct=None), None)["estimated"] is True
    assert not (set(T.bond_record(bond(call_date_unconfirmed=False, estimated=False), None)) & OPTIONAL_FLAGS)


def test_deployed_flags_are_exactly_the_audited_rows(deployed):
    """표지가 붙은 행은 감사가 짚은 3건뿐이다: DB손해 제1·2회(콜일 미확정) + 하나손해 2026-06-29 추정 행(금리·콜일 없음)."""
    unconfirmed = [(c, r["issue_date"], r["face_eok"]) for c, v in deployed["securities"].items() for r in v
                   if r.get("call_date_unconfirmed")]
    estimated = [(c, r["issue_date"], r["face_eok"], r["coupon_pct"], r["call_date"]) for c, v in deployed["securities"].items()
                 for r in v if r.get("estimated")]
    assert sorted(unconfirmed) == [("KR0011", "2025-09-01", 7470.0), ("KR0011", "2025-09-25", 1200.0)]
    assert estimated == [("KR0050", "2026-06-29", 999.0, None, None)]


def _mutant(old, new):'''),
])
