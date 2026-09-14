# Insurequant Designer TODO (Stage 5)

> Last updated: 2026-09-14 · Stage 5/5 — designer
> Prompt: docs/agents/claude-agent-designer.md (§5 design system formalized 2026-06-16) · Changelog: docs/changelog_designer.md

Session start: read this file + `claude-agent-designer.md` + the page(s) in scope (root HTML files). Publishing ([`TODO_publishing.md`](TODO_publishing.md)) owns master JSONs; designer only reads them and decides how they render. English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

Stage 5 = HTML structure / styling / responsive breakpoints / A11y / chart layout. Desktop pages are in production; KEYCOLOR-V1 K-ICS cancelled by owner (IFRS17 구현 불만족). Mobile scope confirmed; M1 foundation done; full mobile pass open.

**Recent (2026-09-14, 손보 손해율 24사 — owner 발주(직접 지시, inbox 티켓 아님), 커밋만·라이브 미배포):**
- **publishing 계약(`data_scope`/`ratio_caveat`)은 이 라운드 세션 시작 시점엔 `jp/jesr_detail.json`·
  `jesr_esr.json` 에 아직 없었다(같은 라운드 병렬 작업) — **스크래치패드 fixture**로 개발
  (`build_fixture.py`, 기존 10사 `data_scope:"full"` + 신규 24사 `ratio_only`, 그중 4사에
  `ratio_caveat` 코드별 1건씩). 실 마스터는 무수정.
- **1) `ratio_only` 회사: 빈 패널 대신 "왜 없는지" 한 줄.** `jesr_app.js`에 `isRatioOnly()`/
  `renderScopeNote()` 신설 — `jesr.html`/`jgaap.html`/`disclosure.html` 3페이지 공통 `#scopeNoteWrap`
  섹션(페이지별 문구, "決算" 탭으로 링크)을 추가하고, 資本層 없는 회사에 쓰던 기존 `noticePanelWrap`
  (規制様式 곧 온다는 문구)은 ratio_only 일 땐 끄고 이걸로 대체 — 안내 문구가 부정확해지는 걸 막음.
  `secCapitalWrap`/`secSensWrap`/`secProfitWrap`(損益の内訳, items 없음)은 패널째 숨김.
  `jgaapCards`(決算 상단 KPI 4장)는 items 없어도 合算率 카드 1장 + 안내문으로 대체(완전 공란 방지).
  `secBsWrap`/`secReservesWrap`/`secReinsWrap`/`secAxesWrap`/`by_line`/`core_history`는 기존
  self-hide 로직이 빈 데이터에서 원래도 잘 숨었다(추가수정 불필요, 확인만). `secProfitabilityWrap`
  (収益性指標: 損害率·事業費率·合算率 카드+5개년 SVG 추이)은 그대로 렌더 — ratio_only 의 유일한
  실데이터 패널.
- **2) 24사 진입점: `jp/index.html`에 "損害率一覧（損保）" 섹션 신설.** 기존 ESRランキング의
  `.map-list`/`.li-row`/FOLD(top5+もっと見る) 패턴을 그대로 재사용(새 UI 언어 안 만듦) — 단
  데이터 소스는 `jesr_esr.json`이 아니라 `jesr_detail.json`(publishing이 이미 만들어 둔
  `loadDetailMap()` fetch에 편승, `buildLossRatioData()` 신설). sector=nonlife 이고 合算率이
  있는 회사는 `data_scope` 무관(既存 full 5사 + 신규 ratio_only 24사 = 29사) 전부 포함, 合算率
  오름차순(낮을수록 위 = 収支黒字). 행 클릭/Enter/Space → `jgaap.html?company=<id>`(収益性指標
  패널로 직행). 이걸로 census `not_yet`라 ESRランキング에 안 뜨는 24사도 처음으로 도달 가능해짐.
  실측: fixture 34사 중 29사가 이 리스트에 집계, 4개사(トーア再保険/ソニー損害保険/レスキュー
  損害保険/MS&AD HD) 전원 노출, 첫 행 클릭·Enter 키보드 둘 다 `jgaap.html?company=` 로 정상 이동.
