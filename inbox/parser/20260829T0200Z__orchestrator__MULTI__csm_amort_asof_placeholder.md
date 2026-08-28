---
from: orchestrator
to: parser
created: 20260829T0200Z
status: answered
route: reparse
company: MULTI
period: MULTI
lane: ifrs17
iter: 1
---

## 미결 (orchestrator 작성 — owner 지적)

**`CSM_amortization.json` 과 xlsx `CSM상각` 시트의 `공시분기` 가 상수 placeholder 다.**

```
공시분기  distinct = 1   ->  전 390행이 문자열 'annual (filings skim)'
```

컬럼이 없는 게 아니라 **provenance 처럼 생긴 자리가 아무 as-of 정보도 안 담는다.** CSM 상각
스케줄은 결산마다 다시 산출되는데 이 표만으로는 어느 공시분의 스케줄인지 알 수 없다.
xlsx 다운로드로 나가면 인용하는 쪽이 시점을 특정할 방법이 없다.

### as-of 정보는 이미 있다. 안 쓰고 있을 뿐이다.

`scripts/viz_build_ifrs17_panels.py:1557` 의 `build_panel()` 이 패널 전체에
`{"period": "annual (filings skim)"}` 상수를 박는다. 그런데 같은 함수가:

- 회사별로 최선의 공시를 골라 **`rcept_no`(14자리 DART 접수번호)를 이미 보유**하고
  (`csm_amort_schedule.json` 의 39개사 전부에 들어 있다),
- **`_period_asof_from_rcept()` 변환 함수도 이미 존재**하며,
- 민감도 패널만 `add_as_of=True` 로 그것을 쓴다. 상각 패널은 안 쓴다.

### 왜 지금 고쳐야 하나 (실측 정정 포함)

**현재는 39개사 전부 `rcept_no` 가 2026년 접수분이라 이질성이 실제로 없다.** 그래서 지금
당장 틀린 숫자가 나가는 것은 아니다.

**그러나 그 함수의 주석이 폴백을 명시한다** — *"an empty FY2025 re-extract does NOT clobber a
good FY2024 (owner: FY2025-missing → keep FY2024)"*. 즉 **회사마다 다른 연도 공시가 섞이는 것이
설계된 동작**이고, 그 일이 벌어지는 순간 상수 라벨이 그것을 조용히 감춘다. 이 저장소가
반복해서 당한 "맞는 산수·틀린 소스" 패턴의 전형이다. 이질성이 없는 지금이 고치기 가장 싸다.

### 요청

1. 상각 패널에도 회사별 as-of 를 부여해라. 기존 `_period_asof_from_rcept()` 를 재사용하고
   **새로 구현하지 마라**(민감도 경로와 어긋난다).
2. `CSM_amortization.json` 의 `공시분기` 를 회사별 실제 값으로 채워라. 지금은 하류에서
   `rcept_no` 가 탈락하므로 그 전달 경로도 같이 손봐야 한다.
3. **`as_of`(날짜)도 같이 실을지 판단해서 보고해라.** 민감도 패널은 `period`+`as_of` 둘 다 싣는다.
   일관성 관점에서는 싣는 쪽이 맞아 보이나 xlsx 컬럼이 하나 느는 문제라 근거와 함께 제안해라.
4. **화면 영향을 확인해라.** `IFRS17.html` Panel 4(CSM 상각 스케줄)가 이 데이터를 쓴다.
   라벨이 "annual (filings skim)" 로 어딘가에 노출되고 있으면 실제 분기로 바뀐다 — 바뀌는 곳을
   보고해라.
5. xlsx `CSM상각` 시트는 `scripts/sync_master_xlsx_sheet.py` 로 그 시트만 반영해라.
6. 골든 `tests/test_viz_ifrs17_panels_golden.py` 가 이 빌더 산출을 고정한다. 인플레이스 덮어쓰기
   빌더이므로 **실행 전 백업**하고, 산출이 의도적으로 바뀌므로 `--update` 재생성 + 커밋에 이유 기록.

### 선행 조건 — 순서 지킬 것

