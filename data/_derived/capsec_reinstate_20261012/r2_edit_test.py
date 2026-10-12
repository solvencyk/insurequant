# -*- coding: utf-8 -*-
from pathlib import Path
P = Path("tests/unit/test_capital_utilization_rules.py")
t = P.read_text(encoding="utf-8")
def sub(old, new):
    global t
    assert t.count(old) == 1, old[:60]
    t = t.replace(old, new)

sub('''# 메모 §3.2 「새 정의로 2026.2Q tier1」 표 (owner 채택 결정 ③). 미정 4사는 보수적 상한(티켓) - 흥국생명은
# 2022-12 전환우선주로 기본자본형 확정(같은 숫자 81.4).
T1_MEMO = {"KR0068": 0.0, "KR0072": 0.0, "KR0050": 0.0, "KR0032": 0.0, "KR0005": 62.4, "KR0073": 70.1,
           "KR0002": 53.1, "KR0011": 151.6, "KR0097": 238.2, "KR0001": 18.9, "KR0003": 14.3, "KR0099": 12.2,
           "KR0076": 221.7, "KR1000": 205.1, "KR0104": 72.7, "KR0083": 42.1, "KR0071": 81.4, "KR0008": 0.5}
T1_UNCONFIRMED = {"KR1000": 94.0, "KR0104": 48.5, "KR0083": 17.3}   # code -> 보완자본형일 때 값(범위 아래 끝)''',
'''# 메모 §3.2 「새 정의로 2026.2Q tier1」 표 (owner 채택 결정 ③) + 2026-10-12 재공개 라운드 재분류(티켓
# 20261012T2030Z, owner 「분류 확정」): 하나생명 제1회(스텝업 구조)·푸본 600억·농협생명 제5회·코리안리 제5/6회가
# 보완자본형으로 확정되어 기본자본 자본증권에서 빠진다 -> KR0097 238.2 -> 0.0 · KR1000 205.1 -> 94.0 ·
# KR0104 72.7 -> 48.5 · KR0083 42.1 -> 17.3 (이 네 값이 바뀐 이유는 전부 이 재분류다 - 느슨하게 푼 것이 아니다).
# 흥국생명은 2022-12 전환우선주로 기본자본형 확정(81.4 불변). 교보 2024 건은 type=tier2(발행조건 스텝업)로
# 바뀌었지만 결속하는 쪽이 기발행 70.1 이라 숫자 불변.
T1_MEMO = {"KR0068": 0.0, "KR0072": 0.0, "KR0050": 0.0, "KR0032": 0.0, "KR0005": 62.4, "KR0073": 70.1,
           "KR0002": 53.1, "KR0011": 151.6, "KR0097": 0.0, "KR0001": 18.9, "KR0003": 14.3, "KR0099": 12.2,
           "KR0076": 221.7, "KR1000": 94.0, "KR0104": 48.5, "KR0083": 17.3, "KR0071": 81.4, "KR0008": 0.5}
# 아직 미확정이 남은 회사 = 푸본의 채권원장에 없는 50억(2024.4Q~)뿐. 결속하지 않아 상한 = 하한.
T1_UNCONFIRMED = {"KR0083": 17.3}   # code -> 보완자본형일 때 값(범위 아래 끝)''')

sub('''    ("KR1000", "tier1", "tier2", 205.1, 94.0),    # 코리안리: 미정 신규를 보완자본형으로 보면 기발행 쪽 94.0
    ("KR0032", "tier2", "tier1", 0.0, 334.7),     # 농협손해''',
'''    ("KR1000", "tier2", "tier1", 94.0, 205.1),    # 코리안리: 확정된 보완자본형 신규 4,800억을 기본자본형으로 보면 205.1
    ("KR0104", "tier2", "tier1", 48.5, 72.7),     # 농협생명: 제5회 2,500억 (확정 전 상한이던 값)
    ("KR0097", "tier2", "tier1", 0.0, 238.2),     # 하나생명: 스텝업 구조 -> 보완자본형. 기본자본형이면 종전 238.2
    ("KR0032", "tier2", "tier1", 0.0, 334.7),     # 농협손해''')

sub('''def test_unconfirmed_flag_comes_from_registry(records, ledger, registry):
    reg = copy.deepcopy(registry)
    for s in reg["companies"]["KR1000"]["securities"]:
        s["type_unconfirmed"] = False
    assert _t1(records, ledger, reg, "KR1000")["type_unconfirmed"] is False
    assert _t1(records, ledger, registry, "KR1000")["type_unconfirmed"] is True''',
'''def test_unconfirmed_flag_comes_from_registry(records, ledger, registry):
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
    assert found == {"KR0097": ["2023-03-31"], "KR0073": ["2024-11-12"]}, found''')
P.write_text(t, encoding="utf-8", newline="\n")
print("ok")