- **3) caveat 4종 배지 — 별도 열 아니라 값 옆 표식(owner 지시).** `CAVEAT_META`(jesr_app.js·
  index.html 양쪽에 §5.2 관례대로 복사)로 4코드를 성격별 **3그룹**으로 나눔: 算式差
  (`lae_excluded`/`ei_basis`, 머리글자 Δ·실선 앰버 테두리) / 画像判読精度(`ocr_read`, 머리글자
  OCR·파선 회색 테두리) / 重複計上(`simple_sum`, 머리글자 Σ·이중선 보라 테두리) — 색만으로
  구분하지 않게 테두리 모양+머리글자+라벨 문구를 코드마다 다르게(a11y-audit 스킬 §3-4 절차대로
  `a11y_contrast_check.py` 로 3쌍 전부 contrast 실측, AA 6.37~9.43:1 전부 통과; 3색 파스텔 간
  delta-RGB 는 16.5~51 로 완전 안전선(60) 미만이지만 텍스트·테두리 모양이 이미 다르므로 스킬
  가이드대로 severity 낮음으로 판단·완화 없이 진행). `손해율一覧` 리스트 행 + `jgaap.html`
  `収益性指標` 合算率 카드 + 상단 KPI 合算率 카드, 총 3곳에 동일 배지, title 속성에
  `ratio_caveat.text` 전문.
- **함정 1건 발견·즉시 수정(모바일)**: 손해율一覧 배지가 붙은 행에서 `.li-name`이 badge와
  회사명을 한 줄에 욱여넣어 375px 에서 `.li-nm`이 min-width 바닥(5.5em≈71.5px)까지 눌려
  회사명이 잘렸다(TODO 이력의 "칩이 회사명을 밀어낸다"와 동일 패턴, 실측으로 발견). `#lossRatioList`
  스코프로 한정해 모바일에서만 배지를 이름 아래 줄로 줄바꿈(`flex-wrap:wrap`+배지
  `flex:0 0 100%`) — 기존 ESRランキング chip 튜닝은 무수정. 재측정: 이름 폭 71.5px → 136.8px 회복.
- **검증**: `node --check`로 `jesr_app.js` + `index.html`/`jgaap.html` 인라인 스크립트 추출본
  구문 확인. html.parser 로 4페이지 태그균형(EOF 시점 미종료 태그 0) 확인, BOM 0. 로컬
  `http.server`(스크래치패드 사본, 포트 8931) + Playwright(`/opt/pw-browsers/chromium-1194`)로
  데스크톱 1280px·모바일 375px 둘 다 실측 — `document.body.scrollWidth<=innerWidth`(가로스크롤
  0, 양쪽 뷰포트), `pageerror` 콘솔 0(외부 CDN `ERR_CONNECTION_RESET`만, 개발망 차단 기존 패턴),
  ratio_only(caveat 有/無 둘 다)·full 회사(`au_nonlife`) 상세 3페이지 전부 DOM 직접 조회로
  hidden 속성·텍스트 확인(스크린샷만으로 판단 안 함), 다크모드(`prefers-color-scheme:dark`)에서
  배지 배경/글자색 유지 확인(기존 `.repro-badge`/`.prelim-badge`와 동일하게 테마 비의존 고정색 —
  기존 컨벤션).
- **손대지 않음(소유권 경계)**: `jp/jesr_detail.json`·`jp/jesr_esr.json`·`J-ESR/`·`scripts/`·
  `TODO_jp.md`·census·한국 자산(`index.html`·`K-ICS.html`·`IFRS17.html`·`공시보고서.html`) 전부
  무수정. `git commit`/`push` 안 함(오케스트레이터/publishing 병합 대기).
- **모델·소요**: Claude Sonnet 5, 단일 세션 약 1.5시간(탐색+구현+fixture+Playwright 검증 포함).

**Recent (2026-09-12c, GA4 내부 트래픽 플래그 — owner 발주 `inbox/designer/20260912T0830Z`, 커밋만·라이브 미배포):**
- **gtag 스니펫이 있는 5 페이지(`index.html`·`K-ICS.html`·`IFRS17.html`·`공시보고서.html`·`privacy.html`)
  전부에서 인라인 `gtag('config', 'G-F8NSCQZBZK');` 를 브라우저 플래그 버전으로 교체.**
  `?iq_internal=1` 접속 시 `localStorage.iq_internal='1'` 저장 → 이후 파라미터 없이 재접속해도
  `gtag('config', ..., {traffic_type:'internal'})` 로 계속 전송, `?iq_internal=0` 으로 해제.
  owner 가 GA4 Admin > Data filters > Internal Traffic 을 Active 로 켜야 실제 보고서에서 빠진다
  (그 활성화는 owner 몫, 이 라운드는 코드만). CSP meta·`<script async src>` 줄은 무수정.
  `jp/index.html` 은 대상 아님(다른 designer 세션이 동시 작업 중이라 미접근).
  `privacy.html` GA 문단에 "운영자 본인의 확인 접속은 내부 트래픽으로 분류해 통계에서
  제외합니다." 한 줄 추가.