xlsx 를 건드리므로 다른 에이전트와 겹친다. **아래 둘이 끝난 뒤 시작해라.**

- `20260828T1900Z` (NH 재보험 item11) — `손익분해PL` 시트 사용 중
- `20260829T0100Z` (자본 마스터 3종 편입) — 신규 시트 3개 추가 예정

시작 전 `git status` 로 확인하고, 끝난 뒤 다른 시트가 안 바뀌었는지 sync 의 사후검증으로 확인해라.

### 하지 말 것

- `PL_breakdown.json`·`pl_breakdown_master.json`·`IFRS17_BS.json` 및 그 시트 금지.
- `index.html`·`K-ICS.html`·`IFRS17.html` 금지(화면 영향은 **보고만**, 수정은 designer 소관).
- `build_master_xlsx.py` 통짜 실행 금지. openpyxl 로 마스터 xlsx 재저장 금지.
- 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.

## 답변 (recipient 작성 — 처리 후)

**요청 1-2, 5-6 완료 (as-of 채움 + xlsx 반영 + 골든 재생성). 요청 3(as_of 컬럼)은 판단 결과
지금은 추가하지 말 것을 제안. 요청 4(화면 영향)는 확인 결과 Panel 4는 무영향, xlsx와
public_exports/는 영향 있음.**

### ① 상각 패널에 회사별 as-of 부여 — `_period_asof_from_rcept()` 재사용, 재구현 없음

`scripts/viz_build_ifrs17_panels.py`의 `build_panel()`에 `apply_overrides` 파라미터를 새로
분리했다. 기존 `add_as_of` 하나로는 민감도 패널 전용 FY2025 override 치환 분기
(`_sensitivity_overrides()`)까지 같이 켜지는데, 이 override 페이로드는
`table_kind: sensitivity_analysis` 형태(시나리오 배열)라 **상각 패널에 그대로 켰다면
override 대상 18개사(`sensitivity_overrides.json`) 중 상각 패널에도 걸리는 회사의
`buckets`/`yearly`/`caption`이 통째로 시나리오 stub으로 치환될 뻔했다** — 값이 사라지는
사고였다. 그래서 `add_as_of`(= `_period_asof_from_rcept()` 호출 여부, 두 패널 공통)와
`apply_overrides`(= override 치환 여부, 민감도 패널 전용)를 분리해 `main()`에서
`csm_amort_schedule.json`은 `add_as_of=True, apply_overrides=False`로, `sensitivity_heatmap.json`은
기존과 동일하게 둘 다 `True`로 호출한다. 민감도 패널 호출 경로는 인자만 늘고 분기 로직은
그대로라 **동작 불변**(아래 검증 참조).

**채워진 as-of 값 분포 (실측, 39개사 전부):** `period` 39/39 = `"FY2025"`, `as_of` 39/39 =
`"2025-12-31"`. 이질성 없음 — 티켓의 "실측 정정"과 일치(전 39개사 `rcept_no`가 `202603xx`~
`202604xx`, 즉 2026년 3-4월 접수 FY2025 사업보고서). status(34 ok/4 empty/1 partial)는 변화 없음
— period/as_of는 status와 무관하게 채워진다(파일이 하나라도 있으면 rcept_no는 있으므로).

**검증**: 실행 전 4개 패널 파일 전부 백업(`*.bak_20260828_csmamort_asof`). 빌드 후 구조적
diff로 39개사 전원 key-set delta = `{period, as_of}` 추가뿐, **다른 필드 변경 0건**(buckets/
yearly/caption/status 전부 그대로) 확인. `insurance_pl_breakdown.json`/`bs_snapshot.json`/
`sensitivity_heatmap.json` 3개는 `cmp`로 **바이트 동일** 확인(민감도 패널 회귀 없음, override
분기 100% 보존 확인).

### ② `CSM_amortization.json` 공시분기 채움 + rcept_no 전달 경로

