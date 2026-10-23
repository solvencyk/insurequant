# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/answers/kr0003_lotte.md")
s = p.read_text(encoding="utf-8")
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60])
    s = s.replace(a, b)
sub("4분기 단일분기 CSM 롤포워드는 105.4억원 어긋난 채 닫히지 않는다(검증이 알아야 할 점).",
    "4분기 단일분기 CSM 롤포워드(기초 22,085.6 + 신계약 1,386.8 + 이자부리 223.0 + 가정조정 813.7 + 상각 −542.8 = 23,966.3 대 기말 23,860.8)는 약 105억원 어긋나 닫히지 않는다(검증이 알아야 할 점).")
sub("`tests/fixtures/master_tables_golden.json`·`builder_input_fingerprints.json`·`data/_derived/pl_oci_vs_bs_aoci_warn.json` 을 복원한다",
    "`tests/fixtures/master_tables_golden.json`·`builder_input_fingerprints.json`·`data/_derived/qoq_warn.json`·`data/_derived/pl_oci_vs_bs_aoci_warn.json` 을 복원한다")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