- **함정 1건 발견·수정: `index.html` 만 파일 전체가 CRLF.** 최초 치환 스크립트가 LF 기준이라
  이 파일만 매치 실패했고, 이어서 임시로 쓴 `sed -i` 가 CRLF 전체를 LF 로 뭉개버렸다(git diff
  로 전수 확인해 발견) — Python 으로 전체 라인을 다시 `\r\n` 복원, `git diff` 로 5줄 삭제+13줄
  추가만 남는지 재확인. 5 파일 전부 BOM 없음 재확인.
- **검증**: 로컬 `http.server`(포트 8901) + Claude Browser 로 `index.html` 3-way 실측 —
  `?iq_internal=1` → `localStorage`='1'·`dataLayer` config 인자에 `traffic_type:'internal'`,
  파라미터 없는 재접속 → 유지, `?iq_internal=0` → `localStorage` null·`cfg={}` 로 해제.
  `K-ICS.html` 도 동일 스니펫 스팟체크로 재확인. `pytest tests/test_deploy_assets.py` 11 passed.
- **잔여**: 커밋만 하고 push 는 owner 승인 후(publishing 소관). GA4 Admin 쪽 필터 활성화는
  owner 본인 조치.

**Recent (2026-09-12, J-ESR 킥오프 2차 — owner 발주 `inbox/designer/20260912T0446Z`, 초안 draft 완료·라이브 미배포):**
- **`jp/index.html` 신규 — 일본 ESR 대시보드 초안(일본어 UI).** 헤더(언어전환)+공표상황 카드3+
  ESR랭킹 가로막대(15사, 색=업태·빗금=연결·速報배지·▲목표마커)+커버리지 도넛+一覧表(7열)+푸터.
  `../common.css` 재사용, 데이터는 `fetch('jesr_esr.json')`(publishing 산출, 읽기전용).
  fixture 불필요 — 착수 시점에 이미 진짜 파일(79사 census·15사값) 도착.
- **실데이터에서 스키마 예시에 없던 오염 2건 발견해 화면단에서 방어**: ① `notes` 필드가
  한국어 내부 검증메모라 비노출 처리 ② `doc_type` 3건(au損害保険 등)에 한글 단어 혼입
  → `jaOnly()`(정규식 한글 토큰 제거, 원본 JSON 불변)로 표시 직전 정화, 전체 렌더 텍스트
  한글 잔여 0건 확인. `basis`≠"J-ICS"(SOMPO만 VaR99.5) 케이스는 차트 캡션+表 표식으로 고지.
- **버그 2건 발견 즉시 수정**: 도넛 인접 슬라이스 라벨 말줄임("公表済...") → 온차트 라벨
  끄고 범례에 건수 병기 / 모바일 375px 헤더 2줄 줄바꿈 → 루트 기존 관례(`.hint{display:none}`
  at ≤640px) 적용.
- **검증**: Claude Browser(1280·375px, 가로스크롤 0, aria-label 데이터기반 확인) + Playwright
  실네트워크 재검증(진짜 배포 파일 그대로, 콘솔 에러 0, 스크린샷 2장 `artifacts/designer/
  jesr_jp_draft_{desktop,mobile}_20260912.png`) + `a11y_contrast_check.py` 실측(업태3색·도넛3색
  전부 delta-RGB 103+, 速報배지 흰글자 2.15:1 FAIL→진한글자 7.18:1 로 교체) + html.parser
  태그균형 0오류·BOM없음·ECharts/Pretendard integrity 루트와 byte-diff 0.
- **owner 판단거리 5건**(備考 공개비고 필요 여부·doc_type 오염 근본수정·noindex 해제 시점·GA
  포함 여부·루트 삽입 조각 3종 실반영)을 티켓 답변에 정리. 루트 `index.html`/`common.css` 등
  4개 배포 페이지는 이번 라운드 무수정(코드 조각만 답변에 제공). 상세는
  `inbox/designer/20260912T0446Z__owner__JP_MULTI__jesr_jp_page_draft.md` 답변, changelog 2026-09-12.

**Recent (2026-09-11b, 이용안내 — owner 지시, 커밋·배포 대기):**
- **`privacy.html` 에 "이용안내" 절을 추가했다(새 HTML 파일 없음, owner 지시 1).** `<h1 id="terms">`
  아래 h2 5개(무엇인가 / 이렇게 쓰셔도 됩니다 / 이것만은 피해주세요 / 데이터 출처 / 운영자·문의·준거법).
  보고서 `artifacts/legal/ip_protection_report_20260911.md` §6-2 의 9개 조를 owner 지시 3번대로
  압축 — "제N조" 없음, 자유인 이용을 먼저 말하고 금지는 두 가지(통째 크롤링·대량 재배포)만.
  운영자 실명 조상욱 표기(owner OK).
  **검수(2026-09-11c):** 3절 금지 목록이 4개(출처표시 제거·AI 학습 수집 별도 항목)로 늘어 owner 지시
  "딱 두 가지만"과 어긋나 2개로 압축(AI 학습 수집은 크롤링 항목 괄호로 흡수, 출처표시 제거는 2절의
  "출처를 밝히고 인용"에 이미 담겨 삭제). 출처표의 "보험업법 제124조" 인용 삭제(법조문 벽 금지).
  이용안내 글자수 1,117 < 개인정보 절 1,532.
  title·og·description·brand hint 를 "개인정보처리방침 · 이용안내" 로. 신규 CSS 2줄(`h1.section-break`,
  `.policy-table.src-table{min-width:0}` — 2열 출처표가 모바일에서 가로스크롤 나지 않게).