`scripts/build_tidy_exports.py`의 CSM_amortization 절이 패널 **전체**의 상수
`am.get("period")`("annual (filings skim)")를 390행 전부에 박고 있었다. `①`로 패널의 회사별
엔트리에 `period`가 생겼으므로, 그 절을 회사 루프 **안**에서 `c.get("period")`를 읽도록
바꿨다(`fy_to_q()`로 "FY2025"→"2025.4Q" 정규화 — CSM_waterfall/PL_breakdown이 이미 쓰는 동일
관례). `rcept_no` 자체는 xlsx 컬럼으로 노출하지 않았다(티켓이 요청한 건 공시분기가 실제
값을 담는 것이지 rcept_no 자체 노출이 아니라고 판단) — "전달 경로 수정"은 rcept_no→period
파생이 패널 층에서 끝나지 않고 tidy-export 층까지 이어지도록 배선하는 것으로 해석해
반영했다. `fy_to_q(None)`은 안전한 no-op(`None` 반환)이라 rcept_no 파싱 실패 회사는
공시분기=null이 된다(추측 금지 원칙 — 틀린 값보다 빈 칸).

`python scripts/build_tidy_exports.py --only amort`로 `CSM_amortization.json`만 재생성
(`CSM_waterfall.json`/`PL_breakdown.json`은 스킵 로그로 미터치 확인, git status로도 재확인).

**결과 (실측)**: 390행 그대로, 공시분기 390/390이 `"annual (filings skim)"` → `"2025.4Q"`로
변경. 그 외 필드(원보험사코드/원수사명/티커/생손보여부/경과차년) 변경 0건.

**부수 발견 — 반영함, 투명하게 기록**: 위 재생성이 삼성생명보험(KR0069) 10개 경과차년의
상각액도 같이 바꿨다(예: 1년차 10561.2→10307.1). 원인 추적: (a) 패널의 삼성생명 `yearly` 값은
내 변경 전/후 동일(내 코드가 만든 변화 아님), (b) 원본 추출 소스
`data/dart/extracted/삼성생명_20260311004614_csm.json`은 `0c04537` 이후 변경 이력 없음(원문
정정 아님), (c) `data/dart/viz/csm_amort_schedule.json`(패널)의 최근 변경 커밋은 `150661e`
("viz 결함 3종")·`8c1666b`("PL을 별도 기준으로")인데 `CSM_amortization.json`(tidy export)의
최근 변경 커밋은 그보다 앞선 `0c04537` — 즉 **내가 손대기 전부터 tidy export가 이미 패널보다
낡아 있었다**(패널 쪽 상각-스케줄 추출 수정이 2026-08-26에 있었는데 그 뒤로 tidy export가
한 번도 재생성되지 않음). 이번 정규 재생성 절차(`build_tidy_exports.py --only amort`)의
기계적 부산물로 자동 교정됐다 — 별도로 값을 손댄 적 없음. gold override 파일 중
`CSM_amortization`/`csm_amort`를 다루는 항목 0건 확인(override 충돌 아님).

### ③ `as_of`(날짜) 컬럼 추가 여부 — **지금은 추가하지 않기를 제안**

근거:
1. **정보량이 중복된다.** `as_of`와 `공시분기`는 둘 다 **같은 `rcept_no`를 같은 월-버킷 함수
   (`_period_asof_from_rcept`)로** 도출한다 — 항상 함께 결정되고 독립적으로 갈리지 않는다.
   공시분기가 (이번 수정으로) 실제 값을 담게 된 이상 "어느 공시분인지 모른다"는 티켓의 핵심
   불만은 이미 해소됐다. `as_of`는 같은 정보를 ISO 날짜 포맷으로 다시 말하는 것에 가깝다.
2. **이 워크북에 전례가 없다.** 12개 시트 중 `as_of` 성격의 열은 하나도 없다(민감도 패널의
   `as_of`는 JSON에만 있고 `build_tidy_exports.py`/xlsx로 이어진 적이 없다 — HTML의
   `senAsOf()`가 화면 표시에만 쓴다). 신설하면 이 워크북에서 처음이라, parser 레인이 혼자
   결정하기보다 owner/designer가 명시적으로 원할 때 넣는 게 맞다고 판단했다.
