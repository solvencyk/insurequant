# PM-2026-09-21 — 배포 HTML 의 JS 가 무검사였다: `IQP is not defined` 로 K-ICS 금리민감도 패널 전멸

> 상태: `closed` (5칸 전부 채움 · 잔여는 UH-26 · UH-27 로 등재)
> 발견 경로: **owner 라이브 QA(눈)** — 게이트·테스트·CI 어느 것도 신호를 내지 않았다
> 관련 inbox: `inbox/validation/20260921T0057Z__owner__ALL__deployed_js_runtime_blind_spot.md`
> (designer 발주 `inbox/designer/20260921T0057Z__owner__ALL_2026.2Q__kics_sens_IQP_referenceerror.md`)
> 관련 커밋: 원인 `2dbc4ca`(2026-09-20 05:55) · 복구 `197d15e`(2026-09-21) · 게이트 신설(이 라운드)

## 0. 사실관계 (blameless)

`2dbc4ca` "design: IFRS17 섹션 네비 통일…" 은 **한 줄을 지웠다**:

```
-    function IQP(){ return (window.IQTheme && IQTheme.chart().primary) || '#0f6e68'; }
```

호출부 두 곳(`renderSensDetail` 의 라인차트 `borderColor:` / `backgroundColor:`)은 그대로
남았다. 그 커밋은 인라인 구현을 `theme.js` 로 올리는 대규모 정리였고, 같이 딸려 있던 한 줄짜리
차트 색상 헬퍼가 함께 지워졌다 — **사람의 부주의가 아니라, 그 종류의 실수를 잡는 기계가 하나도
없었다는 것이 이 사고의 내용이다.** 저장소 전체에서 배포 HTML 의 JS 를 읽는 검사기는 0개였다.

라이브에서 `ReferenceError: IQP is not defined` 가 나면서 `renderSensDetail()` 이 중단됐다.
예외 위치가 **듀레이션 카드 렌더 뒤 · placeholder 숨김 앞**이라, 화면은 "듀레이션 숫자는 보이는데
그 아래에 '보험사를 선택하면…' 안내문이 떠 있는" 어정쩡한 상태가 됐다. 빈 화면이었다면 더 빨리
보였을 것이다. **데이터는 100% 정상이었다** — `kics_rate_sensitivity.json` 798행은 한 바이트도
안 틀렸고, 이 사고에서 고칠 데이터 셀은 0개다. 순수한 렌더링 사망이다.

**영향 범위 (실측, 2026-09-21 validation).** 오케스트레이터 최초 보고는 "39사 중 36사" 였는데
재측정 결과 **기본 화면에서는 39/39 사 전부**다. 예외는 `if (postRatio) { … IQP() … }` 안에서만
터지므로, 그 분기에 **경과조치 적용후 지급여력비율 행이 있는** 버킷만 죽는다(적용전만 있는
버킷은 색상이 리터럴 `'#6c757d'` 이라 살아난다).

| 축 | 실측 |
|---|---|
| 선택 가능한 (회사,분기) 버킷 | **138** |
| 그중 `IQP()` 에 도달 = 패널 사망 | **129** (93.5%) |
| 살아난 버킷 | **9** — 동양생명 2024.4Q · 삼성생명 2024.4Q/2025.2Q/2025.4Q · 신한이지 2025.4Q · 카카오페이손보 2025.4Q · 하나손보 2024.4Q/2025.2Q/2025.4Q (전부 적용전만 보유) |
| **기본 선택(최신 분기)에서 죽은 회사** | **39 / 39** — `qSelect.value = quarters[0]` 이라 첫 화면이 곧 최신 분기다 |