- **푸터 5페이지(4 대시보드 + privacy) 한 문장 + 링크 2개.** "화면·데이터베이스는 저작권법으로 보호되며
  이용 조건은 이용안내를 따릅니다." + "© 2026 InsureQuant · 운영자 조상욱 · 개인정보처리방침 · 이용안내".
- **`download-survey.js` 동의 라벨만 손봄 — 체크박스 개수 1개·필수 여부·에러 문구 불변(owner 지시 3).**
  "위 안내사항과 [이용안내](데이터 이용 조건)를 확인했습니다", 링크는 `privacy.html#terms` 새 탭.
  xlsx 표지 시트에 "이용 조건" 행 + `build_id` 가 manifest 에 있을 때만 "빌드 ID" 행(지문).
- **검증:** `pytest tests/test_deploy_assets.py` 10 passed · 5 HTML html.parser 태그균형 0 오류·BOM 0 ·
  브라우저 1280/375 실측(가로스크롤 0, 출처표 303px < 305px 래퍼, 모달 라벨 링크 렌더, consent 1개).
  콘솔 오류는 외부 CDN(Pretendard·gtag) `ERR_NETWORK_ACCESS_DENIED` 뿐 — 개발 PC 망 차단, 기존.
- **같은 시각 publishing 에이전트가 저장소 쪽 0원 조치(robots.txt AI 크롤러·LICENSE·`.gitignore`·IR xlsx
  11개 `git rm --cached`·manifest license/build_id)를 병행했다** — 내가 먼저 쓴 robots.txt/LICENSE 를
  그쪽이 덮었고 내용이 더 낫길래 그대로 뒀다. `export_public_sheets.py` 의 build_id 블록은 내 것,
  license/terms_url/copyright 키는 그쪽 추가. 상세는 changelog 2026-09-11b.

**Recent (2026-09-13, jp 랭킹 算定基準 — owner 2차 지시로 chip안 폐기·막대 패턴으로 교체, 커밋만·라이브 미배포):**
- **경위: 1차(chip안)를 owner가 "칩이 너무 많다"로 반려.** 실측(HEAD 기준) scope chip 15/15행·
  目標 chip 7행·速報 4행·単体詳細 3행 — 이미 최대 3개/행인데 여기 basis chip을 더하면 4개.
  (25) 라운드 "모바일에서 칩이 회사명을 밀어낸다" 지적과 같은 종류의 문제라 커밋 전에 되돌렸다.
- **최종안: 算定基準은 chip이 아니라 막대(`li-bar`)의 塗りつぶし 패턴.** 색(`colorForRange`의
  초록/黄/赤)은 이미 目標レンジ 의미로 점유돼 있어 색과 **직교하는 채널**을 썼다 —
  自社基準(`internal_model`+`internal_management`, 한 덩어리)은 대각선 ハッチ柄
  (`.li-bar-self{background-image:repeating-linear-gradient(...)}`, `background`(shorthand) 대신
  `backgroundColor`만 인라인 세팅해 CSS class의 패턴이 안 지워지게 함), `未確認`(basis가 null이거나
  알 수 없는 값)은 점선 테두리(`.li-bar-unconfirmed{border:1px dashed}`) — 규제표준은 무지(기존
  그대로). **3단이 아니라 2채널**: 内部モデル vs 内部管理의 세부 구분은 chip을 없앤 대신
  `row.title`/`aria-label`/`bar.title`(호버·스크린리더 텍스트, 전부 갱신)과 상세 페이지로만.
- **칩 감량 결과**: scope chip·目標 chip **전부 폐지**(목표레인지는 이미 트랙 위 밴드로 중복
  표현 중이었어서 손실 없음, scope는 tooltip에 남김). 남은 chip 은 速報·単体詳細 2종뿐인데
  실측상 **서로 배타적**(単体詳細는 HD 지주행에만, 速報는 개별사에만 — 동시발생 0건) —
  **Playwright 실측: 15행 전부 chip ≤1**(desktop·mobile 공통), 목표(desktop ≤2·mobile ≤1)를
  넘겨서 달성. 모바일 회사명 폭도 100.8~136.8px 로 회복(chip 2종 시절 71.5~75.8px 대비 개선).