3. **최소 변경 원칙.** 티켓의 핵심 불만(공시분기가 상수라 시점을 특정 못 함)은 ①②로 완전히
   해소된다. `as_of`는 참고용 정밀도 개선이지 이 불만의 해소에 필수가 아니다.

되돌리기 쉬움: 패널에는 이미 `as_of`가 회사별로 들어 있다(①). 나중에 필요해지면
`build_tidy_exports.py`에 `"as_of": c.get("as_of")` 한 줄만 추가하고 `TEXT_COLS`에 `"as_of"`를
등록하면 된다(coerce()는 NUMERIC_COLS 미등재 열을 자동으로 text 처리하므로 날짜가 숫자로
안 깨짐). 반대 의견 있으면 알려달라 — 큰 작업 아니다.

### ④ 화면 영향 — 확인 결과

- **Panel 4(IFRS17.html `#canvasAmort`/`#amortCap`) 무영향.** 이 패널은
  `data/dart/viz/csm_amort_schedule.json`을 **직접** fetch하고(`PATHS.amort`), 읽는 필드는
  `amRow.status`/`buckets`/`yearly`/`caption`/`granularity`/`row_label`뿐 — `.period`/`.as_of`를
  읽는 코드가 없다(grep 확인, 0건). 즉 "annual (filings skim)"이라는 문자열이 Panel 4
  화면 어디에도 노출된 적이 없었고, 이번 수정으로도 차트·캡션·툴팁 어느 것도 안 바뀐다.
  (새로 생긴 `period`/`as_of`는 JSON에는 들어가지만 현재 화면 코드가 안 읽으므로 비활성 상태 —
  나중에 as-of 각주를 붙이고 싶으면 이미 데이터는 있다.)
- **`insurequant_master_tables.xlsx`의 `CSM상각` 시트는 바뀐다** — 공시분기 열이
  "annual (filings skim)" → "2025.4Q"로. 이 파일을 여는 사람(owner 리뷰 루프)에게 실제로
  보이는 변화는 여기가 유일하다.
