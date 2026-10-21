# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("TODO_validation.md"); s = p.read_text(encoding="utf-8")
head_old = s.split("\n", 3)[2]
assert s.startswith("# Insurequant Validation TODO (Stage 3)")
lines = s.split("\n")
# line index 2 is the "> 갱신 ..." line
assert lines[2].startswith("> 갱신 2026-10-13")
lines[2] = "> 갱신 2026-10-22 (31차 교보 KR0073 CSM·PL 재작성 기준 적재 `3e53aef8` 독립 검수 + tax22_src 룰 최신 비교열 판 인정 + 골든 정리) · 프롬프트 `docs/agents/claude-agent-validation.md` · 이력 `docs/changelog_validation.md`"
s = "\n".join(lines)
marker = "## Status (최신 3개)\n\n"
entry = (
"- **2026-10-22 (31차) 교보생명 KR0073 CSM·PL 「재작성 기준」 적재(`3e53aef8`) 독립 검수 + `tax22_src` 룰 수정 + 골든 정리 (대상 커밋 `3e53aef8`, 후속 `eea3f61c`)** — "
"원문 자체 재독(`vreader.py`, parser 코드 미사용): PL 항목 1·4·17·19·20·22·23·24·25·31 x 2023.1Q~2024.2Q 60/60 · CSM 항목 1~6 x 7분기 일치(0건 불일치), CSM 상각 대 PL 항목 4 짝 6/6 정확히 닫힘, 2024.3Q·4Q 누계 불변, 교보 밖 변경 0(마스터 · 출처표 · 골드 · 장부 전수 대조).\n"
"  룰: `tax22_src` 가 같은 분기 원공시 판 **또는** 다음 해 같은 기간 캐시 전기 열(`_tax22_prior_tier1`, 빌더와 같은 `_parse`) 중 하나와 맞으면 통과. 전 643버킷 시뮬: 닫힘 4(교보 2023.3Q~2024.2Q) · 깨짐 0 · 주입 탐지 282/282 불변, 변이시험 2종 신설(분기 제거 시 교보 4칸 RED 복귀). 게이트: tax22_src 278P/4F -> 282P/0F · 데이터계약 RED 0 · 골든 `master_tables`(pl_bridge · csm_amort_identity · qoq_warn 3필드, 교보 행만 원인 입증) + 입력지문 `viz_ifrs17_panels` 갱신.\n"
"  발견: **2023.3Q 단일분기(값_당분기) 재작성 기준 이음매** = parser 티켓 `20261021T1655Z`(PL 항목 24 마스터 83,882 대 공시 3개월 열 8,175 · CSM 단일분기 항등식 +960.03억; 판정: 누계 방식에선 불가피하나 값을 싣는 것은 비추천, 선택지 A·B·C 제시). 남은 것: 그 티켓 · 단일분기 항등식 룰 설계(아래 열린 일).\n"
)
assert marker in s
s = s.replace(marker, marker + entry, 1)
# open item
open_marker = "## 열린 일\n\n"
item = (
"- [ ] **단일분기(값_당분기) 항등식 룰 설계 범위(룰 없음 -> 등재 금지, 설계만)** — 현재 어떤 게이트도 `기초_분기 + 신계약 + 이자 + 가정 + 상각 = 기말_분기`(값_당분기 기준)를 안 본다. 전 회사 333 버킷 실측 5건 어긋남"
"(교보 2023.3Q +960.03 · 메리츠화재 2023.3Q +4,007.3 · 한화생명 2023.3Q −950.1 · KB라이프 2023.4Q −126.4 · 롯데손보 2024.4Q +105.3; `data/_derived/kyobo_validation_20261022/census_quarterly_closure.py`). "
"전부 3Q/4Q 에서 재작성 기준과 이전 분기 기준이 섞인 유형으로 보이나 회사별 원인은 미확인. 룰을 만들면 이 5건의 처리(수정 vs owner 등재)가 먼저 결정돼야 RED=0 이 된다. "
"PL 쪽은 3개월 열 인쇄값 대조가 원문 필요라 전 회사 룰이 못 된다(교보만 `v_quarterly_3m.py` 로 실측).\n"
"- [ ] **tax22_src 가 못 보는 잔여(참고)** — 교보 외 17사 51버킷에서 FS-API 다음 해 전기 열이 마스터(원공시 판)와 다르다(`sim_other_vintage_buckets.txt`; 마스터 원공시 판 97칸 · 전기 열 판 15칸). 「확실히 검산 닫히는 것만 덮어쓰기」 방침상 의도된 잔여일 수 있다. 방침 변경이 있으면 그 칸들이 다음 후보.\n"
)
assert open_marker in s
s = s.replace(open_marker, open_marker + item, 1)
p.write_text(s, encoding="utf-8", newline="")

c = Path("docs/changelog_validation.md"); t = c.read_text(encoding="utf-8")
assert t.startswith("# Validation Changelog (Stage 3)")
t = t.replace("> Last updated: 2026-10-13 (30차", "> Last updated: 2026-10-22 (31차 교보 KR0073 재작성 기준 적재 독립 검수 + tax22_src 룰 수정 + 골든 정리 · 30차", 1)
anchor = "## 2026-10-13 (30차) --"
entry2 = open("data/_derived/kyobo_validation_20261022/changelog_entry.md", encoding="utf-8").read()
assert anchor in t
t = t.replace(anchor, entry2 + "\n" + anchor, 1)
c.write_text(t, encoding="utf-8", newline="")
print("ok")
