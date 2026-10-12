# -*- coding: utf-8 -*-
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/disclosure/_meta/ifrs17_owner_followups_runlog_20261012.md"
s = open(p, encoding="utf-8", newline="").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:60], s.count(a))
    s = s.replace(a, b)
rep("`CSM_sensitivity.json` HEAD 와 바이트 동일", "`CSM_sensitivity.json` HEAD 와 내용 동일")
rep("한화생명은 패널이 연결 표(88,752.04억, 행 수 점수 19 > 18)를 골라 마스터 y1~y10 이 연결 값이었다(기말 CSM 87,136.5 는 별도).",
    "한화생명은 패널이 연결 표(88,752.04억)를 골라 마스터 y1~y10 이 연결 값이었다(기말 CSM 87,136.5 는 별도; 이유는 `csm_amort_schedule_fix_runlog_20261011.md` §9-2 — 행 수 점수가 별도 우선 규칙보다 먼저 결정한다).")
rep("시험: viz 골든 2종 · 배당 · 상각 단위시험 13 통과", "시험: 마스터테이블 골든 · viz 골든 2종 · 배당 · 상각 단위시험 13 통과")
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
