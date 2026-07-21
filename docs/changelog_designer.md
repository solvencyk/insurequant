# Insurequant Changelog — Designer Stage

> Last updated: 2026-07-21 · Stage 5/5 — designer
> Prompt: docs/agents/claude-agent-designer.md · TODO: TODO_designer.md

Scope: HTML structure / styling / responsive breakpoints / chart layout / A11y. Master JSON content is **publishing** ([`changelog_publishing.md`](changelog_publishing.md)) — designer reads them but does not modify. Cross-stage history: `docs/claude-changelog.md`.

---

## 2026-07-21 — A11y baseline + audit (inbox `20260721T0233Z`)

Owner backlog item: adopt an A11y audit baseline (owner had reviewed 42 external skills, flagged `ui-ux-pro-max` as a fit for the designer stage's long-open A11y TBD). Went local instead — see rationale in `docs/a11y_baseline.md` §4.

- **Baseline formalized**: WCAG 2.1 AA, table + method in `docs/a11y_baseline.md`. New tool `scripts/a11y_contrast_check.py` (WCAG contrast ratio + protanopia/deuteranopia colorblind simulation via linear-RGB matrix transform — replaces hand-computed contrast checks). New local skill `.claude/skills/a11y-audit/SKILL.md` for repeat audits.
- **Audited all 4 deployed pages** (index/K-ICS/IFRS17/공시보고서): color contrast (every `common.css` token + page-local literal used as text), chart-palette colorblind confusability (K-ICS teal/pink pair, IFRS17 `NB_LINE_COLORS` 6-color palette, index treemap/bubble diverging gradients), keyboard access (every `addEventListener('click')` on a non-native element), focus visibility, form-label association.
- **Fixed (purely additive, no rendered-value change)**:
  - `index.html` treemap cells (`.cell`) and mobile list rows (`.li-row`) were click-only — the page's primary company→detail navigation had **no keyboard path** (WCAG 2.1.1 fail). Added `tabindex="0"`, `role="link"`, `aria-label` (reused the existing `title` text), and a `keydown` handler (Enter/Space → same nav as click).
  - `index.html` custom toggle switch hides its real `<input>` at 0×0/opacity:0, so the sitewide `:focus-visible` ring landed on an invisible element (WCAG 2.4.7 fail). Added `.toggle-input:focus-visible + .toggle-label{outline:...}` targeting the visible label.
  - `공시보고서.html` was the one page **not** linking `common.css` — meaning it had no focus-visible ring and no `prefers-reduced-motion` handling at all. Added the `<link>` in the same position as the other 3 pages.
  - 10 chart `<canvas>`/ECharts `<div>` containers (K-ICS ×5, IFRS17 ×5, index ×2) had no `role`/`aria-label` for screen readers. Added `role="img"` (`role="group"` for the treemap, since its cells are now focusable link children) + concise Korean labels.
  - Active-tab links (`K-ICS.html`, `IFRS17.html`, `공시보고서.html`) had no `aria-current` — screen readers couldn't tell which page is current beyond the color-only highlight. Added `aria-current="page"` alongside the existing `active` class (`index.html` has no self-referencing tab, no change needed there).
- **Owner-review queue** (touches an existing rendered value — owner-gated per `common.css`'s own token-value rule, not auto-fixed): `--muted` on `--card` = 4.45:1 (just under AA); index.html bubble-legend bold-green text = 3.30:1; `#adb5bd` "no data" placeholders = 2.07:1; IFRS17 `NB_LINE_COLORS` has 2 pairs (orange/red, purple/teal) that get close under deuteranopia/protanopia simulation; index.html treemap/bubble red↔green diverging scales lose contrast under the same simulation (partially mitigated — every cell already has a tooltip + on-cell numeric label). Full detail + severities in `docs/a11y_baseline.md` §2b.
- **Corrected a stale doc note**: the previous `#ff9f40` medium-confidence-badge gap in `claude-agent-designer.md` §5.3 no longer applies (literal isn't in any of the 4 pages anymore) — removed.
- **Verification**: Claude Browser preview, all 4 pages, 1280px + 375px — 0 console errors. Dispatched `Enter` keydown on a treemap cell → navigated to `K-ICS.html?company=...` exactly like a click. `공시보고서.html` confirmed loading `common.css` with `:focus-visible` rule present.
- **Docs**: `docs/agents/claude-agent-designer.md` §5.3 rewritten to point at the new baseline doc + skill instead of the old ad-hoc gap list.

## 2026-06-20

- **도넛 섹션 잠정 숨김** (inbox 20260620T0238Z): K-ICS.html `#donut-section-panel`(`<div class="panel">` L156)에 `style="display:none"` 추가 — 자본성증권 소진율 도넛 2개(tier1·tier2) 분자 오류로 잠정 비표시. 마크업/JS/데이터 보존, 복구는 `style` 제거만으로 가능. inbox resolved.
- **차트 공통 테마** (DESIGN-V2 P2): Chart.js `Chart.defaults` 전역 설정 — Pretendard 폰트·그리드 `#e9ecef`·틱 `#6c757d`·tooltip dark(rgba 33,37,41,0.9). IFRS17.html ECharts에 'iq' 테마 등록(`echarts.registerTheme`) + `echarts.init(el,'iq',...)` 적용. K-ICS.html Chart.js 동일 defaults 적용.
- **MOB-KICS 카드뷰** (MOB-KICS): K-ICS.html 피벗 테이블 → 모바일(≤640px)에서 분기별 카드 렌더. `renderMobileCards(data,quarters,displayOrder)` 신설 — 분기=카드헤더, 항목=행(`kics-mob-row`), 서브아이템 들여쓰기(`sub`). `renderPivotTable`에서 `window.innerWidth<640` 분기 후 early-return. 기존 데스크톱 테이블·subtoggle 로직 무변경.
- **KPI 카운트업 애니** (DESIGN-V2 P2 완결): `countUp(el,target,fmt,dur)` — ease-out cubic, 600ms, `prefers-reduced-motion` 즉시세팅. index.html 히어로 KPI 3개(총CSM·지급여력비율·수록사), IFRS17.html Panel 7 KPI 4개(기말CSM·상각·신계약CSM·NB배수) 적용. text-only KPI(기준분기)는 미적용.
- **검증**: Playwright 29/29 GREEN.

## 2026-06-16 (W1) — 워터폴/PL 기간 윈도잉 통일 + 롯데 PL 부호버그 + inbox 정리 (owner 직접)

- **inbox 정리**: answered designer 9건 전부 `inbox/_resolved/`로 이관(designer inbox open 0).
- **기간 윈도잉 통일**(owner): CSM waterfall(P1) + PL table(P4)을 시계열과 동일 규약으로 — **분기=최신 포함 직전 5분기**(WF_Q_WINDOW 6→5), **연도=연말+최신부분 [2023,2024,2025,2026.1Q]**. PL table은 `selectPeriods` 재사용(plTablePeriods 재작성, 연도 라벨 FY2025→2025로 시계열과 정합).
- **롯데손보 PL waterfall 투자손익 부호버그**: 데이터는 정상(투자손익 -55,656백만=△557억, 보험손익 +27,200). 원인=**zero-crossing 렌더버그** — 스택+투명 placeholder 방식이 0선 넘는 step에서 placeholder(음수)/colored(양수)를 양·음 따로 쌓아 빨강 막대가 0 위로 뜸. **fix=ECharts custom renderItem**으로 막대를 [min,max] 직접 그림(`encode:{y:[0,1]}` 자동 스케일). 보험손익(+0.03) → 투자손익이 0선 아래로 뻗어 끝점 △0.03. (CSM waterfall은 CSM이 stock이라 0선 안 넘어 무영향.)
- **검증**: Playwright 하니스 +5 assert → **29 GREEN**(롯데 geo y0>0>y1, 윈도잉 분기5/연도4, 콘솔0).

## 2026-06-16 (G1/G2) — IFRS17 +버튼 SOT 통일 + 점선 시리즈 legend 명시 (inbox 20260616T0506Z)

owner 라이브 QA. master 무수정, 확정결정 4개 유지.

- **G1 재보험 +버튼 → K-ICS `.subtoggle` 미러**: `.subtoggle`(+:hover)를 **common.css로 승격**(§5 공유 컴포넌트), K-ICS inline 제거. IFRS17 장기재보험 토글을 inline-styled `<span>＋`→**`<button class="subtoggle">`**(동일 마크업·`+`/`−`·`aria-expanded`·이름 뒤). 양 페이지 단일 SOT.
- **G2 점선 시리즈 식별**: Panel 2 dataset 라벨을 코드주석→legend로. 실선="기말 CSM 잔액 (실선)", 점선="**신계약 CSM 시계열 (점선)**". legend·tooltip 동일, 스와치 색만으론 못 가리던 점 해소.
- **검증**: Playwright 하니스에 G1/G2 assert 추가 → **24 GREEN**(fresh 브라우저). ※preview는 구 common.css 캐시로 +버튼이 처음 UA버튼처럼 보였으나 fresh 로드 정상.
- **배포 주의**: common.css 갱신 시 재방문자 캐시로 신규 공유 규칙이 안 먹을 수 있음 → 배포 `common.css?v=<hash>`/캐시헤더 무효화 필요(publishing/owner).

## 2026-06-16 (DS1b + DS2) — index 히어로 KPI/typeahead + Playwright 회귀 하니스

owner "둘 다 진행" 지시로 DESIGN-V2 P2 슬라이스 + DS2를 함께 착수.

- **DS1b — index 히어로 KPI 스트립 + 회사 typeahead** (DESIGN-V2 P2): `index.html` 상단에 KPI 4카드(**업계 총 기말 CSM 163조 · K-ICS 지급여력비율 중위값 193% · 수록 39社 · 기준 2026.1Q**) — 로드된 데이터에서 산출(`updateKpis`/`totalClosingCsmEok`=wfRowsRaw 항목6 최신 합, `_median`=GROUPED ratio). degrade-safe 진입 애니(`@keyframes riseIn` + reduced-motion 무력화). 회사 typeahead(input+datalist 39사 → IFRS17.html?company= 점프). 토큰 사용, 팔레트/△ 유지, 모바일 2열. 검증: KPI 채움·datalist 39·콘솔0.
- **DS2 — Playwright 회귀 하니스**(`webapp-testing` skill): venv에 playwright+chromium 설치(번들 Chromium 이 머신 구동 OK = Edge/Chrome `--dump-dom` 0바이트 우회). `tests/regression_dashboards.py`(+README) — `with_server.py` 서버 자동관리(좀비0), 데스크탑 뷰포트로 윈도잉까지 assert. **22 assert GREEN**: index(KPI·typeahead·트리맵) / K-ICS(드롭다운≥40·**KB 2026.1Q=185.87**) / IFRS17(as-of·shock↑↓·△·연도[2023,2024,2025,2026.1Q]·분기 last5·미제공사·각 페이지 콘솔0). 캔버스 텍스트(도넛 100%+)는 visual-only 갭으로 문서화.

## 2026-06-16 (DS1) — frontend-design skill 도입: 디자인 시스템 + common.css 추출 (inbox 20260616T0036Z) + KB 렌더 버그

**frontend-design 스킬**로 designer 프롬프트 TBD(디자인 시스템/common.css/A11y/차트 규약)를 정식화. 무파괴(extraction, not redesign) — common.css 값 = 기존 렌더값 1:1. 정찰 Workflow(4 병렬 read-only)로 3파일 토큰 인벤토리 + KB 버그 위치 선행 파악.

- **신규 [`common.css`](../../common.css)**: `:root` 토큰(surface/ink·brand·금융 status·type·spacing 4px·radius·misc) + 공통 chrome(body/header/.brand/.tabs/.tab/.container/.select/.panel h2·p/table base/.num·.small-muted·.muted) + A11y(`:focus-visible`·`prefers-reduced-motion`). 22 규칙.
- **3 HTML 배선**: `<link href="common.css">`를 inline `<style>` **앞**에 추가 + 각 inline에서 중복 chrome/토큰 제거. 페이지 고유(.panel/.controls 여백·`*{box-sizing}`·차트/컴포넌트 클래스·@media)는 유지. index `.tab` cursor:pointer는 common으로 흡수.
- **`*{box-sizing}` 미추출**: 3파일 모두 보유하나 hoist 시 레이아웃 시프트 위험 → 페이지 inline 유지(보수적).
- **프롬프트 §5 정식화**: `docs/agents/claude-agent-designer.md` skeleton→정식(토큰표·extraction contract·A11y 갭·차트 규약 legend밀도/donut stack/모바일 scope·확정결정 4개 잠금). status 라인·assets/ 경로 참조 정정.
- **KB 2026.1Q 렌더 버그 수정** (parser inbox 20260616T0050Z): 원인=분기축 아님, **항목명 라벨 변형 정확매칭**. `K-ICS.html` line 491이 긴 형 `'다. 지급여력비율 : 가 ÷ 나 × 100'`만 매칭 → 2026.1Q 짧은 형 `'지급여력비율'` 쓰는 ~15사 누락(undefined→null). 두 변형 OR 매칭으로 수정. 데이터 정상(파서 책임 아님).
- **검증(무회귀, preview 라이브)**: 3페이지 reload — common.css 200·콘솔 0·computed style 일치(데스크탑 베이스=common, 모바일 @media override 동작)·index treemap 39행. 확정결정 4개 유지(삼성생명 senTable △/↑/정수). KB 분기차트 2026.1Q=185.87% 표시 확인.
- **DS2(webapp-testing/Playwright)**: 미구현, 가부 회신 — flaky한 건 Edge headless(0바이트)지 preview 아님(이번 세션 정상). Playwright는 28건 회귀 자동화·서버 라이프사이클로 가치 有 → 스모크 spike 후 전용 세션 권장.
- **배포 주의**: common.css는 신규 루트 에셋 → HTML과 함께 배포 필요(publishing handoff).

## 2026-06-16 — owner 라이브 QA 3차 10건 (inbox 20260616T0007Z) — IFRS17.html

전부 표시 레이어만(master·viz JSON 무수정). 검증: node --check + 헬퍼 단위테스트(fmtShock·asOfFromRcept·samo·selectPeriods) + preview 라이브(삼성생명·현대해상·아이엠라이프, 콘솔에러 0).

- **D1 민감도 as-of**: `asOfFromRcept(rcept_no)` 추가(제출월→기준일: 1~4월=직전FY 12-31 등). senCap "기준: FY2024 사업보고서 (2024-12-31)". 긴 공시각주는 표 아래 muted 보존. 데이터 `period`/`as_of` null → parser inbox `20260616T0030Z`로 정식 채움 요청(`senAsOf()`가 as_of 채워지면 우선 사용).
- **D2 fmtShock 보강**: 부호·방향어 없는 선두 "3.27%"(상향충격)→**3.27%↑**, ^▲→↑ ▼→↓. 삼성생명 케이스(bare %) 해결. 검증 "3.27%↑/↓"·"3.40%↑(실손보상 2.62%)".
- **D3 억 정수 반올림**: senTable `fmtNum(,0)`(0||2=2자리 버그) → **`samo()`**(정수+△). △3,765 / 3,298.
- **D4 현대해상 키컬러**: `#FFB81C`(노랑) → **`#F47920`**(주황). 스와치 rgb(244,121,32).
- **D5/D6 분기 미제공사**: `wfHasQuarterly()`(4Q-only=데이터기반 11사: AIG·아이엠라이프·하나생명 등). 분기 모드 → Panel1 waterfall 생략+"분기 공시 미제공" 메시지(D5), Panel2 시계열은 연 fallback(D6).
- **D7 축 윈도잉**: `selectPeriods()` — 시계열(hist)·NB배수(nb): 분기→직전 5분기, 연도→연말(4Q→연표기)+최신부분(2026.1Q). 검증 연도=[2023,2024,2025,2026.1Q], 분기=[2025.1Q..2026.1Q].
- **D8 상각 5년캡**: bucket 'y5_plus(5년 초과)' 제거 + yearly maxY 10→5. amort=[1년이내,1–3년,3–5년].
- **D9 모바일 1시점**: ≤640px → waterfall 최신 1버킷, 시계열 최신 1시점. 0폭 preview에서 hist 1시점 확인.
- **D10 로딩 경감**: boot 9 JSON 직렬 await → **Promise.all 병렬** + "데이터 불러오는 중…" 힌트. (지연 원인=직렬 9 round-trip.)

## 2026-06-14 — owner 라이브 QA 글리치 4건 (inbox 20260614T0712Z)

디자이너-단독 4건 처리, 상류대기 3건 ack. (전체 내역 = inbox 답변 섹션.)

- **(1) K-ICS 드롭다운 누락사** [G3 코리안리/G9 예별]: `K-ICS.html` 데이터로드 `.then`에 `fillMissingCompanies()` — 하드코딩 옵션에 없는 `kics_disclosure.json` 원수사명 전부 append(가나다순). JS 선택로직이 `select.options` 검색이라 옵션 추가만으로 선택됨. 옵션 30→48. 코리안리·예별·AIG손해보험·카카오페이손해·서울보증·교보라이프플래닛 선택 가능 확인. (완전 데이터화는 curated 순서 보존 위해 P2 보류.)
- **(2) 현대해상 키컬러** [G5]: `IFRS17.html` KEY_COLORS `#008A3E`(초록)→**`#FFB81C`**(노란주황, owner값). 밝은색이라 line 32% 보정 자동. 스와치 rgb(255,184,28) 검증.
- **(3a) ΔCSM 헤더** [G4a]: IFRS17 sens 테이블 "ΔCSM(백만)"→**"ΔCSM(억원)"** (라벨만).
- **(3d) 모바일 테이블**: IFRS17 `@media≤640` th/td `4px 6px`→`6px 8px` + `.num{white-space:nowrap;word-break:keep-all}`.
- **상류대기 ack**: (3b) shock 표기 통일·(3c) 흥국 행분리 → parser/ifrs17 `sensitivity_heatmap.json` 단계. (4) 기본자본 소진율 100%+ → publishing tier1 overflow→tier2 데이터 대기(donut >100% 표현 위해).
- 검증: Edge headless dump, JS에러 0.

### 2026-06-14 (후속) — sensitivity 3b/3c 매듭 + 푸본현대 parser handoff
- **(3c) 흥국 행분리 = parser 완료 확인**: `sensitivity_heatmap.json` 흥국생명 6행 정리됨(product line 혼입 제거). designer 표 정상.
- **(3b) shock 표기 = designer display 파싱으로 완료**: parser가 자유텍스트 유지 → IFRS17 `fmtShock()` 추가(top-level helper, sens 렌더 line ~955 적용). `{n}% 증가/상승`→`{n}%↑`, `{n}% 감소/하락`·`(-){n}%`→`{n}%↓`. 복합/비정형 원문보존. 검증: 흥국 3.27%↑/↓·9.16%↑/↓·2.62%↑ /0.26%↑.
- **푸본현대생명보험(KR0083) 오파싱 발견 → parser reparse 요청**: sensitivity_heatmap 엔트리가 "기말 보험계약부채" 잔액표 오추출(shock=금액). inbox `20260614T1140Z__designer__KR0083_FY2024__sensitivity_misparse.md`. (display 레이어로 불가 = 추출단계 정정 필요.)

### 2026-06-15 — inbox 2건: 도넛 실값 병기 + CSM null="—"
- **owner 0435Z(도넛 100%+)**: 정식 발주 = 직전 구현분과 동일. 추가로 owner "실값 병기 권장" 반영 → 툴팁 "100%+ (실제 242.5% · 발행액이 인정한도 초과)". status answered.
- **parser 1300Z(CSM null 렌더)**: 동양생명·NH농협손해 `csm_delta=null`(미공시)이 senTable에 "0"으로 렌더(Number(null)=0 버그) → **null이면 "—"(회색)+title** 처리, pl_impact도 동일. 마스터 무수정(표시레이어). 검증: 동양생명 CSM 전부 "—". status answered.

### 2026-06-14 (후속3) — 기본자본 소진율 "100%+" 표기 (owner 결정 복원)

owner가 **(4) 도넛 100%+ 표기를 복원** 지시. 직전 "구현 취소"(publishing artifact 논거 수용)는 **번복**.
- owner 논거: 분자(신종자본증권 발행액)=KOFIA, 분모(인정한도)=공시 → 독립 소스라 사전 100% cap은 애초 불가능. 계산값 >100%면 그냥 "100%+"로 표기하는 게 정당(현재 raw "242%"가 더 오도, `Math.min`은 원호만 캡할 뿐 중앙 숫자는 raw 노출 중이었음).
- 수정(`K-ICS.html` renderDonut): 중앙 텍스트 `pct>100 ? '100%+' : pct.toFixed(0)+'%'`, 툴팁 사용 `'100%+ (인정한도 초과)'`. 원호 `Math.min(...,100)` 캡은 도넛 360° 한계라 유지. 색(>=100 빨강) 유지.
- publishing artifact 주장과 무충돌: "100%+"는 정확값(242.5%)을 안 박아 artifact 오도도 회피. 파서가 excess 추출해 ≤100% 되면 자동으로 정상 %로 표시됨(분기 없음).
- 검증: canvas 중앙 텍스트는 DOM 미노출 → 코리안리 도넛 렌더+인정>한도(>100% 경로) 확인, 실제 "100%+" 글자는 배포 후 육안.

### 2026-06-14 (후속2) — 민감도 stub 마감 + (4) 도넛 보류 확정
- **parser 푸본현대 수정 확인(resolved)**: `_has_shock_rows` 가드로 푸본현대·KB손해·미래에셋·신한을 `status="partial"`(scenarios=[]) 재분류 — ±shock 행 없는 롤포워드 오태깅. KR0083 thread resolved→`_resolved/` 이동.
- **민감도 stub 사용자친화화**: IFRS17 Panel 6 stub "status=partial / 시나리오 없음"(개발자스러움) → "% 충격 기준 보험위험 민감도표가 없는 보험사입니다."(없는 회사) / "민감도 데이터 미수록 보험사입니다."(엔트리 자체 없음). 검증(Edge dump): 푸본현대·KB손해 깔끔한 stub, "7,095,833" 금액 노출 사라짐.
- **(4) 기본자본 소진율 100%+ 도넛 = 구현 취소(보류 아님)**: publishing 조사 결론(`20260614T1141Z__publishing__...`) — tier1 100%+는 Ⅴ.1 excess 파싱누락 artifact, 파서가 excess 추출하면 정의상 ≤100% → `K-ICS.html` `Math.min(...,100)` 캡이 정답. "XXX%+ 도넛+overflow 툴팁" 미구현. designer 액션아이템에서 제거(publishing 재통지 시 재개). 메시지 answered.

## 2026-06-13 — 트리맵 색 임계 앵커 130/200% + 민감도 권고선 정합 (TREEMAP-SCALE, inbox 🟠4)

권고선 = **130%** (owner 확정 2026-06-13; 기본자본비율은 50%). 사이트 메인 K-ICS 차트들은 모두 "지급여력비율 130% 기준선"을 씀.

- 트리맵 `colorForRatio` K-ICS 피벗 = **130%**(원래 값 유지) + **200% 충분 영역**(200%+ 더 진한 초록, 시각용 앵커). <130%는 빨강(미달 깊이 ∝ 채도). 매끈한 발산 그라데이션 → 권고선 기준 빨강/초록 + 200 캡으로 의미 강화.
- 범례 `#legendThresh` 임계 표기 신설: kics "(빨강 <130% 권고미달 · 초록 ≥130%, 200%+ 진함)", basicCapital "(빨강 <50% · 초록 ≥50%)". 모바일 리스트 막대도 동일(같은 함수).
- **정합 수정**: 내가 2026-06-11 만든 K-ICS 금리민감도 패널의 권고선이 `감독당국 권고 150%`로 박혀 있어 사이트 표준(130%)과 불일치 → **130% 기준선으로 정정**(메인 차트 문구와 통일). (작업 중 treemap을 150%로 잠시 바꿨다가 owner 정정으로 130% 환원.)
- basicCapital 50% 피벗은 미변경.
- 검증(Edge headless dump): 130~135% 회사(IBK연금·롯데·하나)가 초록, <130%는 빨강 경계 확인, legendThresh "130%" 렌더.

## 2026-06-13 — IFRS17 회사 키컬러 적용 (KEYCOLOR-V1, owner hex 확정)

화이트 베이스 유지 + 회사 선택 시 키컬러를 **차트 데이터잉크 + select 액티브에만** (배경·패널보더 무채색 유지 — 절제). owner 2026-06-12 hex 확정분 반영.

- `KEY_COLORS` 맵(표시명 키) + `keyColorOf(coName)` → `{primary, line, soft, fill, isKey}`. 미등록사 = 기본 블루(#0d6efd) fallback. 모듈 스코프 `currentKey`를 `renderCompany`에서 회사별 설정, 각 렌더가 읽음.
- **WCAG 보정**: relative luminance > 0.45(KB 옐로우 등)는 선/축용 `line`을 32% 어둡게 (#FFBC00 → rgb(173,128,0)). 막대 면적엔 원색.
- 적용: Panel1/4 워터폴 total 막대 → primary (증감 초록/빨강 의미색 유지), Panel2 기말선+좌축+그리드 → line/soft, Panel5 연누계선 → line/soft, Panel3 상각막대 → fill(0.6). select 보더+box-shadow 링 + 회사명 옆 키컬러 스와치.
- 확정 팔레트: 삼성#1428A0·한화#F37321·신한#0046FF·KB#FFBC00·NH#00A05E·미래에셋#F58220·DB#0E8C3A·현대해상#008A3E·교보#0B5D52·메리츠#E60012·롯데#DA291C. 그린 4곳은 회사 1곳씩 보는 화면이라 충돌 없음.
- 검증(Edge headless dump): 삼성생명 스와치 rgb(20,40,160)=#1428A0, select 링 네이비, JS에러 0, 패널 렌더 정상. 캔버스 색 자체는 DOM 미노출 — 스와치/링이 같은 currentKey라 차트도 동일 색. (K-ICS 재사용은 공통 js 추출 P2 과제, 이번 패스는 IFRS17만.)
- Report: `artifacts/designer/ifrs17_keycolor_v1_20260613.md`.

## 2026-06-12 — 음수 △ 전면화 + K-ICS 위험액 하위 토글 + P1 퀵윈 + 버블 로그축 (4페이지)

- **음수 △ 표기 (사용자 최우선 지시)**: IFRS17 `fmtNum`·워터폴/PL 축라벨·total 라벨·시작/끝 툴팁, K-ICS `sensFmtDelta`('−'→'△')·forward note Δ·민감도표 `fmtAmt`/`fmtPct`. (K-ICS `formatNumber`/`fmtEokInt`, IFRS17 `samo()`는 기존 적용분.) index는 음수 노출 지표 없음.
- **K-ICS 하위위험 토글**: 17(생명장기)→29~35(1-1~1-7), 19(시장)→36~40(3-1~3-5) 기본 접힘 + 항목명 옆 +/− 버튼(`.subtoggle`). `SUB_ITEM_NUMS` → `RISK_SUB_GROUPS`+`subOpen`(재렌더에도 상태 유지). 36~40은 기존 미표시 데이터 — 신규 노출.
- **P1 퀵윈 (4페이지)**: Pretendard Variable(dynamic subset CDN)+`tabular-nums`, IQ 파비콘(data-URI SVG, 잉크색 중립), meta description/OG, 공통 푸터(출처·기준분기·면책·△ 관례), 이모지 제거(📊/🚧). **팔레트 교체는 보류** — 사용자 피드백("남색이야말로 AI스럽다") 반영, 방향 재논의 중.
- **index 버블 겹침 보정**: X축 linear→**log10**(좌측 군집 해소), 라벨 흰 외곽선(textBorder 2px), labelLayout moveOverlap:shiftY + labelLine, nbCsm>0 필터(log 요건).
- **index 회사 약칭 + 트리맵 꼬리 '기타' 묶음 (사용자 지적)**: `shortName()`(접미사 룰: 화재해상보험→화재, 손해보험→손보, 생명보험→생명, 재보험→삭제 + 영문 약칭 NAME_ABBR ~16건) — 트리맵 셀/모바일 리스트/버블 라벨/버블 리스트 표시 전용 (툴팁·클릭 내비는 원래 이름 = 조회 키 유지). 트리맵 코너 슬리버: 예상 면적 < 2,400px²(≈60×40) 소형사는 그룹당 '기타 N사' 한 칸으로 병합 — 중립색, 호버에 명단+비율, 모바일 리스트는 전체 로스터 유지. Edge headless 검증: 기타 3사(처브·BNP카디프·교보라이프플래닛), 셀명 메리츠화재/코리안리/DB손보 등 약칭 확인.
- **신한EZ손해(KR0051) PAA 표기 (inbox 🔴1)**: IFRS17 P1/4/6 stub → "CSM 분리공시 미제공 (PAA·단기계약 중심)" 전용 문구. 목록 제외 대신 표기 채택(PL 패널 공시 살아있음). `PAA_ONLY` Set (코드+표시명 — renderCompany는 회사코드 키임에 주의). Edge headless 검증. KEY_COLORS 시안은 inbox 답변에 작성, owner hex 확정 대기(→ 06-13 확정·적용).
- **index 제목 위계 정리 (사용자 지적)**: 헤더 힌트 "K-ICS Market Map (Balanced Treemap)" → "보험사 공시 대시보드", 트리맵 패널에 `.section-title` "K-ICS — 지급여력 마켓맵" 신설(버블 패널과 동일 패턴). `<title>`도 "보험사 마켓맵"으로. 기술용어 노출 제거.
- 검증: preview_eval 브리지 반복 행(06-07 screenshot 행과 동일 증상) → **Edge headless `--dump-dom`** 대체. K-ICS(한화손해 quarter): 토글 2·하위행 12 기본숨김·△21. IFRS17(한화손해): △47·차트 DOM 정상. index: 22社 로그축 렌더. 15s budget 내 완주. launch.json 포트 8765→8889(좀비 점유).

## 2026-06-11 — K-ICS 금리 민감도 패널 (kics_rate_sensitivity.json)

New panel between 소진율 donuts and Forward Outlook: **5-point 민감도 곡선** (±50/±100bp × 적용전 점선/적용후 실선, Chart.js) + ±100bp Δ%p KPI 칩 + 적용전후 상세표(가용/요구/비율) + 회사별 기준분기 select. 150% 권고선은 메인 차트 annotation 스타일 재사용. `refreshBottomPanels()`에 합류 (회사 change + URL 파라미터 둘 다).

- Coverage 29/30 (미커버 미래에셋생명 1곳 → placeholder). 적용후 미공시(post_dash)는 적용전 단독 렌더 (삼성생명 케이스 확인).
- Preview 검증: 메리츠 2024.4Q 수치 일치([238.23 … 244.42], −10.01/−3.82%p), 분기 전환, stub, mobile 375px (차트 260px, 표 nowrap+가로스크롤). **Console 0.**
- 거대 인라인 데이터 라인(209-211) 미접촉. 서브에이전트 구현 + 메인 세션 nit 2건 (범례 usePointStyle, 표 nowrap).
- Report: `artifacts/designer/kics_rate_sensitivity_panel_20260611.md`.

## 2026-06-11 — index.html 모바일 CSM 버블 → 리스트 (M2 패턴 미러)

≤640px에서 스캐터 숨기고 `#bubble-list` 표시: 생보/손보 그룹 · **최신 기말 CSM desc** 정렬 · 값=**NB CSM 배수** · 미공시사는 최신 분기 fallback + `25.4Q`/`24.4Q` 칩 · 클릭=IFRS17 cross-nav. 데스크톱 스캐터는 자체 패스(2026.1Q 고정) 그대로 — 리스트는 raw 마스터 별도 패스 (32社, 칩 10곳).

- 칩이 `.li-name` ellipsis에 잘리던 버그 → flex(.li-nm 말줄임 + 칩 고정) 구조로 수정, 이름 칸 36→44% (버블 리스트 스코프만).
- 모바일 `#bubble-meta`를 리스트 기준으로 갱신; matchMedia 전환 리스너(모바일 진입=리스트 갱신, 복귀=스캐터 재렌더+resize, 0×0 init 가드).
- Preview 검증 375px+desktop 전환, **Console 0.** 플래그: `.bubble-swatch`는 dead CSS.
- Report: `artifacts/designer/mobile_bubble_list_20260611.md`.

## 2026-06-07 — Panel 3 당기순이익 bridge waterfall (PL_breakdown.json)

Replaced Panel 3 (old Chart.js 손보-only 당기순이익 분해 from `net_income_breakdown.json`) with a CSM-style **bridge waterfall** from new root `PL_breakdown.json`, reusing Panel 1's 보험사 + 기준(연도/분기) controls. First cut — owner to refine details.

- 5-bar bridge (exact reconciliation verified, 손보+생보): **보험손익(1) → 투자손익(17) → 영업외손익(21) → (−)법인세(23) → 당기순이익(24)**. 단위 백만원, 축 조원, ECharts (Panel 1 technique).
- Source has **both YTD(`값`) and 당분기(`값_당분기`)** → 분기 mode works now (unlike CSM): 연도=latest `*.4Q` via `값`; 분기=latest Q via `값_당분기`. Shared #wfPeriod drives both panels.
- `PATHS.plx` (root + data/ fallback), `ix.plx` = company→quarter→항목번호→{y,q}. Template canvas→div `#chartPl`; `destroyCharts` wf+pl now ECharts(dispose), amort/nb/hist Chart.js.
- **Company-name mismatch flagged:** PL uses 삼성생명보험/미래에셋생명보험/코리안리재보험/KB라이프생명 (vs dropdown 삼성생명/…/코리안리/케이비라이프생명보험). `plResolve()` fuzzy-matches (substring); 케이비라이프↔KB라이프 still gaps → stub. Publishing to canonicalize names.
- Removed orphaned `ni`(net_income_breakdown) wiring. Pre-existing dead `payload.pl`/`ix.pl` left untouched.
- Verified via ECharts getOption + canvas dims (screenshot tool hung renderer-side): 현대해상 FY2025 (396,111→…→561,106 reconciles), 현대해상 2026.1Q 당분기, 삼성생명→삼성생명보험 resolve, 삼성화재 mobile, 처브라이프 stub. **0 console errors** both breakpoints.
- Report: `artifacts/designer/panel3_pl_bridge_waterfall_20260607.md`.

## 2026-06-07 — Panel 1 windowed CSM waterfall (company × 연도/분기)

Replaced Panel 1's single fixed 2024 year-end waterfall with a **company × period windowed** waterfall, mirroring `K-ICS.html` selector methodology.

- New source: root `CSM_waterfall.json` (long-format: 원수사명/항목번호/항목명/공시분기/값, 23사 × 2023.1Q~2026.1Q, **단위 억원**, YTD/연 누계). Wired as `PATHS.wfx` (root primary + `data/dart/viz/` fallback), indexed `ix.wfx` = company→quarter→항목번호→값.
- **연도 mode (shipped):** trailing 4 buckets (latest period + prior year-ends), expanded to 18 bars — 기초 CSM → 연도별 신계약·이자·가정/경험·상각 → 기말 CSM. Axis in 조원, tooltips in 조+억. Component reconciliation + year-end chain verified.
- **분기 mode (stubbed):** UI present; `WF_QUARTER_READY=false` shows "당분기 데이터 준비 중" because the file is YTD. Flip flag when 당분기 table lands.
- Old stages-based `renderWfEcharts` removed. Company dropdown = union of legacy 28사 + new 23사, so legacy-only insurers still list and Panel 1 stubs gracefully.
- Mobile: ECharts `dataZoom` (inside+slider) on the 18-bar chart, defaults to latest ~2 groups; `@media (max-width:640px)` unchanged, desktop math untouched.
- Verified via Claude Preview at 1280px + 375px (삼성생명 10.7조→13.6조, 현대해상, DB생명, 분기 stub, 라이나 missing-data stub): **0 console errors**.
- Report: `artifacts/designer/panel1_windowed_csm_waterfall_20260607.md`.
- Hand-off to publishing: relocate `CSM_waterfall.json` → `data/dart/viz/`; flip `WF_QUARTER_READY` when per-quarter table ships.

---

## Archive (pre-2026-06)

- 2026-05-31 — Designer stage created (split from publishing): new prompt `claude-agent-designer.md`; TODO/changelog seeded from root TODO items (MOB-KICS / MOB-IFRS17 / VIS-DONUT / VIS-CHARTLEGEND / M3 / Panel 7 / INDEX-BUBBLE-V2 / F17 Tier2); done archive imported (M1·M2·treemap cleanup·panel pruning·F6·F17 P3·single-source·dead CDN·console·INDEX-C12·KICS-HTML-SUB·F1).
- 2026-05-30 — Panel 3 clean 4-bar swap (data from publishing F17-T1): raw 12-row bar dump → 4-bar 당기순이익 분해 (보험손익·투자손익·영업외 → 당기순이익) + 보종별 caption. Source `net_income_breakdown.json` (Tier1 10/10 손보). 생보 graceful stub, 콘솔 0.
- 2026-05-28 — IFRS17 패널 정리 + F6 yearly amort Panel 2: F6 desktop 10y / mobile 5y (`matchMedia`); coarse → 4-bucket. Panel 5 KPI 카드 + Panel 6 BS 스냅샷 제거(`docs/archived_metrics.md` archive), 패널 1–6 재번호. Generators kept. → follow-up Panel 7.
- 2026-05-28 — index treemap text cleanup + mobile list sort: "기준 XXX" meta line 제거(`.meta` CSS/JS), size-aware labels(name ≥46×60px, ratio ≥26×44px). 모바일 리스트 정렬 ratio desc → 지급여력기준금액 desc (삼성생명 top, 라이나 9th). Preview 검증, 콘솔 0.
- 2026-05-28 — M2 mobile responsive (treemap → vertical list): index.html ≤640px swaps treemap for `#map-list` + `renderList(sector)` mirroring `render()` (same data/color/toggle/click-through). 생명/손해 그룹, ratio desc. Preview 375px 검증, 콘솔 0.
- 2026-05-28 — M1 mobile responsive foundation (4 pages): added `@media (max-width:640px)` to all 4 (zero queries existed before). Header/tabs scroll, panel/chart heights ↓, table overflow-x, map 76vh→58vh. ≤640px scoped → desktop unaffected. Preview 375/1280 검증.
- 2026-05-28 — HTML single-source refactor (P1 + P4): root `K-ICS.html` vs `templates/K-ICS.html` drift(line 171 forward blob) → root sole copy, `git rm templates/{index,K-ICS,IFRS17,공시보고서}.html`. P4: index.html dropped unused `xlsx.full.min.js` CDN (~900KB, 817→816 lines). Preview now `python -m http.server 8000` from root. Deferred: data-JSON dup (P2), shared CSS/nav (P3), K-ICS inline data → external (P5).

Pre-2026-05-28 HTML/viz design entries are in the compressed historical archive of root `docs/claude-changelog.md` ("## Historical archive (compressed)"): IFRS17.html 6-panel dashboard (initial) / K-ICS.html Phase 4 (자본성증권 도넛 + Forward Outlook dual-axis) / index.html treemap (initial Phase 3) / K-ICS sub-items + transition toggle.