- **범례 1줄만 추가**(`.chart-legend`에 ハッチ스와치 1개), 기존 5종은 문구 그대로 유지 — 새로
  늘리지 않았다. 각주(`.chart-caveat`)는 새 문구 1문단으로 재작성: "無地=規制ベース(告示74号의
  標準式)／ハッチ柄=自社基準(内部モデル・内部管理)／点線枠=算定基準未確認…自社基準은 규제베이스와
  단순비교 주의…상세는 행에 커서를 올리거나 회사별 상세에서" 취지.
- **상세 페이지(`jesr.html`, `jesr_app.js`)는 1차 라운드 그대로 유지** — chip이 아니라 `metaLine`
  인라인 텍스트 세그먼트(`算定基準: ...`)라 이번 "칩 감량" 지시와 무관, 되돌리지 않았다.
- **검증**: `pytest tests/test_deploy_assets.py` 11 passed. BOM 0, html.parser 태그균형 0 오류,
  `node --check`(추출한 IIFE 스크립트)로 JS 구문 검증 통과. Playwright(1차 라운드와 동일
  `executable_path` 우회, `/opt/pw-browsers/chromium-1194`)로 1200px·375px·다크모드 렌더:
  콘솔 pageerror 0(`ERR_CONNECTION_RESET` 2건은 샌드박스 외부망 차단, 코드와 무관, 기존 패턴).
  15행 전부 `.li-bar` class·chip 개수·`.li-nm` 폭을 DOM에서 직접 측정(스크린샷만으로 판단하지
  않음) — chip ≤1/행, 가로스크롤 0. `regulatory_standard`(au損保·明治安田損保)는 무지 막대,
  `internal_model`/`internal_management`(朝日生命·富国生命·T&D HD 등 7+3사)는 `li-bar-self`
  class 로 ハッチ 렌더 확인. `未確認` 케이스는 실데이터 15사 전원 basis 확정이라 실측 불가 —
  로직 검토(`isUnconfirmedBasis`)로만 확인, 값이 다시 생기면 자동으로 점선 테두리가 뜬다.
- **손대지 않음(소유권 경계)**: `jp/jesr_esr.json`·`jp/jesr_detail.json`·`J-ESR/`·`scripts/`·
  `TODO_jp.md`. `jp/jp.css`는 이번 라운드도 무수정. 커밋·push 는 오케스트레이터 몫.

> 📦 **Status 이력은 `docs/todo_archive_designer.md` 로 이동했다** (2026-09-11, 내용 무수정 — Recent (2026-09-03) 및 그 이전 항목). 세션 시작 시 읽지 않는다; changelog 처럼 특정 과거 결정의 배경이 필요할 때만 연다. **이 Status 는 최신 5개 항목만 유지**하고, 밀려난 항목은 그 파일 헤더 바로 아래에 그대로 잘라 붙인다.

## 🔴 Open — P1

