# -*- coding: utf-8 -*-
"""Derive this folder's planner from the shared e23_plan.py by asserted substitutions (each must hit exactly once).  Read-only on every master / gold / provenance / test."""
from pathlib import Path

p = Path(__file__).resolve().parent / "e23_plan.py"
s = p.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:100])
    s = s.replace(a, b)


sub('E23 = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3"',
    'E23 = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb_load2"')
sub('EVREL = "data/_derived/remaining_20261022/e23_d1_d3"', 'EVREL = "data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb_load2"')
sub('LIVE_NOTE = "2026-10-23 parser/ifrs17 (e23, ticket 20261023T0900Z D1~D3: 최신 비교열 채택, owner 결정 2026-10-23 승인)"',
    'LIVE_NOTE = "2026-10-23 parser/ifrs17 (e23, ticket 20261023T0900Z D3: 케이디비생명 KR0072 FY2023 2023.1Q~4Q 최신 비교열 채택, owner 결정 2026-10-23)"')
sub("증거 {EVREL}/e23_plan_{b['code']}.json\")", "증거 {EVREL}/e23_plan_kdb.json\")")
sub("증거 {EVREL}/e23_plan_{c['code']}.json\")", "증거 {EVREL}/e23_plan_kdb.json\")")
sub("(증거 e23_plan_{b['code']}.json parts)", "(증거 e23_plan_kdb.json parts)")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok", len(s))
