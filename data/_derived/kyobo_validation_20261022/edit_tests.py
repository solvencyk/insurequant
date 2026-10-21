# -*- coding: utf-8 -*-
from pathlib import Path
# 1) append mutation tests for the new branch
p = Path("tests/test_rule_coverage_manifest.py")
s = p.read_text(encoding="utf-8")
add = '''

# ---------------------------------------------------------------------------
# 2f TAX22_SOURCE_CROSSCHECK -- 최신 비교열 판 분기 (2026-10-22, ticket 20261021T1310Z 후속)
# 교보생명 2023.3Q~2024.2Q 의 법인세는 후속 공시가 소급재작성한 값이다. 규칙은 같은 분기 원공시
# 캐시 **또는** 다음 해 같은 기간 캐시의 전기 열 둘 중 하나와 맞으면 통과, 둘 다와 어긋나면 FAIL.
# 이 분기가 실제로 읽히는지(빼면 RED), 두 판 어디에도 안 맞는 값은 여전히 FAIL 인지, 원공시 판
# 값도 여전히 통과하는지를 변이로 못 박는다. 등재부(예외)는 쓰지 않는다.
# ---------------------------------------------------------------------------
_TAX22_KYOBO_RESTATED = [("교보생명보험", q) for q in ("2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q")]


def _tax22_set_tax(rows, co, q, tax):
    """co/q 의 item24 를 item22 - tax 로 바꿔 |22-24| == tax 가 되게 한다(item22 불변)."""
    r22 = next(r for r in rows if r["원수사명"] == co and r["공시분기"] == q and r["항목명"] == "세전이익")
    for r in rows:
        if r["원수사명"] == co and r["공시분기"] == q and r["항목명"] == "당기순이익":
            r["값"] = r22["값"] - tax
    return rows


def _tax22_fail_keys(V, rows):
    _p, fails, _s = V._check_tax22_crosscheck(rows, quiet=True)
    return {(f[0], f[1]) for f in fails}


def test_tax22_latest_comparative_vintage_branch_is_read_and_enforced():
    import copy
    V = _vmt()
    import fetch_dart_fs as fdf
    rows = _pl_rows()
    p0, fails0, _s0 = V._check_tax22_crosscheck(rows, quiet=True)
    assert not fails0, f"라이브 마스터에 tax22 FAIL: {fails0[:3]}"
    # (a) 분기를 빼면 교보 4칸이 RED 로 돌아온다 = 이 분기가 실제로 읽힌다
    orig = V._tax22_prior_tier1
    try:
        V._tax22_prior_tier1 = lambda *a, **k: None
        assert _tax22_fail_keys(V, rows) == set(_TAX22_KYOBO_RESTATED)
    finally:
        V._tax22_prior_tier1 = orig
    # (b) 두 판 어디에도 안 맞는 값은 FAIL -- 최신 비교열 판 +5,000백만, 원공시 판 +5,000백만
    kr2cc = V._tax22_corp_codes()
    cc = kr2cc["KR0073"]
    for co, q in _TAX22_KYOBO_RESTATED:
        same = abs(V._tax22_tier1(fdf, cc, q)[23])
        prior = abs(V._tax22_prior_tier1(fdf, cc, q)[23])
        assert abs(same - prior) > 1000, (co, q, same, prior)   # 두 판이 실제로 다르다
        for bad in (prior + 5000.0, same + 5000.0, (same + prior) / 2):
            m = _tax22_set_tax(copy.deepcopy(rows), co, q, bad)
            assert (co, q) in _tax22_fail_keys(V, m), (co, q, bad)
        # (c) 원공시 판 값도 여전히 통과 (HEAD~1 마스터가 그랬다)
        m = _tax22_set_tax(copy.deepcopy(rows), co, q, same)
        assert (co, q) not in _tax22_fail_keys(V, m), (co, q, same)
        # (d) 최신 비교열 판 값은 통과 (= 현 마스터)
        m = _tax22_set_tax(copy.deepcopy(rows), co, q, prior)
        assert (co, q) not in _tax22_fail_keys(V, m), (co, q, prior)


def test_tax22_prior_tier1_reads_annual_and_quarterly_prior_columns():
    """4Q = frmtrm_amount, 분기 = frmtrm_add_amount (누계). 교보 캐시 실측값(원 단위 -> 백만원)."""
    V = _vmt()
    import fetch_dart_fs as fdf
    cc = V._tax22_corp_codes()["KR0073"]
    expect = {"2023.3Q": 255935.161968, "2023.4Q": 207353.112783,
              "2024.1Q": 104131.9, "2024.2Q": 207856.692792}
    for q, v in expect.items():
        got = abs(V._tax22_prior_tier1(fdf, cc, q)[23])
        assert abs(got - v) < 1.0, (q, got, v)
'''
assert "test_tax22_latest_comparative_vintage_branch_is_read_and_enforced" not in s
p.write_text(s.rstrip("\n") + "\n" + add, encoding="utf-8", newline="")

# 2) manifest text for item 22
s = p.read_text(encoding="utf-8")
old = '''"CONSTRUCTIVE 탐지율 0.0% 였다 — 이 항목이 이 매니페스트의 존재 증명이다",'''
new = '''"CONSTRUCTIVE 탐지율 0.0% 였다 — 이 항목이 이 매니페스트의 존재 증명이다. "
        "2026-10-22: 원천 법인세는 같은 분기 원공시 판 **또는** 다음 해 같은 기간 캐시 전기 열"
        "(최신 비교열 판)과 맞으면 통과(교보 재작성 4칸; 전 643버킷 시뮬 닫힘 4·깨짐 0, 주입 탐지 "
        "282/282 불변) — test_tax22_latest_comparative_vintage_branch_is_read_and_enforced",'''
assert s.count(old) == 1
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="")

# 3) identity registry statement
q = Path("tests/test_identity_registry.py")
t = q.read_text(encoding="utf-8")
old = '''"2026-08-29 신설, ticket inbox/validation/20260829T2130Z.",
        "impl": [("scripts/validate_master_tables.py", "_check_tax22_crosscheck")],'''
new = '''"2026-08-29 신설, ticket inbox/validation/20260829T2130Z. "
                     "2026-10-22: 원천 법인세는 같은 분기 원공시 판 또는 다음 해 같은 기간 FS-API "
                     "캐시의 전기 열(최신 비교열 판, `_tax22_prior_tier1`) 중 하나와 맞으면 통과 "
                     "(교보생명 2023.3Q~2024.2Q 소급재작성 법인세 4칸; 둘 다와 어긋나면 FAIL).",
        "impl": [("scripts/validate_master_tables.py", "_check_tax22_crosscheck")],'''
assert t.count(old) == 1
t = t.replace(old, new)
q.write_text(t, encoding="utf-8", newline="")
print("ok")