### BS-TACCOUNT — IFRS17.html Panel 1 (was Panel 7) 재무상태표 (formerly BS-DRILLDOWN, renamed 2026-08-14d)
Now a T-account at the **top** of the dashboard (owner's own explicit ask this round — `inbox/designer/20260814T1250Z__owner__IFRS17__bs_taccount_top_panel.md`, answered), not a mockup panel anymore in intent. Data-contract-driven by `섹션`/`레벨` fields on `IFRS17_BS.json` (parser landing separately, `inbox/parser/20260814T1250Z…`) — no item-number branching in the render code.
- [x] **T-account + reposition (2026-08-14d)**: moved above Panel "2) CSM 이동" (was 7, all panels renumbered 1-7). 좌 자산 / 우상단 부채 / 우하단 자본, right-column height ∝ value ratio. Per-zone `+` (`.subtoggle`, reused from the PL panel) toggles a 레벨2 detail list; disabled+`aria-disabled`+"세부 미공시" when a section has zero 레벨2 rows (covers both "parser hasn't landed detail yet" and "company doesn't disclose" with the same code path — no special-casing needed). 준비금 kept structurally separate from 자본 (own side-note block, excluded from the capital total/detail) per owner's explicit double-counting warning.
- [x] `EQ_SECTION_LEVEL_BRIDGE` bridges the *current* pre-migration schema (items 1-7, no 섹션/레벨 columns yet) so the frame renders today; disappears in effect the moment parser's real columns land (row data wins over the bridge automatically, zero HTML changes needed).
- [x] **This time actually deleted** (not hidden) the 08-14b/c dead L2/L3 functions — preserved-uncalled twice already, proven unreusable both times because the schema kept moving under them. History is in the changelog, not in commented-out code.
- [x] Verified 4 companies incl. all 3 of owner's named edge cases (has-detail / listed-no-detail-yet / non-listed-never-has-detail / zero-BS-data). 0 console errors. `pytest tests/test_deploy_assets.py` 10/10.
- [x] **Real-viewport recheck (2026-08-18, resolved after 3 carried-over sessions)**: this session's Browser pane returned a real `window.innerWidth===375` (not the `0` bug from 08-14b/c/d) — confirmed via `resize_window`+JS query: `.bs-t` switches to `flex-direction:column`, detail/sub rows collapse to 1 grid column, `body.scrollWidth` never exceeds `innerWidth` (no horizontal overflow), 0 console errors. Screenshot pixels still unavailable (pane still doesn't composite for actual frame capture), but this is real DOM/computed-style verification, not a skip.
- [x] **Schema landed same session** (owner shrank scope to 13 detail items, not the original ~60 — `inbox/_resolved/20260815T0100Z__parser__MULTI__ifrs17bs_taccount_schema_ready.md`): confirmed compatible with zero HTML changes (contract design worked as intended). Data shape + render-code field matching verified by direct inspection (`fetch(...,{cache:'no-store'})` vs. `renderBsZone`); a true fresh-browser render wasn't achieved that session — local server's HTTP cache kept serving the pre-migration snapshot. **2026-08-18: confirmed live** — 자산/부채/자본 `+` all enable and render real rows for KR0008 (Tier-1), verified via `.click()` + `box.hidden`/`getComputedStyle(...).display` in a clean preview.
- [x] **Partial-detail confusion fixed (2026-08-15, inbox `20260814T1710Z__validation__IFRS17__bs_detail_is_highlight_label_it.md`)**: validation caught that the 레벨2 detail is an intentional "≤15-line highlight" (owner scope, not full closure — `scripts/build_ifrs17_bs.py`), so a section's shown detail routinely undershoots its total (worst case validation found: 신한라이프 자산 세부 17-21조 vs 59조+ total) with zero on-screen explanation — reads as broken. Fixed by computing a "기타·미표시" residual row client-side (`total − Σshown`, no master change) plus a short caption clause. Re-verified on the exact worst-case company (신한라이프/KR0094): shown-detail + residual now ties out to the total within rounding.
- [x] **🔴 `+` toggle dead-on-arrival bug fixed (2026-08-18, owner live-QA `inbox/designer/20260818T0026Z` D-3)**: `.bs-l2-rows{display:flex}` was beating the UA `[hidden]{display:none}` default in cascade, so `box.hidden` toggling never changed the rendered layout — the button looked completely dead (aria-expanded flipped, screen didn't). Fixed with one CSS rule, `.bs-l2-rows[hidden]{display:none}`. Audited all 4 HTML pages for the same display+hidden collision pattern — none found elsewhere (K-ICS/index/공시보고서 don't use the `hidden` attribute at all; the PL 재보험 subrow toggle uses `style.display`, unaffected).
- [x] **법정준비금 재배치 (2026-08-18, D-4)**: moved from a standalone `#bsReserveNote` block (deleted, along with its render code + CSS) into the 자본 zone's own detail list, as indented sub-rows anchored right after the "이익잉여금" row (name-matched, not item-number — new `renderReserveSubrows()`). Still excluded from the shown/residual sum (rendered via a separate pass, owner's double-counting warning preserved) — verified on KR0008 the residual stayed a small △81억 (not off by the ~6.95조 it would be if reserves had leaked into the sum). Companies without an 이익잉여금 row (non-listed) get the sub-rows inserted before the residual row instead.
- [x] **버그 수정(같은 대화, owner 즉시 재확인): 연도모드 "직전 3년" 위반** — 재사용한 `selectPeriods()`가 무상한(전체 4Q) 반환이라 BS가 2021년까지 있는 회사(메리츠화재·현대해상·KB손보·코리안리 등)에서 6열까지 붙었음. BS 전용 `eqYearPeriods()`(최신+직전3개년말 하드캡, `wfYearBuckets()`와 동일 패턴) 신설로 교체, 공유 함수는 미변경(CSM/PL/NB 마스터는 실측상 전부 2023년 시작이라 이 결함이 잠재적일 뿐 미발현 — 확인만 하고 안 건드림). 6개사 전부 재검증 완료.
- [x] **시계열 원천 테이블 신설 (2026-08-19, owner 채팅 발주)**: T자 밑에 다분기(`#wfPeriod` 연동, `selectPeriods` 재사용) 표 추가 — 분기=직전5분기 / 연도=최신+직전3개년말, 분기 미제공사는 CSM 패널과 동일 문구의 stub. 자산/부채/자본[+] → 세부[+] → 자본 세부의 "이익잉여금"은 자체 중첩 [+]로 법정준비금(이제 4항목 — `보증준비금 기적립액` 신규, 생보 16사만) 한 겹 더. 항목은 선택 기간 전체의 이름 유니온(`eqUnionNames`)이라 항목번호 하드코딩 없음. 상위 토글 접을 때 중첩 하위 토글도 재귀 리셋(`collapseGroup`). `renderBsTable`/`buildBsTableDom`/`eqHasQuarterly`/`eqUnionNames`/`eqValByName` 신설. 브라우저 실측 다수(연도/분기 헤더 owner 예시와 정확 일치, 생보/손보 준비금 항목수 차이 확인, stub 전환, zero-BS-data 회사 무충돌, 375px 표 자체 스크롤). `pytest` 10/10.
- [x] **(종결 2026-08-20)** Deploy 차단 해소 — 게이트 `RED=0 YELLOW=276 exit=0`, main 배포 실제로 진행됨(`a0979b9`, 오늘만 3회). 원문: (unrelated to this rebuild, standing condition). No push attempted.

