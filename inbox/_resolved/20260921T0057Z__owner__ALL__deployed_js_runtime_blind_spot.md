---
from: owner
to: validation
created: 20260921T0057Z
status: resolved
route: blind_spot
company: ALL
period: N/A
rule: (신설 대상) DEPLOYED_JS_RUNTIME
iter: 1
---

## 미결 (sender 작성)

**게이트가 전부 초록인 상태로, 라이브 K-ICS 금리민감도 패널이 39사 중 36사에서
JS 예외로 죽은 채 하루 넘게 배포돼 있었다.** 데이터는 100% 정상이었다.

### 사고 요약 (오케스트레이터 실측, 2026-09-21)

- `K-ICS.html:1368-1369` 이 `IQP()` 호출 → 정의는 `2dbc4ca`(2026-09-20 designer 커밋)가
  삭제. `renderSensDetail()` 이 `ReferenceError: IQP is not defined` 로 중단.
- 예외가 듀레이션 카드 **뒤**, placeholder 숨김 **앞**에서 터져서 화면은
  "데이터는 일부 보이는데 미공시 문구가 떠 있는" 상태가 됐다. owner 가 QA로 잡았다.
- 통과한 게이트: `prepush_check.py` 전 단계. `tests/test_deploy_assets.py` 는
  keep-list·인라인금지·BOM·삭제경로 참조만 본다. **배포 HTML 의 JS 가 실제로
  실행되는지는 아무도 안 본다.**

### 시킬 일

1. **포스트모템**: `incident-postmortem` 스킬대로 5칸 전부 채워서
   `docs/postmortems/PM-20260921_kics_sens_iqp_referenceerror.md` 작성,
   `docs/postmortems/README.md` 색인 갱신.
2. **진짜 게이트 신설**. 배포 4종(`index.html`·`K-ICS.html`·`IFRS17.html`·`공시보고서.html`)에
   대해 런타임 오류를 잡는 검사를 만들고 **`scripts/prepush_check.py` 에 호출을 넣는다.**
   - "문서에 mandatory 라고 썼다 ≠ 강제" — 배선 자리를 그 자리에서 확인하고,
     `tests/test_push_gate_wiring.py` 에도 반영한다.
   - 방식은 validation 판단. 후보 ①헤드리스 브라우저로 4페이지 로드 + 회사/분기 셀렉터를
     순회하며 uncaught error 0 확인 ②`<script>` 블록만 파싱해 "호출되는데 정의가 없는
     식별자" 정적 검사. ①은 회사망/헤드리스 안정성 리스크(메모: preview_eval 반복 행 →
     Edge headless `--dump-dom` 로 우회한 전례), ②는 CSS `var()`·주석·문자열 노이즈를
     반드시 걸러야 한다. 둘 다여도 좋다. **오탐 0 을 실측으로 보이고 나서 배선할 것.**
   - 스코프 판정(`prepush_check.py` §0)에 루트 HTML 이 이미 "전체 게이트" 트리거이므로
     범위 목록을 건드릴 일은 없을 것이다. 건드리면 `tests/test_prepush_scope.py` 동반.
3. 신설 게이트가 **이번 사고를 실제로 잡는지** 회귀로 보인다: `IQP` 정의를 지운 상태에서
   RED, 복구 후 GREEN. 변이시험 형태로 테스트에 박는다.
4. designer 에 `inbox/designer/20260921T0057Z__owner__ALL_2026.2Q__kics_sens_IQP_referenceerror.md`
   로 수정 발주가 나가 있다. 코드 수정은 designer 몫이니 중복으로 고치지 말고,
   게이트·포스트모템만 맡는다(검증 목적의 일시적 수정은 커밋하지 말 것).

## 답변 (recipient 작성 — 처리 후)

**처리: validation, 2026-09-21.** 4항목 전부 완료. 배포 HTML·마스터 JSON 은 한 바이트도 안 건드렸다.

### 1) 포스트모템 — `docs/postmortems/PM-20260921_kics_sens_iqp_referenceerror.md` (5칸 전부, `closed`)

색인 + UH 표 갱신(`docs/postmortems/README.md` L78 · L120-121). 4칸(exception)은 **"없음"**
이다 — 고칠 데이터 셀이 0개라 면제할 대상 자체가 없다.

