# Insurequant Designer TODO (Stage 5)

> Last updated: 2026-06-20 · Stage 5/5 — designer
> Prompt: docs/agents/claude-agent-designer.md (skeleton) · Changelog: docs/changelog_designer.md

Session start: read this file + `claude-agent-designer.md` + the page(s) in scope (root HTML files). Publishing ([`TODO_publishing.md`](TODO_publishing.md)) owns master JSONs; designer only reads them and decides how they render. English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

Stage 5 = HTML structure / styling / responsive breakpoints / A11y / chart layout. Desktop pages are in production; KEYCOLOR-V1 K-ICS cancelled by owner (IFRS17 구현 불만족). Mobile scope confirmed; M1 foundation done; full mobile pass open.

**Recent (2026-06-20):**
- **도넛 섹션 잠정 숨김**: K-ICS.html 자본성증권 소진율 패널 `display:none` — 분자 오류(tier1 excess누락·tier2 proxy과대). 마크업/JS 보존. 복구: ifrs17 capital_securities_issuance JSON 완성 후 owner 신호.
- **차트 공통 테마**: Chart.js defaults (Pretendard 폰트, 그리드 #e9ecef, tooltip dark) IFRS17+K-ICS 양 페이지 적용. ECharts 'iq' 테마 IFRS17 waterfall/PL 적용.
- **MOB-KICS 카드뷰**: ≤640px 피벗 테이블 → 분기별 카드(`renderMobileCards`). 서브아이템 들여쓰기. 데스크톱 무변경.
- **KPI 카운트업 애니**: `countUp(el,target,fmt,dur)` ease-out cubic 600ms. index.html 히어로 3개 + IFRS17 Panel 7 KPI 4개. `prefers-reduced-motion` 즉시세팅. **DESIGN-V2 P2 완결.**

**Recent (2026-06-17):**
- **FORWARD_DATA 재임베드**: K-ICS.html L205 `window.FORWARD_DATA` → `templates/forward_capital_latest.json` (37→38사, 2026.1Q 재베이스라인). L1104 Baseline 라벨 2025.4Q→2026.1Q. publishing 트리거 신호 발송.
- **모바일 timeframe 수정 (D9 override)**: `selectPeriods` `isMobile→slice(-1)` 제거 + waterfall 테이블 `_mob` 1버킷 제한 제거. 모바일도 연도/분기 동일 windowing. Playwright 29 GREEN.
- **상각스케줄 Y축 auto-scale**: `toLocaleString` → 데이터 최댓값 기준 조/억/백만 자동 선택 + 타이틀 단위 동기화.
- **예별손해보험 드롭다운 4번째 삽입**: K-ICS.html 하드코딩 옵션에 롯데손해보험 바로 다음 추가.
- **VIS-DONUT 완료 확인**: `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap` → 375px 화면에서 자동 1열 스택(명시적 flex-direction:column 불필요). 이미 구현돼있었음.
- **KEYCOLOR-V1 K-ICS 취소**: owner 지시. IFRS17 구현도 불만족(구리다) — K-ICS 미적용.

**Recent (2026-06-16):**
- **DS1 (frontend-design skill)**: 디자인 시스템 정식화 — 신규 루트 `common.css`(토큰 + 공통 chrome + A11y baseline), 3 HTML 점진 배선(무회귀, 확정결정 4개 유지), 프롬프트 §5 skeleton→정식. **common.css는 신규 배포 에셋**(publishing handoff 필요).
- **DS1b (DESIGN-V2 P2 슬라이스)**: index 히어로 KPI 스트립(총 CSM·중위값·수록사·기준분기) + 회사 typeahead 점프. 진입 애니(degrade-safe). 토큰/팔레트/△ 유지.
- **DS2 (webapp-testing/Playwright)**: 회귀 하니스 `tests/regression_dashboards.py`(+README) — **29 assert GREEN**. venv playwright+chromium 설치(번들 Chromium 구동 = Edge dump 0바이트 우회). owner QA 글리치 자동화.
- **G1/G2 (inbox 0506Z)**: IFRS17 재보험 +버튼 → K-ICS `.subtoggle` 양식 통일(.subtoggle→common.css 승격) · Panel2 점선 시리즈 legend "신계약 CSM 시계열 (점선)" 명시.
- **W1**: CSM waterfall(P1)+PL table(P4) 기간 윈도잉 통일 / 롯데 PL waterfall 투자손익 zero-crossing → ECharts custom renderItem.
- **상류 의존**: sensitivity_heatmap의 `period`/`as_of` null → parser inbox `20260616T0030Z`.

## 🔴 Open — P1

### KEYCOLOR-V1 — 회사 키컬러 액센트 시스템 ~~(K-ICS 취소, IFRS17 재검토 대기)~~
IFRS17 적용 완료 2026-06-13. K-ICS 적용은 **owner가 2026-06-17 취소** (IFRS17 구현 불만족). IFRS17 키컬러도 재검토 필요 — owner 피드백 대기.
- [x] IFRS17 적용 완료 (2026-06-13)
- [~] K-ICS 적용: **owner 취소 (2026-06-17)**
- [ ] (보류) 전체 키컬러 방향 재검토 — owner 피드백 후

### DESIGN-V2 — de-AI 디자인 오버홀 (proposal delivered 2026-06-11, awaiting owner sign-off)
Owner complaint: site looks AI-generated. Audit done (4 pages + barabom.me reference — actual findings: Spoqa Han Sans Neo webfont + restrained neutrals + 0.1-0.2s micro transitions, NOT heavy animation). Phases:
- [ ] **P1 quick wins (~half day)**: Pretendard Variable + `font-variant-numeric:tabular-nums` 전역 / 탈부트스트랩 팔레트(#0d6efd·#f8f9fa 교체, 잉크+페이퍼+딥블루 1액센트) / favicon(IQ 모노그램)+OG+meta description / footer(출처·기준분기·면책) / 이모지 placeholder 제거 / radius 12→6px / Chart.js·ECharts 색 CSS 변수화 (기본 teal/pink 퇴출). [부분 착수: P1-QUICKWIN 일부 done 2026-06-12, 팔레트 교체는 보류]
- [x] **P2 structural (1~2d)**: ✅ common.css · ✅ index 히어로 KPI 스트립+typeahead · ✅ scroll-reveal · ✅ 차트 공통 테마 · ✅ KPI 카운트업 애니(index 3개+IFRS17 Panel7 4개, ease-out 600ms, 2026-06-20) — **완료**
- [ ] **P3**: M3 잔여(도넛 stack·범례) 흡수, 다크모드(선택)
- [x] **TREEMAP-SCALE**: 트리맵 색 임계 앵커 130/200% + 범례 임계 표기 — done 2026-06-13 (권고선=130%, 민감도 패널 150%→130% 정합)
- [ ] **COMPANY-ACCENT**: 회사 키컬러는 배경 틴트 대신 "액센트 1곳" 원칙(패널 제목 2px 룰 + 회사명 칩 + 차트 주 시리즈, 저채도 변형 23사 맵) — 시안 owner 승인 후

## 🟠 Open — P2

### MOB-KICS — K-ICS.html full mobile layout (scope confirmed by owner 2026-06-12)
Owner confirmed scope: **full-panel mobile pass + alternative render** (not foundation-only). M1 foundation already in place (header/tabs/table scroll, chart heights ↓).
- [x] Donuts stacked vertically — `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap`으로 375px에서 자동 1열 스택. 이미 구현됨 (2026-06-17 확인).
- [x] Forward-chart legend reposition — `position: window.innerWidth < 640 ? "bottom" : "top"` (2026-06-17)
- [x] Dense table → card view (가/나/다 sub-items) — `renderMobileCards` ≤640px (2026-06-20)
- [ ] **(owner open rec 1)** horizontal-scroll range for dense panels — decide which panels scroll vs reflow
- [ ] **(owner open rec 2)** breakpoint set — confirm thresholds beyond the single 640px (e.g. <400px sub-query)

### MOB-IFRS17 — IFRS17.html full mobile layout (scope confirmed by owner 2026-06-12)
Owner confirmed scope: **full-panel mobile pass + alternative render**. M1 foundation only so far.
- [ ] Panel 1–6 mobile policy: which to keep, which to collapse, which to swap for alternate viz
- [ ] **(owner open rec 1)** horizontal-scroll range for dense panels
- [ ] **(owner open rec 2)** breakpoint set confirmation
- (shares the two owner open recs with MOB-KICS — resolve once for both pages.)

### VIS-DONUT — K-ICS donut row stacks on phones ✅ 완료
- [x] `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap` → 375px 화면에서 자동 1열 스택. 명시적 flex-direction:column 불필요. 이미 구현됨 (2026-06-17 확인).
- [x] Labels legible: 각 도넛이 전체 너비 차지, 레이블 공간 충분.

### VIS-CHARTLEGEND — chart legend/axis density on mobile
- [x] K-ICS forward + IFRS17 hist/NB legend → bottom on mobile (`window.innerWidth < 640`) (2026-06-17)
- [ ] IFRS17 amort + index bubble legend (amort display:false OK, bubble ECharts top=8 review later)

### M3 — chart fine-tuning (roll-up of VIS-DONUT + VIS-CHARTLEGEND + misc)
- [x] K-ICS 도넛 2개 세로배치 (= VIS-DONUT) — 이미 구현됨
- [x] Forward 라인 범례 위치 (= VIS-CHARTLEGEND) — done 2026-06-17
- [ ] 차트 미세조정 across pages

### Panel 7 — 원천지표 카드 ✅ 완료 (2026-06-17)
IFRS17.html 대시보드 최상단에 4-card KPI strip 추가(기말 CSM 잔액·CSM 상각·신계약 CSM·NB CSM 배수). `wfVal(company,latestQ,6/5/2)` + `ix.nbm` 기반. 2열 모바일 그리드.

### INDEX-BUBBLE-V2 HTML side — 4축 bubble rendering
Publishing ships the data (`TODO_publishing.md` INDEX-BUBBLE-V2). Designer ships the ECharts spec:
- [ ] 4축 mapping: X=당기순이익 / Y=CSM 잔액 / size=신계약 CSM / color=신계약 CSM 배수
- [ ] Mobile rendering: 4축 → simplified (e.g. bar 또는 list with sort options)
- [ ] Click → cross-nav (existing pattern)

### F17 Panel 3 — Tier2 LOB drill-down rendering (when publishing ships Tier2 JSON)
Publishing currently has Tier1 4-bar in production. Tier2 (LOB 장기/자동차/일반 stacked) waits on parser F17 decision + publishing assembly.
- [ ] Stacked bar / waterfall design (손보만, LOB visible)
- [ ] 생보 alt-rendering (장기 전사 fallback)
- [ ] Caption variant per-company taxonomy (장기/자동차/일반 vs 보장성/물보험/저축성)

## ✅ Done (archive)
- QA-GLITCH-0614 owner 라이브QA: K-ICS 드롭다운 누락사 보강(30→48, fillMissingCompanies) + 현대해상 키컬러 #FFB81C + ΔCSM 헤더 억원 + 모바일 표 패딩/nowrap — 2026-06-14 (changelog 06-14). 상류대기: shock표기통일·흥국행분리(parser), 소진율 100%+캡(publishing)
- TREEMAP-SCALE 트리맵 색 임계 앵커 130/200% + 범례 임계표기 (권고선=130%, 민감도 패널 150%→130% 정합) — 2026-06-13 (changelog 06-13)
- KEYCOLOR-V1 IFRS17 적용(워터폴 total + Panel2/5 라인 + Panel3 상각막대 + select 링 + 스와치, WCAG 보정) — 2026-06-13 (changelog 06-13)
- NAME-ABBR index 회사 약칭 + 트리맵 '기타' 묶음 — 2026-06-12 (changelog 06-12)
- SHINHAN-EZ-PAA 신한EZ손해(KR0051) CSM 미공시 사유 표기 — 2026-06-12 (changelog 06-12)
- SAMO-ALL 음수 △(세모) 표기 전면화 (K-ICS + IFRS17) — 2026-06-12 (changelog 06-12)
- KICS-RISK-TOGGLE 생명장기·시장위험액 하위 +/− 토글 (29~35·36~40) — 2026-06-12 (changelog 06-12)
- P1-QUICKWIN Pretendard+tabular/파비콘/메타·OG/푸터/이모지 제거 (4p, 팔레트 보류) — 2026-06-12 (changelog 06-12)
- BUBBLE-LOG index 버블 X축 log10 + 라벨 보정 — 2026-06-12 (changelog 06-12)
- F-SENS-PANEL K-ICS 금리 민감도 패널 (kics_rate_sensitivity.json, coverage 29/30) — 2026-06-11 (changelog 06-11)
- F-BUBBLE-MLIST index.html 모바일 CSM 버블 → 리스트 (M2 미러) — 2026-06-11 (changelog 06-11)
- F-PL-WF Panel 3 당기순이익 bridge waterfall (PL_breakdown.json) — 2026-06-07 (changelog 06-07)
- F-WF-WINDOW Panel 1 windowed CSM waterfall (company × 연도/분기) — 2026-06-07 (changelog 06-07)
- M1 Mobile responsive foundation (4 pages, `@media max-width:640px`) — 2026-05-28 (changelog 05-28)
- M2 index.html treemap → vertical list on phones (`renderList()`) — 2026-05-28 (changelog 05-28)
- INDEX-TREEMAP-CLEAN desktop treemap label cleanup (size-aware) — 2026-05-28 (changelog 05-28)
- INDEX-LIST-SORT mobile list sort → 지급여력기준금액 desc — 2026-05-28 (changelog 05-28)
- IFRS17-PANEL-CLEAN KPI 카드 4개 + BS 스냅샷 panel 제거, 패널 1–6 재번호 — 2026-05-28 (changelog 05-28)
- F6-HTML F6 yearly CSM amort Panel 2 (desktop 10y / mobile 5y) — 2026-05-28 (changelog 05-28)
- F17-PANEL3 Panel 3 clean 4-bar swap — 2026-05-30 (changelog 05-30)
- P1-HTML-SINGLE HTML single-source refactor (templates/*.html 삭제, root sole copy) — 2026-05-28 (changelog 05-28)
- P4-DEAD-CDN index.html dropped unused xlsx.full.min.js CDN (~900KB) — 2026-05-28 (changelog 05-28)
- CONSOLE-CLEAN debug console.log cleanup across pages — 2026-05-28 (changelog 05-28)
- INDEX-C12 index treemap + IFRS17 quadrant (items 27/28 default) — done
- KICS-HTML-SUB K-ICS.html sub-items + transition toggle + JSON sync — done
- F1-HTML index.html → IFRS17 cross-nav (ECharts on('click') → URL param) — done (`fcdd544`)

## 🗂️ Conventions reference

**Responsive breakpoints**
- M1 foundation: `@media (max-width:640px)` on all 4 pages. Header/tabs/chart heights/table scroll.
- M2: index.html ≤640px swaps treemap → vertical list (`renderList()` mirrors `render()`).
- M3: donut stack + legend reposition + chart fine-tuning.

**Chart libraries (committed)**
- Chart.js: IFRS17 Panels 2–6
- ECharts: Panel 1 (CSM waterfall), index treemap, bubble

**Page roster (root single-source since 2026-05-28)**
- `index.html` — market map + IFRS17 quadrant + bubble
- `K-ICS.html` — per-insurer detail + sub-items + forward outlook
- `IFRS17.html` — 6-panel dashboard
- `공시보고서.html` — static info

**Local preview:** `python -m http.server 8000` from repo root. (preview_eval 반복 행 시 Edge headless `--dump-dom` 대체; 좀비 포트 회피로 현재 8889.)

## Reading order for designer subagent
1. This file (`TODO_designer.md`) + [`docs/changelog_designer.md`](docs/changelog_designer.md)
2. [`docs/agents/claude-agent-designer.md`](docs/agents/claude-agent-designer.md)
3. Root HTML page(s) in scope
4. Master JSON schema (publishing's output) for the panel you touch — read-only
5. Root [`TODO.md`](TODO.md) for cross-stage roadmap notes

## Hand-off
- **From publishing**: notification that a master JSON changed (`manual_html_edit` warn) or that a new field needs rendering.
- **To human**: designer never pushes. Hand off to publishing for the commit message + push recommendation.
