# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

T = "tests/unit/test_capital_utilization_rules.py"
OLD_START = '''def test_past_call_exclusion_is_load_bearing(tmp_path, monkeypatch):
    """변이: 콜 경과 미상환 표지를 무시하면 차감액이 늘어난다(합성 원장)."""'''
NEW_TEST = '''def test_past_call_exclusion_is_load_bearing(tmp_path, monkeypatch):
    """콜일 <= 분자 기준일 이면 뺀다(콜일에서 직접 판정; 원장 표지는 보조). 변이: 날짜 판정을 지우거나 표지를 지우면 차감액이 늘어난다(합성 원장)."""
    doc = {"companies": [{"code": "KR9999", "bonds": [
        {"tier": "subordinated", "issue_date": "2017-05-25", "outstanding_mn": 100000, "past_call_outstanding": True},
        {"tier": "subordinated", "issue_date": "2019-05-25", "outstanding_mn": 50000, "past_call_outstanding": False},
        {"tier": "subordinated", "issue_date": "2021-04-12", "outstanding_mn": 21000, "past_call_outstanding": False,
         "call_date": "2026-04-12"},                                                   # 표지는 false 인데 콜일이 기준일(2026-06-30) 이전
        {"tier": "hybrid", "issue_date": "2016-12-29", "outstanding_mn": 92000, "past_call_outstanding": True},
        {"tier": "hybrid", "issue_date": "2022-03-01", "outstanding_mn": 30000},
        {"tier": "hybrid", "issue_date": "2022-03-02", "outstanding_mn": 40000, "call_date": "2027-03-02"},   # 콜이 기준일 이후 -> 차감
        {"tier": "hybrid", "issue_date": "2021-06-30", "outstanding_mn": 10000, "call_date": "2026-06-30"},    # 콜일 == 기준일 -> 제외
        {"tier": "subordinated", "issue_date": "2023-03-01", "outstanding_mn": 70000}]}]}
    p = tmp_path / "bonds.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps({"rows": [{"원보험사코드": "KR9999", "종류": "후순위채", "잔액_억": 1.0, "발행일": "2019-05-25",
                                          "잔액기준일": "2026-06-30"}]}), encoding="utf-8")
    monkeypatch.setattr(R, "BONDS_PATH", p)
    got = R.load_ledger(rows)
    assert got["KR9999"]["sub_legacy"] == 500.0 and got["KR9999"]["hybrid_legacy"] == 700.0
    # 분자 기준일이 바뀌면 같은 원장도 다른 값: 2025-12-31 기준이면 2026-04-12 콜 채권은 아직 인정
    assert R.load_ledger(rows, "2025-12-31")["KR9999"]["sub_legacy"] == 710.0
    assert R.quarter_end("2026.2Q") == "2026-06-30" and R.quarter_end("2025.4Q") == "2025-12-31"
    src = (ROOT / "scripts" / "capital_utilization_rules.py").read_text(encoding="utf-8")
    line = 'if b.get("past_call_outstanding") or (cd and cd <= numerator_date):'
    assert src.count(line) == 1
    for new, exp_sub, exp_hyb in (('if b.get("past_call_outstanding"):', 710.0, 800.0),            # 날짜 판정 삭제
                                  ('if cd and cd <= numerator_date:', 1500.0, 1620.0)):            # 표지 삭제
        ns: dict = {"__name__": "rules_mutant", "__file__": str(ROOT / "scripts" / "capital_utilization_rules.py")}
        exec(compile(src.replace(line, new), "rules_mutant", "exec"), ns)
        ns["BONDS_PATH"] = p
        bad = ns["load_ledger"](rows)
        assert (bad["KR9999"]["sub_legacy"], bad["KR9999"]["hybrid_legacy"]) == (exp_sub, exp_hyb), new
'''

# replace the old test body: from OLD_START up to (not including) the next test
p = Path(T)
t = p.read_bytes().decode("utf-8")
i = t.index(OLD_START)
j = t.index("def test_owner_decision_effects_named_in_the_ticket", i)
t = t[:i] + NEW_TEST + "\n\n" + t[j:]
p.write_bytes(t.encode("utf-8"))
print("replaced test body")

edit(T, [
('"KR0001": ("R2", 9724.88, 30.8),', '"KR0001": ("R2", 11824.88, 37.5),'),
('"KR0076": ("R5", 2109.54, 56.9),', '"KR0076": ("R5", 2609.54, 70.4),'),
('"KR0099": ("R2", 0.0, 0.0),', '"KR0099": ("R2", 108.51, 0.8),'),
("""    assert ledger["KR0004"]["sub_legacy"] == 0.0 and ledger["KR0049"]["sub_legacy"] == 0.0         # 엠지손해 680 · 악사 JPY 458.8""",
 """    assert ledger["KR0004"]["sub_legacy"] == 0.0 and ledger["KR0049"]["sub_legacy"] == 0.0         # 엠지손해 680 · 악사 JPY 458.8
    # validation 20261013T0205Z: 표지가 false 여도 첫 콜일이 분자 기준일(2026-06-30) 이전이면 뺀다 - 메리츠 제7회 2,100(콜 2026-04-12),
    # 아이엠라이프 DGB 사모 500(2026-05-07), KB라이프 제1회 1,299.7(2026-05-31)
    assert ledger["KR0001"]["sub_legacy"] == 3860.0 and ledger["KR0076"]["sub_legacy"] == 0.0 and ledger["KR0099"]["sub_legacy"] == 699.8"""),
("""# 농협생명 21.1(콜 경과 2,800 제외)·롯데 58.6·흥국화재 53.3·악사 29.2.""",
 """# 농협생명 21.1(콜 경과 2,800 제외)·롯데 58.6·흥국화재 53.3·악사 29.2.
# validation 20261013T0205Z: 제외 판정을 원장 표지가 아니라 콜일 <= 분자 기준일(2026-06-30)로 -> 메리츠 30.8 -> 37.5 · 아이엠라이프 56.9 -> 70.4 ·
# KB라이프 0.0 -> 0.8 (다른 회사 변동 0)."""),
])