### DIVIDEND-PAGE — 공시보고서.html 배당현황 (built 2026-08-15)
Owner's C-4 chain, designer leg (`inbox/_resolved/20260814T2230Z__parser__MULTI__dividend_json_ready_for_gongsi_page.md`). Fills the page's long-standing "준비 중" shell — no new tab/page, per owner's explicit constraint.
- [x] Company selector (24-company registry, drawn from `dividend.json` itself, not the 39-company kics universe — the 15 non-listed companies structurally never have this DART disclosure, so they're left out of the picker rather than showing a permanent empty stub) + KPI strip + company-level table (항목 1-7) + per-종류주 mini-tables (항목 8-10, auto-detected classes, no hardcoded company list).
- [x] `0` vs `"정보없음"` kept strictly separate everywhere (owner's own repeatedly-flagged trap) — verified on real data, not just written and assumed.
- [x] `claude-agent-designer.md` §1 doc-table gap fixed (my half of `test_docs_agree_with_what_pages_fetch`).
- [x] **(종결 2026-08-20)** `dividend.json`은 **git 추적 중**이고(`git ls-files` 확인) 2026.2Q 24사까지 배포됐다. 'untracked·deploy far off' 전제 stale. 원문:, `claude-agent-publishing.md` doesn't mention it yet, and `validate_data_contract.py` doesn't wire this master into its gate at all — all three already ticketed in `inbox/publishing/20260814T2230Z` (P-1/P-2/P-4), not this stage's files to touch.
- [x] **Period selector added (2026-08-18, owner live-QA `inbox/_resolved/20260818T0026Z` D-5)**: the "shows all 14 raw quarters" gap above is closed — added a K-ICS.html-style 기간(분기/연도) toggle. Quarter mode = last 5 quarters, year mode = latest + prior 3 fiscal year-ends (partial current year labeled "…누계", e.g. "2026.2Q누계"), both derived from `dividend.json`'s own data (`GLOBAL_QUARTERS`), not hardcoded. Window is **global** (same header columns regardless of which company is selected), not per-company — deliberate, so a company's missing quarter shows as a 정보없음 cell under a stable header rather than shifting the whole column set. Also removed 항목1 주당액면가액 (owner: "필요없으니까 빼고"). KPI strip decision: stays anchored to "latest 4Q" regardless of the new period selector (a multi-quarter window doesn't map to a single KPI snapshot) — documented in `#divKpiCap`'s caption per owner's explicit ask to decide-and-state. Verified live on KR0008: quarter headers 2025.2Q~2026.2Q, year headers 2023/2024/2025/2026.2Q누계, `0`-vs-정보없음 distinction intact (현금배당금총액 real 0 for 3 quarters vs 정보없음 for the undisclosed 2026.2Q cell), 0 console errors, 375px no horizontal overflow.
- [x] Real-viewport mobile recheck done for this page too (2026-08-18, same session as BS-TACCOUNT above) — `resize_window`+JS query confirmed `.controls` wraps, period selector visible, no horizontal overflow at 375px.

### KEYCOLOR-V1 — 회사 키컬러 액센트 시스템 ~~(K-ICS 취소, IFRS17 재검토 대기)~~
IFRS17 적용 완료 2026-06-13. K-ICS 적용은 **owner가 2026-06-17 취소** (IFRS17 구현 불만족). IFRS17 키컬러도 재검토 필요 — owner 피드백 대기.
- [x] IFRS17 적용 완료 (2026-06-13)
- [~] K-ICS 적용: **owner 취소 (2026-06-17)**
- [ ] (보류) 전체 키컬러 방향 재검토 — owner 피드백 후

### DESIGN-V2 — de-AI 디자인 오버홀 (proposal delivered 2026-06-11, awaiting owner sign-off)
Owner complaint: site looks AI-generated. Audit done (4 pages + barabom.me reference — actual findings: Spoqa Han Sans Neo webfont + restrained neutrals + 0.1-0.2s micro transitions, NOT heavy animation). Phases:
- [~] **P1 quick wins** — **3/4 이미 배포돼 있다 (2026-08-30 `origin/main` 실측)**: Pretendard 4페이지+common.css 전부 적용 · `tabular-nums` 적용 · `rel="icon"` 4페이지 전부 존재. **남은 것은 둘뿐** — 부트스트랩 잔재 색(`#0d6efd`·`#f8f9fa`)이 4페이지+common.css 에 아직 있고, `og:image` 는 0건이다. 종전 문구 —: Pretendard Variable + `font-variant-numeric:tabular-nums` 전역 / 탈부트스트랩 팔레트(#0d6efd·#f8f9fa 교체, 잉크+페이퍼+딥블루 1액센트) / favicon(IQ 모노그램)+OG+meta description / footer(출처·기준분기·면책) / 이모지 placeholder 제거 / radius 12→6px / Chart.js·ECharts 색 CSS 변수화 (기본 teal/pink 퇴출). [부분 착수: P1-QUICKWIN 일부 done 2026-06-12, 팔레트 교체는 보류]
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
- [ ] Panel 7 (BS-DRILLDOWN, added 2026-08-14) has `@media(max-width:640px)` CSS following the same pattern as Panels 1-6 but hasn't had a real-viewport pixel check — fold into this pass' verification
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
- [x] **🚫 폐기 — 재착수 금지 (2026-08-20 확인)**. 4축 V2는 owner가 폐기했고 **3축이 이미 라이브 완결**이다: `index.html` L165 *"X: 신계약 CSM 규모 · Y: NB CSM 배수 · 크기: 기말 CSM 잔액"*. 이 줄을 열린 항목으로 두면 다음 세션이 완결된 기능을 다시 만든다. 원문:
- [ ] Mobile rendering: **3축** 버블맵 → simplified (bar 또는 list with sort options) — 위 4축 폐기에 맞춰 축 표기 정정(2026-08-20)
- [ ] Click → cross-nav (existing pattern)

### F17 Panel 3 — Tier2 LOB drill-down rendering (when publishing ships Tier2 JSON)
Publishing currently has Tier1 4-bar in production. Tier2 (LOB 장기/자동차/일반 stacked) waits on parser F17 decision + publishing assembly.
- [ ] Stacked bar / waterfall design (손보만, LOB visible)
- [ ] 생보 alt-rendering (장기 전사 fallback)
- [ ] Caption variant per-company taxonomy (장기/자동차/일반 vs 보장성/물보험/저축성)

## ✅ Done (archive)
완결 항목 25+개(2026-05-28~06-14) — M1 모바일 foundation, KEYCOLOR/TREEMAP-SCALE, △(세모) 전면화, 생명장기·시장위험액 토글, PL/CSM 워터폴 패널, HTML single-source refactor, dead-CDN 제거 등. 상세는 `docs/changelog_designer.md`(당시 `(changelog MM-DD)`로 인덱싱) + git log.


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
- `IFRS17.html` — 7-panel dashboard (1=BS T-account, 2-7=CSM/PL/NB/sensitivity)
- `공시보고서.html` — 배당현황 (per-company dividend disclosure, filled in 2026-08-15; was a static "coming soon" shell before)

**Local preview:** `python -m http.server 8000` from repo root. (preview_eval 반복 행 시 Edge headless `--dump-dom` 대체; 좀비 포트 회피로 현재 8889.)

## Reading order for designer subagent
1. This file (`TODO_designer.md`) — current state (changelog is deferred: [`docs/changelog_designer.md`](docs/changelog_designer.md) is history, open only when you need a past decision's background)
2. [`docs/agents/claude-agent-designer.md`](docs/agents/claude-agent-designer.md)
3. Root HTML page(s) in scope
4. Master JSON schema (publishing's output) for the panel you touch — read-only
5. Root [`TODO.md`](TODO.md) for cross-stage roadmap notes

## Hand-off
- **From publishing**: notification that a master JSON changed (`manual_html_edit` warn) or that a new field needs rendering.
- **To human**: designer never pushes. Hand off to publishing for the commit message + push recommendation.