**영향 범위를 재측정해 티켓의 "36사" 를 정정한다.** 예외는 `if (postRatio) { … IQP() … }` 안에서만
터지므로 그 분기에 **적용후 지급여력비율 행이 있는** 버킷만 죽는다(적용전만 있으면 색상이
리터럴 `'#6c757d'` 이라 산다). 실측 — 선택 가능한 (회사,분기) 버킷 **138** 중 **129(93.5%)** 가
사망, 살아난 9버킷은 동양생명 2024.4Q · 삼성생명 2024.4Q/2025.2Q/2025.4Q · 신한이지 2025.4Q ·
카카오페이손보 2025.4Q · 하나손보 2024.4Q/2025.2Q/2025.4Q. **기본 화면(최신 분기)에서는
39/39 사 전부**다(`qSelect.value = quarters[0]`).

### 2) 신설 게이트 — `scripts/validate_deployed_js.py` (정적, 브라우저 없음)

페이지가 **실제로 로드하는** 스크립트(인라인 `<script>` + 같은 저장소 `<script src>` 4개)를
렉서로 토큰화해 `참조 − 바인딩 − 브라우저내장 − CDN전역 ≠ ∅` 이면 RED(`DEPLOYED_JS_UNDEFINED_CALL`).
같은 게이트에 `DEPLOYED_JS_SCRIPT_MISSING`(로컬 `<script src>` 부재) ·
`DEPLOYED_JS_UNSCANNABLE`(렉서 실패 = fail-closed, SKIP 금지)도 있다.

- **오탐 억제가 설계의 전부다.** `바인딩` 은 과대추정(스코프 미해석), `참조` 는 과소추정
  (멤버호출·옵셔널체이닝·메서드축약 정의 제외). 둘 다 "못 잡는 쪽" 으로 틀려 있어 **잡으면 진짜**다.
- 티켓이 지목한 노이즈는 렉서가 원천 차단한다 — CSS `var()`/`rgba()`·한국어 산문은 문자열·주석
  안이라 토큰에 안 들어온다. 단 템플릿 `${…}` **안쪽은 진짜 코드라 재귀 토큰화**한다.
- **오탐 0 실측(배선 전)**: 4페이지 · 토큰 73,175 · 참조지점 3,627 · **RED=0**.
  designer 가 임시 스윕에서 만난 `formatter`·`afterDraw` 오탐도 안 난다(`name(…){` = 메서드 축약
  정의로 판정). `gtag`/`dataLayer` 는 CDN allowlist 에서 **뺐다** — 그건 인라인 GA 스니펫이
  만드는 것이라 넣어 두면 스니펫이 지워져도 안 걸린다(빼고도 RED 0).
- **검출력 실측**: `function NAME(` 전수 변이 **183건 중 172건(94%) 검출**. 미검출 11건 사유
  전건 규명 — 9건은 같은 이름이 `download-survey.js`/`theme.js` IIFE 안에도 있어 과대추정에
  흡수(UH-26), 2건은 진짜 무해(즉시실행 명명함수식 · 호출처 0 인 죽은 코드).
- 작업 중 **내 룰의 버그를 실측으로 잡았다**: `.catch(err => {…})` 를 catch 절로 읽어 콜백 본문의
  이름을 통째로 바인딩으로 삼켰다(거짓음성 3건). 멤버 위치 가드를 넣어 168→172 로 회복.
- 비용: **인-프로세스 0.09초**(훅이 부르는 방식) · 단독 실행 2.9초(파이썬 기동 2.2초 포함).
  라이브 감사 축을 켜면 +2.3초(git show 8회).

**배선 (그 자리에서 확인, 문서 아님)**
| 확인 | 위치 |
|---|---|
| import | `scripts/prepush_check.py:35` |
| 실제 호출(§1f, `_run_korean_master_gates()` 본문) | `scripts/prepush_check.py:409` `n_js = deployjs.main([])` |
| 언팩 | `:450` |
| **exit code 반영** | `:581` `blocked = … or n_js` → `:600` `return 2 if blocked else 0` |
| 훅 | `.githooks/pre-push:23` (`core.hooksPath=.githooks` 확인) |
| 매니페스트 | `tests/test_push_gate_wiring.py` `WIRED["validate_deployed_js"]` |
| 변이시험 묶음 | `scripts/prepush_check.py:547` `tests/test_deployed_js_gate.py` |

**범위 목록은 안 고쳤다.** §0 `ROOT_FULL_SUFFIXES` 에 `.html`·`.js` 가 이미 있어 루트 HTML/JS
번들은 자동 FULL 이다 → "화면을 고쳤는데 화면 게이트를 건너뛰는" 조합이 구조적으로 안 나온다.
`tests/test_prepush_scope.py` 는 **무수정 통과**(단 `_run_korean_master_gates` 가짜 반환값에
`js` 키를 더했다 — 안 더하면 `main()` 이 KeyError 로 죽는다).

### 3) 이번 사고를 실제로 잡는지 — RED → 복구 → GREEN

