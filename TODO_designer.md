# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-07 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-07 og:image 링크 미리보기 카드** — 루트 5개 페이지에 `og:image`·`twitter:card` meta + `og-image.png`(트리맵+버블맵 장식 카드, 원본 `docs/og-image.src.html`).
  `ALWAYS_KEEP` 등재. owner 직접 지시로 orchestrator 가 작성·배포. 라이브 커밋 `git log origin/main -- og-image.png`.
- **2026-09-22 K-ICS 금리 민감도 패널 교체** — 순자산 듀레이션/컨벡서티 2카드 → 자산D/부채D/듀레이션갭 3카드(owner 지시).
  컨벡서티는 폐지(K-ICS 상승/하락 충격 비대칭). 라이브 `22e2471`.
- **2026-09-21c IFRS17·기타공시 헤더 셀렉트 + 기간 토글 이식**, 토글 CSS 를 `common.css` 로 승격, 섹션 앵커 착지 오프셋을 헤더 실측으로. `6a51b7a`.

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
