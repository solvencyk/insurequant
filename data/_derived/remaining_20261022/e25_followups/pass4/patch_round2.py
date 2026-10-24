# -*- coding: utf-8 -*-
"""fix round 1 (ticket 20261024T1000Z): NH 2023.2Q item 15 = 0.0 (structural zero) joins the plan, texts follow."""
from pathlib import Path
B = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4")
def patch(fn, pairs):
    p = B / fn
    s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        assert s.count(old) == 1, (fn, s.count(old), old[:70])
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8", newline="\n")
patch("p01_build_plan.py", [
    ('NH농협손해보험 2023.2Q 손익계산서 앞부분(보험손익·기타사업비용·투자손익·투자이익·보험금융손익·영업이익·영업외손익)과 2023.1Q 보험금융손익을 "',
     'NH농협손해보험 2023.2Q 손익계산서 앞부분(보험손익·기타영업수익[구조적 0]·기타사업비용·투자손익·투자이익·보험금융손익·영업이익·영업외손익)과 2023.1Q 보험금융손익을 "'),
    ('    dict(code="KR0032", cells="2023.2Q item 15 and LOB-note items 6 / 7 / 11 / 12", reason="outside the ticket (no statement line)"),\n',
     '    dict(code="KR0032", cells="2023.2Q LOB-note items 6 / 7 / 11 / 12", reason="outside the ticket (no statement line)"),\n'),
])
patch("make_apply_p4.py", [
    ("NH농협손보 KR0032 2023.2Q items 1/16/17/18/19/20/21 and 2023.1Q item 19", "NH농협손보 KR0032 2023.2Q items 1/15/16/17/18/19/20/21 and 2023.1Q item 19"),
    ("NH농협손보 2023.1Q/2Q statement items 1/16-21", "NH농협손보 2023.1Q/2Q statement items 1/15-21"),
])
print("patched")
