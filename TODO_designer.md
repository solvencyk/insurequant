# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-24 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-19 접근성 2차 C8~C15 · C17 완료(push `7fc4971f` · main 배포 `3a91a4ea` 완료, 라이브 4파일 바이트 일치; owner 「C8~C17 진행」)** — compare 카드 제목 h3 → h2(+ `aria-label` 로 접근 이름 최대 840 → 16자, 모양 불변), 섹션 공유 버튼 이름을 섹션별로 고유하게, compare · privacy `<main>` + 포커스 때만 보이는 건너뛰기 링크, 감소 모션에서 Chart.js 애니메이션 · smooth 스크롤 끔(index · K-ICS · IFRS17 차트도 같이), 경과조치 · 중앙값 조작 뒤 `#live` 문구, 테마 토글 `aria-pressed` 제거(바뀌는 레이블만), compare 넓은 화면 손해율 카드에 화면 밖 현재가치 표, privacy 표 영역 `role=region`.
  검사: `scripts/check_a11y_compare_privacy.py --step 3` 4,287 단언 통과, 별도 검증자 25분 상자(제목 모양 HEAD 와 차이 0 · 6페이지 공유 버튼 이름 중복 0 · 건너뛰기 링크 · 감소 모션 · 첫 화면 24조합은 노이즈 이내). 남은 것: C16(WCAG 2.1 대 2.2 목표 결정) · C10 링크 없이 Tab 30번(링크 쓰면 3번).
- **2026-10-19 밤 손해율 비교 단위 선택기 · 오류 제보 내부 접속 제외 · a11y C1·C2·C3·C4·C6 완료(push `a8d9f193` · main 배포 `5221a1b4` 완료; owner 승인)** — 선택기: compare 손해율 카드 · IFRS17 8절 select 하나(구분 · 생보 · 손보 · 재보), 단위 없는 회사는 n/a 줄, 100억원 미만 칸 흐린 점선, 주소 `g=` 는 구분 이름과 단위 키 모두. `report-widget.js` 는 `iq_internal=1` 이면 수집기로 안 보냄. a11y: ? 팝오버 마우스 유예(`common.css` `.is-grace` + `theme.js` `pointerleave` 0.4초), 칩 제거·추가 뒤 포커스, 입력창 `--control-border` · placeholder `--muted`, 모바일 손해율 선 표식.
  독립 검증: 220+507 상태 · 회귀 82건 · 44상태 HEAD 대비 스타일 차이는 입력창 테두리·placeholder·팝오버 다리뿐. 버린 것: ? 옆 삼각형 호버 영역(오른쪽 끝에서 문서를 가로로 넓힘). 남은 것: 일본 오류 제보 위젯 · n/a 문구를 ? 팝오버로 옮길지(C8~C17 은 위 항목에서 완료).
- **2026-10-19 안내 팝업 시작일 10-31 · 손해율 기본 Non-Par · 방명록 내부 접속 제외 · a11y 감사 완료(main 배포 `f96f06b0` 완료; owner 승인)** — 팝업 `NOTICE.showFrom` 2026-10-31(독립 검증 47/47), 선택기 기본 Non-Par(마스터 재계산 0.05pp 이내), `download-survey.js` 가 `iq_internal=1` 방문을 수집기로 보내지 않음. compare·privacy 감사 18건(중간 6 · 낮음 9 · 참고 3)을 `docs/a11y_baseline.md` 와 티켓 `20261019T1400Z` 에.
  남은 것: a11y 티켓 수정(? 팝오버 마우스 접근 · 포커스 유실 · 모바일 손해율 선 마커 등 코드 문제 먼저, 색 변경 5건은 owner 승인 뒤) · 구분 단위 평면 선택기(10-19 밤 owner 「선택기는 조사 추천대로」로 결정·구현·배포 완료, 평면 12개) · 배포 때 HTML 2개 + `panel_compare.json` + `panel_loss_ratio.json` + `theme.js` + `download-survey.js` 한 묶음.

## 열린 일

- [ ] **LIC 2단계(항목 16·17) 적재 후**(2026-10-24 정정: 적재는 2026-10-11 ILP 라운드 3 에서 끝났고 화면 재확인만 남음): 화면은 이미 준비됨(줄무늬 「계산값」 BEL·RA, 합성 데이터로 확인) — 실데이터가 들어오면 빌더 재실행·`--check` 후 화면만 재확인. index 트리맵 재보험·보증은 손해 아래 칸(3열 가로 배치가 필요하면 알려 주세요). 후속 후보: 「CSM 확대(CSM만 자동 스케일)」 토글(owner 정정으로 지금은 안 만듦).

- [ ] **a11y 이월 2건(티켓 `20261019T1400Z` 종결 때 옮김, 2026-10-24)** — C16 터치 대상 크기: owner 가 WCAG 2.1 / 2.2 중 목표를 정해야 기준이 생긴다. C10 「Tab 15번 이내(건너뛰기 링크 없이)」 부기준 미충족: 순서대로 30번 Tab, 건너뛰기 링크로 3번. 고치려면 roving tabindex 가 필요하다.
- [ ] **듀레이션갭 3개 분기 도달 불가** — publishing 과 같이(`TODO_publishing.md`).
- [ ] **팔레트 B 에서 내 판단으로 바꾼 +/△ 색**(올리브 `#4b7f2a`·벽돌 `#b4443a`) — owner 확인 대기.
- [ ] **jp ESRランキング 범례 8개** — owner 판단 대기(2026-09-15b). jp 파일은 이 브랜치에 없다(`lane/jp`, `../iq_jp`, `CLAUDE.md` §1).

## owner 결정 대기 · 휴면

KEYCOLOR/COMPANY-ACCENT 방향 재검토 · MOB-KICS·MOB-IFRS17 owner 권고 2건(가로 스크롤 범위 · 640px 외 breakpoint) · MOB-IFRS17 패널 1~6 정책 ·
VIS-CHARTLEGEND(IFRS17 상각·index 버블 범례) · M3 차트 미세조정 · F17 Panel 3 Tier2(parser 결정 대기) · F16 Panel 5 caption(가능한 회사 명시).

## 결정

- 차트 색 변경 안 함: a11y 감사 C5 · C7 · C18(사별 비교 손해율 선 색 포함) — 값 표에 수치가 같이 표시됨 (owner 2026-10-19).
- 일본 사이트 오류 제보 위젯의 내부 접속 제외는 보류 (owner 2026-10-19).

## 참고

- 페이지 5개: `index.html`(시장지도·버블) · `K-ICS.html` · `IFRS17.html`(7패널, 1=재무상태표 T계정) · `공시보고서.html`(배당현황) · `compare.html`(사별 비교).
- 차트: Chart.js(IFRS17 패널 2~6) · ECharts(CSM 워터폴·treemap·버블). 색은 `IQTheme.chart()` 로 CSS 변수를 읽는다(라이브러리는 `var()` 를 못 먹는다).
- 로컬 미리보기 `python -m http.server 8000`. 프리뷰 창은 `window` scroll 이벤트를 안 뿜는다 — 스크롤 스파이는 합성 이벤트로 검증.
