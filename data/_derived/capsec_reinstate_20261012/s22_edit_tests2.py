# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

T = "tests/unit/test_capital_utilization_rules.py"
edit(T, [
("""# 메모 재현표(recompute_47.csv)는 인쇄값 기준이라 아래 21사는 이 결정으로 숫자가 바뀐다 - (규칙, 분자, 소진율) 정확값을 박제한다
# (느슨하게 푼 것이 아니다: 이 21개 값 밖의 26사는 메모 값 그대로). 근거 표 data/_derived/capsec_reinstate_20261012/z3_tier2_before_after_47.*
""",
"""# 메모 재현표(recompute_47.csv)는 인쇄값 기준이라 아래 19사는 이 결정으로 숫자가 바뀐다 - (규칙, 분자, 소진율) 정확값을 박제한다
# (느슨하게 푼 것이 아니다: 이 19개 값 밖의 28사는 메모 값 그대로). 근거 표 data/_derived/capsec_reinstate_20261012/z3_tier2_before_after_47.*
# 2026-10-13 coordinator 정정: 콜일이 지났는데 상환 안 한 채권(past_call_outstanding)은 차감액에서 뺀다 -> 현대해상·DB손해는 메모 값 그대로로 복귀,
# 농협생명 21.1(콜 경과 2,800 제외)·롯데 58.6·흥국화재 53.3·악사 29.2.
"""),
("""    "KR0001": ("R2", 9724.88, 30.8), "KR0002": ("R2", 8288.25, 46.6), "KR0003": ("R2", 5289.77, 50.1),
    "KR0005": ("R2", 5119.32, 45.2), "KR0009": ("R-none", 23522.36, 64.2), "KR0010": ("R2", 7384.19, 20.5),
    "KR0011": ("R-none", 20692.16, 36.0), "KR0032": ("R2", 6908.29, 102.8), "KR0049": ("R2", 0.0, 0.0),
    "KR0068": ("R3", 56155.44, 74.8), "KR0070": ("R2", 6081.29, 70.4), "KR0071": ("R2", 5227.17, 37.0),
    "KR0073": ("R2", 27137.98, 51.5), "KR0076": ("R5", 2109.54, 56.9), "KR0079": ("R3", 2930.93, 24.5),
    "KR0082": ("R3", 2563.95, 31.6), "KR0083": ("R2", 5639.79, 73.1), "KR0099": ("R2", 0.0, 0.0),
    "KR0104": ("R4", 825.57, 4.8), "KR1000": ("R2", 7105.18, 60.9), "KR1011": ("R2", 2749.47, 76.2),
}""",
"""    "KR0001": ("R2", 9724.88, 30.8), "KR0002": ("R2", 8288.25, 46.6), "KR0003": ("R2", 6188.4, 58.6),
    "KR0005": ("R2", 6039.32, 53.3), "KR0010": ("R2", 7384.19, 20.5),
    "KR0032": ("R2", 6908.29, 102.8), "KR0049": ("R2", 370.65, 29.2),
    "KR0068": ("R3", 56155.44, 74.8), "KR0070": ("R2", 6081.29, 70.4), "KR0071": ("R2", 5227.17, 37.0),
    "KR0073": ("R2", 27137.98, 51.5), "KR0076": ("R5", 2109.54, 56.9), "KR0079": ("R3", 2930.93, 24.5),
    "KR0082": ("R3", 2563.95, 31.6), "KR0083": ("R2", 5639.79, 73.1), "KR0099": ("R2", 0.0, 0.0),
    "KR0104": ("R4", 3625.57, 21.1), "KR1000": ("R2", 7105.18, 60.9), "KR1011": ("R2", 2749.46, 76.2),
}"""),
("""            if (b.get("issue_date") or "") < "2023-01-01":
                amt = (b.get("outstanding_mn") or 0) / 100.0""",
"""            # 콜일이 지났는데 상환 안 한 채권(past_call_outstanding)은 실효 만기(콜일)가 지났으므로 뺀다(coordinator 정정 2026-10-13)
            if (b.get("issue_date") or "") < "2023-01-01" and not b.get("past_call_outstanding"):
                amt = (b.get("outstanding_mn") or 0) / 100.0"""),
("""def test_owner_decision_effects_named_in_the_ticket(computed):""",
"""def test_past_call_outstanding_bonds_are_not_deducted(ledger, computed):
    \"\"\"coordinator 정정 2026-10-13: 콜일이 이미 지났는데 상환 안 한 2022년 이전 채권은 인정 자본이 아니므로 기발행 차감액에서 뺀다
    (자본증권의 실효 만기 = 콜일; 발행사도 DB손해·현대해상·농협생명의 기발행 줄에 넣지 않는다). 원장 플래그만 쓴다.\"\"\"
    assert ledger["KR0011"]["sub_legacy"] == 0.0 and ledger["KR0009"]["sub_legacy"] == 0.0          # 1,700 · 2,330 (2022 콜 경과)
    assert ledger["KR0104"]["sub_legacy"] == 8300.0                                                  # 11,100 - 공모채 1-2회 2,800
    assert ledger["KR0003"]["sub_legacy"] == 1390.55                                                 # 2,289.18 - 08차 898.63 (콜 2025-05)
    assert ledger["KR0005"]["hybrid_legacy"] == 1200.0                                               # 2,120 - 제1회 920 (콜 2021-12)
    assert ledger["KR0004"]["sub_legacy"] == 0.0 and ledger["KR0049"]["sub_legacy"] == 0.0         # 엠지손해 680 · 악사 JPY 458.8
    assert (computed["KR0011"]["t2"]["pct"], computed["KR0009"]["t2"]["pct"], computed["KR0104"]["t2"]["pct"]) == (38.9, 70.5, 21.1)


def test_past_call_exclusion_is_load_bearing(tmp_path, monkeypatch):
    \"\"\"변이: 콜 경과 미상환 표지를 무시하면 차감액이 늘어난다(합성 원장).\"\"\"
    doc = {"companies": [{"code": "KR9999", "bonds": [
        {"tier": "subordinated", "issue_date": "2017-05-25", "outstanding_mn": 100000, "past_call_outstanding": True},
        {"tier": "subordinated", "issue_date": "2019-05-25", "outstanding_mn": 50000, "past_call_outstanding": False},
        {"tier": "hybrid", "issue_date": "2016-12-29", "outstanding_mn": 92000, "past_call_outstanding": True},
        {"tier": "hybrid", "issue_date": "2022-03-01", "outstanding_mn": 30000},
        {"tier": "subordinated", "issue_date": "2023-03-01", "outstanding_mn": 70000}]}]}
    p = tmp_path / "bonds.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps({"rows": [{"원보험사코드": "KR9999", "종류": "후순위채", "잔액_억": 1.0, "발행일": "2019-05-25",
                                          "잔액기준일": "2026-06-30"}]}), encoding="utf-8")
    monkeypatch.setattr(R, "BONDS_PATH", p)
    got = R.load_ledger(rows)
    assert got["KR9999"]["sub_legacy"] == 500.0 and got["KR9999"]["hybrid_legacy"] == 300.0
    src = (ROOT / "scripts" / "capital_utilization_rules.py").read_text(encoding="utf-8")
    assert src.count('if b.get("past_call_outstanding") or (b.get("issue_date") or "") >= LEGACY_CUTOFF:') == 1
    ns: dict = {"__name__": "rules_mutant", "__file__": str(ROOT / "scripts" / "capital_utilization_rules.py")}
    exec(compile(src.replace('if b.get("past_call_outstanding") or (b.get("issue_date") or "") >= LEGACY_CUTOFF:',
                             'if (b.get("issue_date") or "") >= LEGACY_CUTOFF:'), "rules_mutant", "exec"), ns)
    ns["BONDS_PATH"] = p
    bad = ns["load_ledger"](rows)
    assert bad["KR9999"]["sub_legacy"] == 1500.0 and bad["KR9999"]["hybrid_legacy"] == 1220.0   # 표지를 무시하면 차감이 늘어난다


def test_owner_decision_effects_named_in_the_ticket(computed):"""),
])