- **`public_exports/CSM상각.json`(다운로드 팝업)은 아직 안 바뀐다 — 후속 조치 필요, 내 소관
  아님.** `download-survey.js`의 "CSM상각" 항목은 `public_exports/CSM상각.json`을 서빙하고,
  그건 `scripts/export_public_sheets.py`가 **커밋된** `CSM_amortization.json`(`git show HEAD:...`)
  으로부터 만든다 — 이 티켓이 정한 대로 `public_exports/`는 손대지 않았다. 부수 확인: 현재
  `public_exports/manifest.json`의 CSM상각 항목은 `quarter_min`/`quarter_max`가 **둘 다
  null**이다(실측 확인) — `export_public_sheets.py`가 2026-08-28에 넣은 정규식 가드
  (`_QUARTER_RE = ^\d{4}\.\dQ$`)가 "annual (filings skim)"을 걸러내기 때문("문자열 정렬 시
  알파벳이 숫자보다 뒤로 가면서 최댓값처럼 오판되는 실측 버그"를 막으려던 가드). 이 커밋이
  머지되고 `export_public_sheets.py`가 재실행되면(designer/publishing 소관) CSM상각 다운로드도
  실제 분기로 바뀌고, 이 null 두 개도 처음으로 값이 채워진다 — 별도 조치를 요청한다.

### ⑤ xlsx 반영 — `sync_master_xlsx_sheet.py "CSM상각"`

dry-run 먼저 확인 후 실행. **공시분기가 키 컬럼이라(`TEXT_COLS`) 390행 전부의 식별키가
바뀌어 diff가 "변경 셀 0 · 추가 390 · 삭제 390"으로 나온다** — 셀 EDIT이 아니라 전량
delete+insert인 게 정상이다(공시분기 하나가 변했으니 그 행의 identity 자체가 바뀐 것으로
difflib이 분류). 사후 자체검증 통과: "CSM상각 390행 × 7열 마스터와 완전 일치, 나머지 시트 값
동일". openpyxl로 직접 재read하여 독립 확인: 공시분기 distinct={"2025.4Q"}, KR0069 10개
경과차년 값이 ②의 교정값과 일치, 시트 12개(기본자본소진율/보완자본소진율/자본비율전망 등
동시 K-ICS 레인 신규 시트 포함) 전부 보존.

### ⑥ 골든 + 신설 지문 게이트

`tests/test_viz_ifrs17_panels_golden.py`: 실행 전 4개 산출 백업. drift 확인 결과
`csm_amort_schedule.json`만 sha256 이동(companies=39, status_counts 34/4/1 불변),
나머지 3개는 fixture 비교에도 아예 안 걸림(바이트 동일). `python scripts/
viz_build_ifrs17_panels.py && python tests/test_viz_ifrs17_panels_golden.py --update` 후
재실행 PASS.

세션 도중 코디네이터가 신설 게이트를 알려왔다(`scripts/validate_golden_input_fingerprints.py`,
`0ebb0ca`, 빌더의 입력·코드·산출 3축 지문 — 로직은 validation 소관이라 안 건드림). 내
`viz_build_ifrs17_panels.py` 수정 때문에 `[viz_ifrs17_panels] CODE_MOVED + FIXTURE_MOVED`
RED 2건이 뜬 상태였다. `--update` 실행 전 다른 5개 spec(ifrs17_bs/pl_breakdown/
viz_csm_waterfall/dividend/post_transition)의 입력·코드·산출 파일이 전부 clean(git status상
무관)함을 먼저 확인 — 다른 세션의 in-flight 상태를 실수로 지문에 박제하지 않기 위해서다.
`--update` 후 구조적 비교로 **5개 spec은 정확히 byte-identical, `viz_ifrs17_panels` 하나만
변경**됨을 확인(`git diff --numstat` 4줄 추가/4줄 삭제). 재실행 결과 `RED=0 → clear`.

### 회귀 확인

- `validate_master_tables.py --no-build`: exit 2지만 **내 변경과 무관** — RED=2는
  `5. SENSITIVITY_UNIT_SANITY` 절(민감도 패널 unit 판정)에서 나오는데, 이 스크립트는
  `CSM_amortization.json`/`csm_amort_schedule.json`을 아예 참조하지 않는다(grep 확인 0건,
  sensitivity_heatmap.json은 바이트 동일 확인됨) — 즉 이 exit 2는 이 세션 이전부터 있던
  상태이지 내가 만든 게 아니다. 내 티켓 범위 밖이라 손대지 않았다.
- `validate_live_artifacts.py`: RED=0. STALE_BASELINE 1건(`csm_waterfall_history.json`
  관련, 삼성생명 2023.2Q)은 내가 안 건드린 별개 파일이라 무관.
- 오프라인 `pytest`(전체 스위트): **468 passed, 2 skipped, 1 failed (571.58s)**. 그 1 fail은
  `archive/2026-08_equity_composition/test_equity_composition_golden.py` —
  `archive/tests/fixtures/equity_composition_golden.json` 파일 자체가 없어서 나는
  `FileNotFoundError`다. `equity_composition.json`은 2026-08-14에 archive되고
  `IFRS17_BS.json`이 유일 17BS 마스터가 됐다(project memory) — 내가 이번에 건드린 어떤
  파일과도 무관, 이전 세션 TODO에도 "아카이브 모듈" fail로 이미 기록된 패턴이다.

### 커밋 대상

`scripts/viz_build_ifrs17_panels.py` · `scripts/build_tidy_exports.py` ·
`data/dart/viz/csm_amort_schedule.json` · `CSM_amortization.json` ·
`tests/fixtures/viz_ifrs17_panels_golden.json` · `tests/fixtures/builder_input_fingerprints.json` ·
`insurequant_master_tables.xlsx` · 이 티켓 · `TODO_parser_ifrs17.md`. 커밋 해시: `84e491d`

status: answered — ③(as_of 컬럼 미추가 판단)과 ④의 `public_exports/` 후속 조치는 orchestrator/
owner 재확인 필요.