재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_deployed_js.py --git-ref origin/main`
→ `K-ICS.html:1368 IQP` · `K-ICS.html:1369 IQP` · `RED=2`.

노출 기간: 2026-09-20 05:55 배포 ~ 2026-09-21 owner 발견(하루 이상). **이 문서를 쓰는 시점에도
라이브(`origin/main@8ba15d9`)는 깨져 있다** — 복구 커밋 `197d15e` 는 작업 브랜치에만 있고 main
배포가 아직 안 나갔다(UH-27 · publishing 티켓 발주).

---

## 1. 무엇이 통과했나 (어떤 게이트가 왜 못 잡았나)

- 통과 당시 게이트 상태: `prepush_check.py` **전 단계 통과**(data-contract RED=0 · K-ICS 룰게이트
  clear · 도메인 7종 pass · DART raw 0 · 골든 입력지문 pass · inbox 0 · 오프라인 테스트 pass).
  데이터가 실제로 정상이었으므로 **이 게이트들은 전부 옳게 동작했다.**
- **못 잡은 이유 — 검사 축 자체가 없었다.** 배포 HTML 을 읽는 기존 검사기는
  `tests/test_deploy_assets.py` 하나뿐이고, 그것이 보는 것은 ① keep-list(참조 파일이 저장소에
  있나) ② 패널 데이터 인라인 금지 ③ BOM/UTF-16 ④ 삭제된 소스 경로 참조 ⑤ 골든 표 동기화다.
  **`<script>` 블록의 내용은 한 바이트도 파싱하지 않는다.** `validate_live_artifacts` 는
  "화면이 fetch 하는 .json 이 마스터와 맞나" 를 보지 JS 를 보지 않는다.
- 즉 `CLAUDE.md` **불변식 1번("게이트가 검사하는 파일 = 사용자가 보는 파일")을 데이터 축에서는
  집요하게 지켜 왔는데 화면 축에서는 한 번도 지킨 적이 없었다.** 파일은 맞게 보고 있었지만
  그 파일의 **절반(JS)** 을 안 열어 봤다.

> **false-green 의 메커니즘 한 문장:** 이 저장소의 게이트는 전부 "숫자가 맞나" 를 묻는데,
> 이 사고는 **맞는 숫자를 화면에 그리는 코드가 죽은 것**이라 어느 질문에도 걸리지 않았다.

- 기존 유형표와의 관계: `docs/postmortems/README.md` 의 5유형(산술만 검사 / 검사축 누락 /
  presence 만 검사 / 입력결측이 검사무력화 / 적용사 하드코딩) 중 **"검사 축 누락"의 가장 큰 판**
  이다. PM-2026-08-25(게이트가 배포본이 아닌 파일을 검사했다)와 형제지간이지만 방향이 다르다 —
  그때는 *틀린 파일*을 봤고, 이번엔 *맞는 파일의 안 본 부분*이다.

## 2. 어떤 룰이었으면 잡았나 (구체 룰 정의)

| 항목 | 내용 |
|---|---|
| 룰 id | **`DEPLOYED_JS_UNDEFINED_CALL`** (+ 같은 게이트의 `DEPLOYED_JS_SCRIPT_MISSING` · `DEPLOYED_JS_UNSCANNABLE`) |
| 입력 | 배포 4종(`index.html` · `K-ICS.html` · `IFRS17.html` · `공시보고서.html`)이 **실제로 로드하는** 스크립트 전부 = 인라인 `<script>` 블록 + 같은 저장소의 `<script src="*.js">`(`theme.js`·`forms-config.js`·`download-survey.js`·`report-widget.js`). 마스터 JSON 은 입력이 아니다(데이터 축이 아니다). |
| 판정식 | 렉서로 토큰화 → `refs − defined − BROWSER_GLOBALS − CDN_GLOBALS ≠ ∅` → RED.<br>`defined` = 한 페이지의 **모든** 스크립트에서 바인딩되는 이름(function 선언·class·var/let/const·함수/화살표 파라미터·catch 파라미터·메서드 축약·`window.X =`·무선언 전역대입).<br>`refs` = 값으로 읽히는 세 자리 — 호출 `name(`·`new name(` / 객체리터럴 값 `{k: name}` / 인자 `f(name)`·`f(a, name)`. |
| 임계값 | 없음(집합 포함 여부). 수치 tolerance 가 아니라 **존재 판정**이라 임계 조작으로 꺼지지 않는다. |
| severity | **RED · push 차단** (`blocked` 경유 exit 2) |
| 오탐 억제 | **설계 전체가 오탐 억제다 — 양쪽을 일부러 반대 방향으로 틀었다.** ① `defined` 과대추정(스코프를 안 본다 · 구조분해 파라미터를 통째로 바인딩으로 본다) ② `refs` 과소추정(멤버 호출 `a.b()`·옵셔널체이닝·메서드 축약 정의 제외, 자유 식별자 전수 해석 안 함) ③ 렉서가 문자열·템플릿·주석·정규식 리터럴을 제거 → **티켓이 지목한 CSS `var()`/`rgba()`·한국어 산문 노이즈는 토큰에 아예 안 들어온다**(템플릿 `${…}` 안쪽만 재귀 토큰화 — 거기는 진짜 코드다) ④ CDN 전역(`Chart`·`echarts`·`XLSX`·`ChartAnnotation`)은 **그 `<script src>` 가 그 페이지에 실제로 있을 때만** 허용 ⑤ 브라우저 내장 allowlist. |
| 오탐 실측 | **4페이지 · 토큰 73,175 · 참조지점 3,627 에서 RED = 0.** `gtag`/`dataLayer` 는 CDN allowlist 에서 **뺐다** — 그 둘은 인라인 GA 스니펫이 만드는 것이라 allowlist 에 두면 그 스니펫이 지워져도 안 걸린다(실측: 빼도 RED 0). |
| 검출력 실측 | `function NAME(` 선언을 하나씩 지우는 전수 변이 **183건 중 172건(94%) 검출**. 미검출 11건의 사유는 전부 규명됐다 — 9건은 같은 이름이 `download-survey.js`/`theme.js` **IIFE 안에도 정의**돼 있어 과대추정에 흡수(스코프 미해석 = UH-26), 2건은 진짜 무해(`fillMissingCompanies` 는 즉시실행 명명함수식, `plResolve` 는 호출처 0인 죽은 코드). |

**왜 헤드리스 브라우저가 *아니라* 정적 검사인가(판단 근거).** 티켓이 준 두 후보 중 ①(헤드리스)은
게이트의 **차단 축**으로 쓸 수 없다고 판단했다: (a) 배포 페이지가 CDN 4종을 로드하는데 훅은
오프라인에서도 돌아야 한다 → 스텁이 필요하고 스텁은 곧 "진짜 페이지가 아닌 것을 검사"다,
(b) 브라우저가 없는 클론(리눅스 컨테이너·Termux)에서는 SKIP 이 되는데 **SKIP-on-missing 이 바로
이 저장소가 반복해서 데인 형태**다(fail-open), (c) 이 머신에서 헤드리스 반복 실행이 행으로 죽은
전례가 있다. ②(정적)는 0.09초 · 오프라인 · 결정론적이고 이번 사고형태를 정확히 덮는다.
**헤드리스로만 잡히는 부류(TypeError·DOM id 불일치)는 안 잡힌다는 사실을 UH-26 으로 등재했다** —
"둘 다 하면 좋다" 를 "하나만 하고 나머지는 안 적는다" 로 바꾸지 않았다.

## 3. 그 룰이 지금 배선됐나

| | 함수/규칙 | 파일 | scope | exit-code 반영 |
|---|---|---|---|---|
| **push 게이트(훅 §1f)** | `validate_deployed_js.main()` ← `_run_korean_master_gates()` | `scripts/prepush_check.py` **L35 import · L409 호출 · L450 언팩 · L581 `blocked` · L600 `return 2`** | **FULL 전용**(축소되지 않는다 — 아래 근거) | ✅ **RED → exit 2 → push 차단** |
| 게이트 본체 | `check_page()` / `collect()` / `scan_tokens()` | `scripts/validate_deployed_js.py` | 배포 4종 전부 | ✅ 자체 exit 2 |
| 훅 강제점 | `GATE="$ROOT/scripts/prepush_check.py"` | `.githooks/pre-push` **L23** (`core.hooksPath=.githooks` 확인됨) | — | ✅ |
| 배선 매니페스트 | `WIRED["validate_deployed_js"]` | `tests/test_push_gate_wiring.py` | — | ✅ 선언과 호출 불일치 시 테스트 FAIL |
| 변이시험 | `tests/test_deployed_js_gate.py` (24 케이스) | 훅 오프라인 묶음 `prepush_check.py` **L547** | — | ✅ pytest 실패 → `n_test` → 차단 |

**축소(jp-scope)로 빠져나갈 수 없다.** `prepush_check.py` §0 의 `ROOT_FULL_SUFFIXES` 에
`.html`·`.js` 가 들어 있어 루트 HTML/JS 를 건드리는 번들은 **자동으로 전체 게이트**다. 즉
"화면을 고쳤는데 화면 게이트를 건너뛰는" 조합이 구조적으로 안 나온다. 범위 목록은 **안 고쳤다**
(`tests/test_prepush_scope.py` 무수정 통과).

**"배선했다"를 실행으로 확인했다(§5.1 3단 점검).**
① 호출 — `prepush_check.py:409 n_js = deployjs.main([])` (주석 아님, `_run_korean_master_gates()`
본문). ② exit code — `L581 blocked = … or n_js` → `L600 return 2 if blocked else 0`.
③ 훅 — `.githooks/pre-push:23`.
그리고 **실제로 돌려서 봤다**: `origin/main` 의 깨진 `K-ICS.html` 을 스크래치패드 트리에 놓고
같은 호출 경로로 `prepush_check.main()` 을 태우면
`PRE-PUSH VERDICT … 배포 JS 런타임=BLOCK … → BLOCKED`, `exit = 2`.
designer 복구본으로 바꾸면 `배포 JS 런타임=clear … gate-clear`, `exit = 0`.
(프로브: `scratchpad/probe_exitcode_e2e.py` — 저장소 파일은 한 바이트도 안 건드린다.)

**회귀 박제(RED→GREEN).** `tests/test_deployed_js_gate.py::test_the_iqp_incident_is_caught_and_the_fix_clears_it`
가 `K-ICS.html` 을 **메모리에서** 읽어 `function IQP(…)` 한 줄을 지우고 RED(호출부 2줄) 를
확인한 뒤 원본으로 GREEN 복귀를 확인한다. K-ICS.html 은 designer 소관이라 **검증 목적으로도
디스크를 수정하지 않는다.** 동어반복 방지로 killer 변이 6종(allowlist 확대 / 호출을 정의로 계상 /
참조 수집 제거 / 인라인 스크립트 미독해 / 렉서 실패 묵인 / 없는 `<script src>` 묵인)이 전부
케이스를 죽이는 것을 확인했다.

## 4. documented exception

**없음.** 이 사고로 등재한 면제는 0건이고, 게이트도 면제 레지스트리를 갖지 않는다.

- 데이터 면제 등재부(`_LIFE8_ISSUER_INCONSISTENT` · `_TIER2_ISSUER_INCONSISTENT` ·
  `data/_gold/kics_exemption_provenance.json` 등)는 **이 축과 무관**하다 — 고칠 데이터가 0셀이다.
- 이 게이트에서 "면제" 에 해당하는 것은 **allowlist 두 개뿐**이고 둘 다 코드에 열거돼 있다:
  `BROWSER_GLOBALS`(브라우저·ECMAScript 내장) · `CDN_GLOBALS`(URL 조각 → 전역 이름). **후자는
  그 `<script src>` 가 그 페이지에 실제로 있을 때만 적용되므로**, CDN 태그를 지우고 호출을
  남기는 사고는 allowlist 가 있어도 그대로 RED 다. allowlist 를 넓히는 것이 이 게이트를 끄는
  유일한 방법이고, `tests/test_deployed_js_gate.py::test_mutant_a_...` 가 "넓히면 사고를 못
  잡는다" 를 매 push 에 보여준다.
- **면제 추가는 owner 권한**이라는 원칙은 이 게이트에도 그대로 적용된다. 오탐이 나면 allowlist
  를 넓히기 전에 **그것이 정말 전역인지** 원문(로드되는 스크립트)으로 확인할 것.

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 티켓 / 우선순위 |
|---|---|---|
| **UH-26 — 런타임 전용 실패는 여전히 무검사.** 정적 검사는 "이름이 없다" 만 본다. 잡히지 **않는** 것: ① `TypeError: a.b is not a function`(객체는 있는데 메서드가 없다) ② `getElementById('…')` 가 null 인데 그대로 `.style` 접근(엘리먼트 id 개명) ③ 차트 옵션 스키마 오류 ④ fetch 응답 모양이 바뀐 경우 ⑤ **스코프 오류** — IIFE 안에서 정의하고 밖에서 부르는 형태(전수 변이 183건 중 9건이 이 이유로 미검출). 전부 "데이터는 맞는데 화면이 죽는" 같은 부류다. | `inbox/validation/20260921T0630Z__validation__ALL__headless_runtime_smoke_feasibility.md` / **P2**. 선행조건 = CDN 오프라인 대응(SRI 자산 로컬 캐시 or 스텁의 정직한 한계 문서화) + **브라우저 없는 클론에서 SKIP 이 fail-open 이 되지 않게 하는 설계**. 그 설계 없이 배선하면 "안 돌렸다"가 "통과했다"로 읽힌다. |
| **UH-27 — 라이브(`origin/main`) 축은 인쇄만 하고 push 를 막지 않는다.** 이번 사고의 본질은 *이미 배포된 것*이 하루 넘게 깨져 있었고 **아무 기계도 그 말을 안 했다**는 것이다. 게이트는 "내가 밀려는 것" 만 본다. 차단으로 걸면 designer 가 main 에 고칠 때까지 무관한 작업까지 전부 막히므로 일부러 정보로 뒀다 — 그 판단을 조용히 하지 않으려고 `_live_audit()` 이 **매 실행 인쇄**한다(`[라이브 감사 · 비차단] origin/main@… RED=n`). | `inbox/publishing/20260921T0630Z__validation__ALL__live_main_still_broken_deploy_iqp_fix.md` / **P1**(지금 라이브가 깨져 있다). 상시 축으로 승격할지는 owner 판단 — 대안은 배포 직후 1회 `--git-ref origin/main` 을 launch-runbook 에 박는 것. |

**같이 기록해 두는 두 가지(룰로 안 만든 결론).**
- **`gtag`/`dataLayer` 를 CDN allowlist 에 넣지 않았다.** `googletagmanager.com/gtag/js` 는
  `window.gtag` 를 만들지 않는다 — 인라인 GA 스니펫이 만든다. allowlist 에 넣으면 그 스니펫이
  지워져도 안 걸린다. 빼고도 RED 0 임을 실측했다.
- **자유 식별자 전수 해석은 일부러 안 했다.** `if (FOO)` · `return FOO` 같은 읽기까지 전부
  검사하면 검출력은 오르지만 스코프를 해석하지 않는 이 설계에서는 오탐이 난다. 오탐이 한 번
  나면 게이트는 그날로 꺼진다 — **오탐 억제를 설계할 수 없으면 배선하지 않는다**(UH-5 선례).

---

## close 체크

- [x] 1 무엇이 통과했나 — `prepush_check` 전 단계 통과, 배포 HTML 의 JS 를 읽는 검사기 0개
- [x] 2 구체 룰 정의 — `DEPLOYED_JS_UNDEFINED_CALL`(입력·판정식·severity·오탐억제·실측 FP 0)
- [x] 3 배선 위치 + scope — `prepush_check.py` L35/409/450/581/600(FULL 전용) · `.githooks/pre-push` L23 · 매니페스트 · 변이시험. **실행으로 exit 2 확인**
- [x] 4 exception 근거·등재 위치 — **없음**(allowlist 2종이 코드에 열거, 확대는 owner 권한)
- [x] 5 미배선 잔여 + 후속 티켓 — UH-26(헤드리스 런타임) · UH-27(라이브 축 비차단), 티켓 2건 발주
