# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-08 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-08 사별 비교 `compare.html` 신규** — 회사 1~4곳의 최신 공시 값을 지표별 막대로 비교(지급여력비율·기본자본비율·기말 CSM·신계약 CSM 배수·보험손익·당기순이익·ROE·유지율 13/25/37/61회차 한 차트·손해율), 같은 유형(생보/손보) 업계 중앙값, 검색창 추천(기말 CSM 위 2·아래 1, 기준은 화면에 안 보임).
  파일 `compare.html`·`data/compare/panel_compare.json`·`scripts/viz_build_compare_panel.py`(`--check`)·5개 페이지 탭·`sitemap.xml`·테스트 배선. owner 직접 지시로 orchestrator 가 작성·배포. 라이브 커밋 `git log origin/main -- compare.html`.
  남은 것: 모바일 실기기 확인, 막대 색(틸+회색)·지표 목록 owner 확인, 서치콘솔 sitemap 재제출.
- **2026-10-08 IFRS17 섹션 8·9 (손해율 가정 · 판매채널별 유지율), 라이브** — 두 표를 접이식 [+] 트리(기본 접힘, 모두 펼치기/접기)로, 손해율 곡선은 monotone 곡선 + 경과연수 비례 x축(640px 이하 모바일은 칸 균등), 9 제목은 "9) 판매채널별 유지율" + 작은 설명줄. 파일 `IFRS17.html`·`scripts/viz_build_persistency_lossratio_panels.py`·패널 JSON 2개·`tests/test_push_gate_wiring.py`·docs 2.
  라이브 main `c72359f`·`0a07663`·`58dff57`. 상세 `docs/changelog_designer.md` 2026-10-08 (3차).
- **2026-10-08 index 마켓맵 보조 목록(`#ratio-sr-list`, `.sr-only`)** — 회사별 "K-ICS 지급여력비율 X%, 기본자본비율 Y%" 를 한 줄씩 글자로(토글로만 보이던 기본자본비율 보강).
  처음엔 표였으나 구글 AI 개요가 열 제목 없이 행만 읽어 기본자본비율을 282.8% 로 오답 → 줄마다 지표명을 붙인 목록으로 교체. `GROUPED`·`samoNum` 으로 JS 가 채움, 픽셀 동일.
  owner 직접 지시로 orchestrator 가 작성·배포. 라이브 커밋 `git log origin/main -- index.html`. 남은 것: 서치콘솔 재색인 뒤 AI 개요 재확인.

## 열린 일

- [ ] **듀레이션갭 3개 분기 도달 불가** — publishing 과 같이(`TODO_publishing.md`).
- [ ] **IFRS17 모바일 가로 넘침 160px** — 375px 에서 `TABLE` 이 407px. 이번 변경 전 라이브에도 있던 것. 표를 `.table-wrap` 스크롤 안에.
- [ ] **팔레트 B 에서 내 판단으로 바꾼 +/△ 색**(올리브 `#4b7f2a`·벽돌 `#b4443a`) — owner 확인 대기.
- [ ] **jp ESRランキング 범례 8개** — owner 판단 대기(2026-09-15b).

## owner 결정 대기 · 휴면

KEYCOLOR/COMPANY-ACCENT 방향 재검토 · MOB-KICS·MOB-IFRS17 owner 권고 2건(가로 스크롤 범위 · 640px 외 breakpoint) · MOB-IFRS17 패널 1~6 정책 ·
VIS-CHARTLEGEND(IFRS17 상각·index 버블 범례) · M3 차트 미세조정 · F17 Panel 3 Tier2(parser 결정 대기) · F16 Panel 5 caption(가능한 회사 명시).

## 참고

- 페이지 4개: `index.html`(시장지도·버블) · `K-ICS.html` · `IFRS17.html`(7패널, 1=재무상태표 T계정) · `공시보고서.html`(배당현황).
- 차트: Chart.js(IFRS17 패널 2~6) · ECharts(CSM 워터폴·treemap·버블). 색은 `IQTheme.chart()` 로 CSS 변수를 읽는다(라이브러리는 `var()` 를 못 먹는다).
- 로컬 미리보기 `python -m http.server 8000`. 프리뷰 창은 `window` scroll 이벤트를 안 뿜는다 — 스크롤 스파이는 합성 이벤트로 검증.
