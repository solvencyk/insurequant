import io
p = "C:/Users/sangwook.cho/Desktop/insurequant/tests/test_tier2_issuer_inconsistent_exemption.py"
s = open(p, encoding="utf-8").read()
pass
a = '''    assert len(registered) == 22, (
        f"면제 레지스트리 크기가 22 -> {len(registered)} 로 바뀌었다.'''
b = '''    # 2026-10-13: 22 -> 20. **줄었다** — ("KR0003","2025.1Q") · ("KR0032","2024.3Q") 두 버킷이 풀렸다.
    # owner 승인(2026-10-12 「최신 공시 직전 컬럼」 덮어쓰기, parser-kics 74a415bf)으로 마스터 항목 13 이
    # 19,202 -> 17,997 · 8,867 -> 9,390 으로 바뀌어 `2_tier1_bridge` RED 가 사라졌다(후속 공시 둘이 같은 값 인쇄,
    # validation 이 원본 PDF 에서 독립 재판독). 박제 셀이 움직이면 INPUT_DRIFT+INERT 가 뜨므로 등재를 푼 것이다.
    assert len(registered) == 20, (
        f"면제 레지스트리 크기가 20 -> {len(registered)} 로 바뀌었다.'''
assert a in s; s = s.replace(a, b)
a = '    ("KR0003", "2025.1Q", 4),\n'
b = '    ("KR0004", "2025.1Q", 4),     # 2026-10-13: 종전 대상 KR0003 2025.1Q 는 등재가 풀려 이 자리로 옮겼다\n'
assert a in s; s = s.replace(a, b)
i = s.index("def test_a_pin_that_names_a_branch_catches_a_branch_change_not_only_a_residual")
j = s.index("    finds = copy.deepcopy(findings)", i)
new_head = '''def test_a_pin_that_names_a_branch_catches_a_branch_change_not_only_a_residual(
        records, findings, monkeypatch):
    """갈래 이름으로 박제한 축은 **갈래가 바뀌면** 같은 잔차라도 면제가 아니다.

    2026-08-24 까지 이 시험의 대상은 한화생명 2025.2Q(`branch=CAPPED`)였다. 그 면제는 같은 날
    해제됐다 — 잔차의 원인이 발행사가 아니라 우리 룰의 item47 스코프 오독이었기 때문이다.
    그 뒤 NH농협 2024.3Q 로 옮겼으나 **2026-10-13 그 면제도 풀렸다**(owner 승인 최신 공시 직전 컬럼
    덮어쓰기로 항목 13 이 9,390 이 되어 `2_tier1_bridge` RED 가 사라졌다). 지금 등재분 중 갈래 이름으로
    박제한 버킷은 0 이라, **시험을 지우지 않고** 라이브 RED 에 `branch=CAPPED` 가 실제로 찍히는
    AIG손해 KR0029 2025.3Q 의 박제 flag 를 이 시험 안에서만 갈래 이름으로 바꿔(monkeypatch) 같은 경로를 흔든다.
    지우면 '갈래가 바뀌어도 통과' 라는 사각이 다시 생긴다."""
    code, quarter, rule = "KR0029", "2025.3Q", "2_tier1_bridge"
    patched = copy.deepcopy(gate._TIER2_ISSUER_INCONSISTENT)
    patched[(code, quarter)]["findings"][rule]["flag"] = "branch=CAPPED"
    monkeypatch.setattr(gate, "_TIER2_ISSUER_INCONSISTENT", patched)
    # 대조군: 갈래 이름 박제로 바꿔도 라이브 마스터에선 그대로 통과해야 한다(박제가 라이브 RED 와 맞는다)
    _acc0, red0, _rev0, _det0 = _run(records, findings)
    assert not any(r["code"] == code and r["quarter"] == quarter for r in red0), red0
'''
k = s.index("\n", s.index('"findings"][rule]["flag"], "이 버킷은 갈래 이름으로 박제돼 있지 않다 — 대상을 바꿔라"', i))
s = s[:i] + new_head + s[j:]
open(p, "w", encoding="utf-8", newline=chr(13) + chr(10)).write(s)