- **실물 증거**: `validate_deployed_js.py --git-ref origin/main` →
  `K-ICS.html:1368 IQP` · `K-ICS.html:1369 IQP` · **RED=2**. 오케스트레이터가 보고한 그 두 줄이다.
- **엔드투엔드 exit code**: origin/main 의 깨진 `K-ICS.html` 을 스크래치패드 트리에 놓고 같은
  호출 경로로 `prepush_check.main()` →
  `PRE-PUSH VERDICT … 배포 JS 런타임=BLOCK … → BLOCKED`, **exit 2**.
  designer 복구본으로 바꾸면 `배포 JS 런타임=clear … gate-clear`, **exit 0**.
- **상주 회귀**: `tests/test_deployed_js_gate.py` **24케이스 8.6초**.
  ① 4페이지 오탐 0(상주판) ② `IQP` 정의를 **메모리에서** 지우면 RED(호출부 2줄)·원본이면 GREEN
  ③ 같은 사고형태를 4종 전부에서 잡는지 전수 변이(검출률 하한 70% 강제)
  ④ killer 변이 6종(allowlist 확대 / 호출을 정의로 계상 / 참조 수집 제거 / 인라인 스크립트 미독해
  / 렉서 실패 묵인 / 없는 `<script src>` 묵인) 전부 케이스를 죽이는지
  ⑤ 노이즈 내성(CSS `var()`·주석·정규식·템플릿).
  **`K-ICS.html` 은 디스크에서 한 번도 수정하지 않았다**(변이는 전부 읽어 온 문자열에만).

### 4) designer 와의 분담

코드 수정 0건. designer 티켓 끝에 `### 검증 메모 (validation, 2026-09-21)` 로 재확인 결과만
남겼고 status 는 안 건드렸다. designer 복구본은 신설 게이트에서 RED=0 이다.

### 미배선 잔여 (조용히 남기지 않는다)

- **UH-26 — 런타임 전용 실패는 여전히 무검사.** `TypeError` · `getElementById()` null ·
  차트 옵션 스키마 · fetch 모양 변화 · **스코프 오류**(정적 변이 183건 중 9건 미검출). 헤드리스를
  차단축으로 쓰려면 ① CDN 오프라인 ② 브라우저 없는 클론에서 SKIP 이 fail-open 이 되지 않는 설계
  가 선행조건이라 이번엔 안 배선했다. 티켓
  `inbox/validation/20260921T0630Z__validation__ALL__headless_runtime_smoke_feasibility.md`.
- **UH-27 — 라이브 축은 인쇄만 하고 막지 않는다.** 이번 사고의 본질이 "이미 배포된 것이 하루 넘게
  깨져 있었는데 아무 기계도 말을 안 했다" 라서 `_live_audit()` 을 넣되 **비차단**으로 뒀다(차단하면
  designer 가 main 을 고칠 때까지 무관한 작업까지 전부 막힌다). 매 실행
  `[라이브 감사 · 비차단] origin/main@<sha> RED=n` 을 **인쇄**한다. **지금 라이브는 RED=2 다** —
  배포 발주 `inbox/publishing/20260921T0630Z__validation__ALL__live_main_still_broken_deploy_iqp_fix.md`.
  상시 차단으로 올릴지는 owner 판단.

### 재현 명령

```
$py = C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
$py scripts/validate_deployed_js.py                      # 워킹트리 RED=0 + 라이브 감사
$py scripts/validate_deployed_js.py --no-live            # 차단 축만 (0.09초)
$py scripts/validate_deployed_js.py --git-ref origin/main   # 사고 재현 RED=2
$py -m pytest tests/test_deployed_js_gate.py tests/test_push_gate_wiring.py tests/test_prepush_scope.py -q
$py scripts/prepush_check.py                             # FULL 게이트
```

Claude Opus 5, 단일 세션. 모델·소요는 changelog 에 기록.

## 종결 (orchestrator, 2026-09-21)

재확인: `validate_deployed_js.py --no-live` 워킹트리 RED=0 · `--git-ref origin/main` RED=2 (K-ICS.html:1368/1369 IQP). `pytest tests/test_deployed_js_gate.py tests/test_push_gate_wiring.py tests/test_prepush_scope.py tests/test_deploy_assets.py` 156 passed / 2 skipped. `prepush_check.py` 배선(import L35 · 호출 §1f · `blocked … or n_js` · 변이시험 묶음) diff 로 확인. UH-26(헤드리스)·UH-27(라이브 감사 비차단)은 각각 `20260921T0630Z` 티켓·owner 판단으로 남긴다.
