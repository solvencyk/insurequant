# -*- coding: utf-8 -*-
"""patch the note texts of the copied KB라이프 planner (evidence path, wording for the printed-line-less default cell)"""
from pathlib import Path

p = Path("e23_plan.py")
s = p.read_text(encoding="utf-8")
n0 = len(s)
subs = [
    ('LIVE_NOTE = "2026-10-23 parser/ifrs17 (e23, ticket 20261023T0900Z D1~D3: 최신 비교열 채택, owner 결정 2026-10-23 승인)"',
     'LIVE_NOTE = "2026-10-23 parser/ifrs17 (e23, ticket 20261023T0900Z D1 = 옵션 B: KB라이프 FY2023 2023.1Q~3Q 만 최신 비교열 채택, 2023.4Q·2024 불변, owner 결정 2026-10-23)"'),
    ("(증거 e23_plan_{b['code']}.json parts)", "(증거 e23_plan_kblife.json parts)"),
    ("증거 {EVREL}/e23_plan_{b['code']}.json\")", "증거 {EVREL}/e23_plan_kblife.json\")"),
    ("증거 {EVREL}/e23_plan_{c['code']}.json\")", "증거 {EVREL}/e23_plan_kblife.json\")"),
    ('else "마스터 피연산자만"', 'else "인쇄 줄 없음(빌더 기본값 또는 마스터 피연산자)"'),
]
for a, b in subs:
    assert s.count(a) == 1, (s.count(a), a)
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched", n0, "->", len(s))
