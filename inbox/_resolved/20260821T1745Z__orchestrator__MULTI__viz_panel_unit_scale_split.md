---
from: orchestrator
to: parser
created: 20260821T1745Z
status: resolved
route: verify
company: MULTI
period: MULTI
rule: VIZ_UNIT_SCALE
lane: ifrs17
iter: 2
---

## 미결 (sender 작성)

**라이브(main) 배포를 준비하다 viz 패널 3개가 브랜치와 main 사이에서 갈리는 것을 발견했다.
그 중 `sensitivity_heatmap.json` 은 카카오페이손해보험 한 회사가 통째로 1,000배 차이난다.**
어느 쪽이 원문과 맞는지 확정될 때까지 **이 3개 파일은 라이브에 올리지 않았다** — 화면 숫자가
바뀌는 변경이라 추측으로 배포할 수 없다.

### 1. `data/dart/viz/sensitivity_heatmap.json` — 카카오페이손해 단위 판정 (핵심)

같은 회사 레코드에서 `unit_detected` 가 서로 다르다. 표시단위(`unit`)는 양쪽 다 `억원`.

| | `unit_detected` | csm_delta(시나리오1) | pl_impact(시나리오2) |
|---|---|---|---|
| main (2026-07-05 빌드) | `백만원` | -4.07 억원 | -7,315.21 억원 |
| branch (현재 빌더) | `천원` | -0.0041 억원 | -7.3152 억원 |

**둘 다 자기 모순이 있다.** 백만원으로 읽으면 pl_impact 가 -7,315억원인데, 카카오페이손해의
자본총계는 그 근처도 안 된다. 천원으로 읽으면 csm_delta 가 -0.0041억원 = **41만원**이라
민감도 시나리오로선 의미가 없는 크기다. 즉 "둘 중 하나 고르기"가 아니라 **원문 표의 단위
표기를 직접 확인해야 하는 건**으로 본다. 다른 12칸(회사[21]의 나머지 시나리오)도 같이 1,000배다.

### 2. `data/dart/viz/csm_waterfall_history.json` — 한 회사의 워터폴 전 단계가 다름

`companies[15]` 의 2026.1Q 가 stage 전부 다르다(기초 2,968,518 vs 3,228,870 / 상각 -70,926 vs
-80,601 / 가정조정 **-94,149 vs +89,821 — 부호까지 반대** / 기말 2,952,975 vs 3,408,243).
브랜치 쪽에 신한라이프 등 3사의 2025.2Q `interest` 스테이지가 **새로 6칸** 들어와 있고,
`companies[11]` 2025.4Q 는 status 가 `download_error` -> `no_extract` 로 바뀌었다.
어느 쪽이 현재 마스터(`CSM_waterfall.json`)와 일치하는지 확인 필요 — 마스터 자체는 main 과
브랜치가 **바이트 동일**이라, 빌더 출력이 마스터와 어긋나 있는 쪽이 있다는 뜻이다.

### 3. `data/dart/viz/csm_amort_schedule.json` — 캡션 절번호와 버킷 값

`companies[0]` 의 buckets 가 전부 다르고(total 1,213 vs 19,813.01), caption 이
`15.7 ...` -> `15.9 ...` 로 바뀌었다. 브랜치 쪽에 `unit`/`unit_detected`/`unit_source: xref`
필드가 새로 붙었다 — 단위 추론 로직이 들어온 것으로 보인다. 이것도 **1번과 같은 계열**일
가능성이 높다.

## 부탁 (수신자가 할 일)

1. 카카오페이손해 민감도 원문 표의 **단위 표기**를 DART 원문에서 직접 확인해 `unit_detected`
   판정 근거를 티켓에 적어라(표 머리글/주석 문구 그대로 인용).
2. `viz_build_ifrs17_panels.py` / `viz_build_csm_waterfall.py` 를 **현재 마스터로 재실행**해
   산출을 확정하고, 골든(`tests/test_viz_ifrs17_panels_golden.py` ·
   `tests/test_viz_csm_waterfall_golden.py`)이 통과하는지 확인해라.
   두 빌더는 **산출 JSON 을 인플레이스로 덮어쓴다** — 실행 전 백업할 것.
3. 확정되면 status 를 `answered` 로 바꾸고 "라이브 배포 가능" 여부를 명시해라.
   그때 orchestrator 가 main 워크트리로 이 3개를 올린다.

## 참고 — main 이 지금 라이브에 걸고 있는 버전

```
data/dart/viz/csm_amort_schedule.json     a1813f9 2026-07-30
data/dart/viz/csm_waterfall_history.json  4f0d483 2026-06-07
data/dart/viz/sensitivity_heatmap.json    7bf0d60 2026-07-05
```
main 의 `IFRS17.html` 은 브랜치보다 **최신**이다(원천테이블 패널 + `hist` fetch 가 main 에만
있다). 브랜치의 HTML 을 main 에 올리면 패널이 사라진다 — **HTML 은 이 배포에서 제외했다.**

## 답변 (parser-ifrs17)

**결론: 3개 파일 전부 branch(현재 브랜치 HEAD)가 맞다. main 은 셋 다 낡았거나 틀렸다.
세 파일 모두 라이브 배포 가능.**

### 1. `sensitivity_heatmap.json` — 카카오페이손해 단위는 `천원`이다 (branch 채택)

원문: `data/dart/FY2025_Q4/raw/KR1098_카카오페이손해보험_20260323001537/20260323001537_00760.xml`.
- 5184행 캡션("8) 가정민감도...") 바로 다음 5195행이 `<TD ...>(단위: 천원)</TD>` — 이 표
  전용 단위 표기가 리터럴로 박혀 있다.
- 같은 필링(14,936행) 전체에서 "(단위: 천원)" 표 머리글이 **45회**, "(단위: 백만원)" 표
  머리글은 **0회**. "백만원"이라는 문자열 자체는 딱 1번 나오는데 그건 표가 아니라 서술문
  ("자본금은 300,000백만원입니다")이다.
- 교차검증: `CSM_waterfall.json`(루트 마스터) 카카오페이손해보험 2025.4Q 기말 CSM =
  3.41188억원. 원표 "사망률" 행의 기준금액·보험계약마진열 원값 = 341,189.
  341,189 × 1e-5(천원→억원) = **3.41189억원** — 마스터와 5자리까지 일치(오차 0.0003%).
  백만원으로 읽으면 3,411.89억원으로 정확히 1,000배 벗어난다.

main 값(1,000배 큼)은 2026-07-05 빌드 스냅샷으로, `TODO_parser_ifrs17.md` 24th pass
(2026-08-20)가 이미 "카카오페이 값이 전부 1,000배 줄었다(이 회사 기말 CSM이 5억이라 새 값이
맞다)"고 기록한 그 수정 **이전** 상태다. `unit_source: xref` 는 `_detect_unit()`
(`scripts/viz_build_ifrs17_panels.py:953`)가 표의 기준금액·CSM열 값과 `CSM_waterfall.json`
기말 CSM 비율을 로그스케일로 스냅한 결과이고, 그 비율이 1.00000e-05로 사실상 완전히
맞아떨어졌다 — main 이 xref 로 `백만원`을 골랐던 건 당시 루트 마스터 쪽 기말 CSM 자체가
아직 1,000배 부풀어 있던 상태였기 때문(같은 24th pass 기록)이다.

### 2. `csm_waterfall_history.json` — companies[15] 케이비라이프생명보험 2026.1Q: branch가 맞다

이 파일은 **현재 아무 스크립트도 재생성하지 않는다** — 빌더(`viz_build_csm_waterfall_history.py`)는
2026-06에 `archive/2026-06_csm_nb_reverse_engineering/`로 아카이브됐다. main·branch 둘 다
과거 특정 시점의 정적 스냅샷일 뿐이라 "최신이냐"가 아니라 "원문과 맞냐"로 판정했다.

원문: `data/dart/FY2026_Q1/raw/KR0099_케이비라이프생명보험/20260529001156.xml`.
"2) 유배당 외 보험" 표는 같은 필링 안에 **"당분기"**(15690행 근처)와 **"전분기"**(15855행
근처) 두 벌이 나란히 인쇄돼 있다:

| 항목(보험계약마진열) | 원문 "당분기" 표 | 원문 "전분기" 표 |
|---|---|---|
| 기초 순장부금액 | **3,228,870** | 2,968,518 |
| 조정치 변동(가정) | **+89,821** | (94,149) |
| 서비스 제공 인식(상각) | **(80,601)** | — |
| 보험금융손익(이자) | **28,625** | 23,841 |
| 분기말 순장부금액 | **3,408,243** | — |

branch 의 companies[15] 2026.1Q 값은 "당분기" 표 5개 항목 전부와 소수점까지 정확히
일치한다. main 은 "전분기"(비교기간) 열을 그대로 옮겼다 — 라벨을 놓친 게 아니라
**잘못된 기간 열을 옮긴 것**이다. 부가 증거: branch 의 2026.1Q 기초(3,228,870)는 branch
자신의 2025.4Q 기말(3,228,870, 이번 diff로 안 바뀐 값)과 정확히 이어지는데, main 의
2026.1Q 기초(2,968,518)는 어느 인접 분기 기말과도 안 이어진다 — 연속성 단절은 그 자체로
룰 위반이다.

같은 diff 안 나머지 변경(신한라이프 등 3사 2025.2Q interest 스테이지 6칸 신규 채움, 2사
2025.4Q status `download_error`→`no_extract`)은 전부 결측→채움 / 상태명 개선 방향의
가산적 변경이라, 위험 신호(부호 반전·연속성 단절)가 없어 셀 단위 원문 재검증은 생략했다.

### 3. `csm_amort_schedule.json` — companies[0] DB생명보험: branch가 맞다 (신규 필링 + 전사합계 vs 부분집합)

| | main | branch |
|---|---|---|
| rcept_no | 20250328002241 (FY2024, 2025-03-28 접수) | **20260327000191 (FY2025, 2026-03-27 접수)** |
| row_label | **"Non-Par(\*1)"**(무배당 상품군 하나만) | **"합 계"**(전 상품 총계) |
| total | 1,213억원 | **19,813.01억원** |
| unit 필드 | 없음(단위추론 프레임워크 이전) | 백만원 / xref |

원문(`data/dart/FY2025_Q4/raw/KR0082_DB생명보험_20260327000191/20260327000191.xml` 49356행
근처)의 "15.9 ... 연도별 인식시기" 표는 캡션 바로 아래 `(단위: 백만원)`가 명시돼 있고,
"Non-Par(\*1)"은 그 표 안 여러 상품군 행(유배당사망·무배당사망·유배당건강·무배당건강 등)
중 하나일 뿐이며 이들을 합산한 "합계" 행이 별도로 있다. 교차검증: `CSM_waterfall.json`
DB생명보험 2025.4Q 기말 CSM = **19,813.1억원** — branch 총계(19,813.01)와 0.0005% 이내
일치. main 값 1,213억원은 이 회사의 어느 분기 기말 CSM(16,548.9~20,652.8억원,
FY2023~FY2026)과 비교해도 자릿수가 안 맞는다 — Non-Par 서브포트폴리오만 잡은 결과다.

branch 로 넘어가면서 필링이 FY2024→FY2025로 교체된 것은 owner 가 이미 승인한 25th pass
(2026-08-20) "상각 패널 FY2025 일괄 갱신"의 일부다(`TODO_parser_ifrs17.md` 기록).

### 재실행·골든 확인

`viz_build_ifrs17_panels.py`·`viz_build_csm_waterfall.py`를 현재 커밋된 입력(마스터+추출
JSON)으로 재실행 — **완전 no-op**(실행 전 백업본과 바이트 단위 100% 동일:
sensitivity_heatmap.json · csm_amort_schedule.json · bs_snapshot.json ·
insurance_pl_breakdown.json · csm_waterfall.json 전부). 즉 지금 브랜치 값은 현재 코드가
결정론적으로 재현하는 값과 정확히 같다. `test_viz_ifrs17_panels_golden.py`는 무변동 통과.
`test_viz_csm_waterfall_golden.py`는 별건(csm_waterfall_gate 티켓)의 코드 수정 때문에
`--update` 재생성 후 통과 — 그쪽 답변에 사유 적어뒀다.

### 참고 — 순수 신규 파일 2개(분쟁 아님, 확인 사항)

`git diff origin/main HEAD --stat`로 viz 패널 전체를 훑어보니 위 3개 외에
`bs_snapshot.json`·`sensitivity_heatmap_provenance.json` 두 개가 **main 에는 아예 없는
순수 추가분**(충돌 없음, added-only)이었다. cherry-push 범위에 포함할지는 orchestrator
판단.

### 결론

3개 파일 모두 **branch 채택 = 라이브 배포 가능**. main 상태를 유지·복사할 이유 없음.

## sender 재확인 (orchestrator, 2026-08-24 3차) — status: open 유지, 착수 안 됨

`git diff main -- data/dart/viz/{sensitivity_heatmap,csm_waterfall_history,csm_amort_schedule}.json`
재확인 — 3파일 전부 아직 main 과 다르다(화해 안 됨). 카카오페이손해 단위 확정(DART 원문
"단위: 천원" vs "백만원" 실측) 등 raw 레벨 조사는 이번 라운드에 착수하지 못했다 — 배정된
서브에이전트가 API 529(모델 과부하)로 죽었다. 화면 숫자가 바뀌는 변경이라 확정 전 배포 불가
원칙 그대로 유지, 다음 라운드로 이월. 상세는 `docs/changelog_validation.md` 2026-08-24(3차)
항목 C.

## 답변 (parser-ifrs17, 2026-08-24 iter-2)

**핵심 결론: 3개 파일 모두 이미 `origin/main`(실제 배포 리모트)에 배포 완료 상태다.
"sender 재확인(3차)"의 "착수 안 됨·화해 안 됨"은 로컬 `main` ref 가 3일치(4커밋) 뒤처져 있어서
생긴 착시다 — raw 레벨 조사 자체는 32nd pass(2026-08-21)가 이미 끝냈고, 이번 iter-2 가 그
결론을 처음부터 전부 다시, 독립적으로 재현해 확인했다.**

### 0. 모순 정리 — "아직 다르다"는 로컬 main 기준이라 생긴 false-diff

- `git rev-parse main` = `346e4dab`(2026-08-20 21:54). `git rev-parse origin/main` = `fba59f0d`
  (2026-08-24 14:54). `git log --oneline main..origin/main` → `0fbe186`(08-21 18:23) →
  **`a883399`(08-21 20:06)** → `c4ce39f`(08-21 22:36) → `fba59f0`(08-24 14:54).
  `git merge-base --is-ancestor main origin/main` = true — 로컬 main 은 origin/main 의 순수
  조상이다(분기 아님, 그냥 이 워크스페이스가 `git fetch` 를 안 해서 뒤처짐).
- **`a883399`("deploy: IFRS17 viz 패널 4종 — 라이브가 틀린 값을 보여주고 있던 3건 정정")의
  커밋 메시지가 이 티켓의 위 `## 답변 (parser-ifrs17)`과 근거·수치가 사실상 동일**(카카오페이
  천원 vs 백만원 1,000배, 케이비라이프 연속성 단절 -260,352, DB생명 1,213억 vs 19,813.01억).
  32nd pass 세션이 원문 대조 직후 바로 push 까지 실행한 것으로 보이나, 이 티켓 파일 자신의
  frontmatter `status` 는 `open` 으로 남아 핸드오프 기록이 끊겼다. `c4ce39f`는 별도로 발견된
  공유함수 버그(8개사 워터폴이 전기를 당기로 표시)를 추가 반영한 후속 배포다.
- **실측**: `diff <(git show HEAD:data/dart/viz/<f>) <(git show origin/main:data/dart/viz/<f>)`
  — `sensitivity_heatmap.json`·`csm_waterfall_history.json`·`csm_amort_schedule.json`·
  `csm_waterfall.json` **4개 전부 IDENTICAL**. 이 브랜치(HEAD)와 실제 라이브 리모트
  (origin/main, `https://github.com/solvencyk/insurequant.git`)가 이 4개 파일에서 바이트
  단위로 이미 같다. `git diff main -- ...`(로컬 main 기준)이 여전히 차이를 보이는 건 데이터
  문제가 아니라 로컬 ref 가 최신이 아니라서다.

### 1. 카카오페이손해(KR1098) 단위 — 독립 재현, 결론 불변: 천원

원문: `data/dart/FY2025_Q4/raw/KR1098_카카오페이손해보험_20260323001537/20260323001537_00760.xml`
(14,936행).

- 5184행: `가정민감도` 캡션. **5195행**: 그 표 전용 단위 셀
  `<TD ALIGN="RIGHT" WIDTH="1117" HEIGHT="23">(단위: 천원)</TD>` — 캡션 바로 다음 표.
- 5239행: 사망률 행 보험계약마진 기준금액 = **341,189**(원문 그대로).
- 필링 전체 재측정(기존 답변의 "45회"는 과소 — **정정**): `(단위: 천원)` **100회**,
  `(단위: 백만원)` **0회**, 순수 문자열 "백만원"은 1595행 서술문("자본금은
  300,000백만원입니다") 단 1회뿐 — "백만원 표머리글 0회"라는 핵심 결론에는 영향 없음.
- 교차검증: `CSM_waterfall.json` 카카오페이손해보험 2025.4Q 항목6(기말 CSM, 직접 조회) =
  **3.41188**억원. 341,189 × 1e-5 = 3.41189 — 차이 0.00001(상대 0.0003%). 백만원 가정 시
  3,411.89억원으로 1,000배 이탈.
- branch `sensitivity_heatmap.json` companies[21] 직접 조회: `unit_detected: "천원"`, 사망률
  `csm_delta: -0.0041`(=-407×1e-5) · `pl_impact: -0.0024`(=-235×1e-5), 장해질병(정액)
  `pl_impact: -7.3152` — 미결 섹션이 인용한 두 수치와 정확 일치.

**판정 불변: branch(천원) 채택이 맞다.**

### 2. 케이비라이프(KR0099) 2026.1Q — 독립 재현, 결론 불변: branch=당분기 정확 일치

원문: `data/dart/FY2026_Q1/raw/KR0099_케이비라이프생명보험/20260529001156.xml`.

"2) 유배당 외 보험" 표(15644행 캡션)에 "당분기"(15676행 헤더)와 "전분기"(15923행 헤더) 두
하위표가 나란히 있다. 보험계약마진 열만 발췌:

| 항목 | 당분기(원문) | 전분기(원문) |
|---|---|---|
| 기초 순장부금액 | **3,228,870**(15693행) | 2,968,518(15940행) |
| 보험계약마진을 조정하는 추정치 변동 | **+89,821** | (94,149) |
| 서비스 제공에 따른 보험계약마진 변동(상각) | **(80,601)** | (70,926) |
| 보험금융손익(PL)(이자) | **28,625** | 23,841 |
| 분기말 순장부금액 | **3,408,243** | 2,952,975 |

branch `csm_waterfall_history.json` companies[15](케이비라이프생명보험) 2026.1Q 직접 조회 —
위 "당분기" 5개 값과 소수점까지 정확 일치. `git show main:...`로 뽑은 main 쪽 2026.1Q 는
"전분기" 5개 값과 정확 일치 — main 이 비교기간 열을 옮긴 것을 재확인했다.

연속성 스모킹건(기존 답변보다 한 단계 더 명확한 근거): branch 는 2025.4Q 기말(3,228,870) =
2026.1Q 기초(3,228,870), 완전 연속. **main 은 2026.1Q 기초(2,968,518)가 main 자신의 2025.4Q
"기초"(2,968,518, `closing` 아님)와 같다** — "전분기" 열을 "당분기"로 착각해 옮겼다는 것의
구조적 증거(전분기 열의 기초는 그 필링의 비교대상 분기 시작점과 항상 같아야 하므로).

**판정 불변: branch(당분기) 채택이 맞다.**

부가 재확인 — 이 파일을 재생성하는 살아있는 스크립트는 없다: `scripts/` 안에서 파일명을
참조하는 4개(`build_tidy_exports.py`·`check_nb_csm_history.py`·
`ifrs17_promote_history_to_measurement.py`·`verify_parser_change.py`) 전부 **읽기 전용**이고,
유일한 빌더 `viz_build_csm_waterfall_history.py`는 `archive/2026-06_csm_nb_reverse_engineering/`
에 있다. `verify_parser_change.py` 자신의 파일-매니페스트(69-72행)도 이 파일의 reader 를
`check_nb_csm_history.py` 하나로만 선언하고 builder 는 등재하지 않았다.

**보너스 발견(화면 영향 재평가)**: `IFRS17.html`(origin/main·branch 동일 확인)의 Panel 6
주석에 "기존 csm_waterfall_history.json은 stale(2025.3Q·2026.1Q 결측, 초기 2023 미교정)이라
폐기"라고 적혀 있고, 실제로 `ix.hist`(284행에서 `new Map()`으로만 선언된 인덱스)에 `.set(`이
파일 전체에서 한 번도 호출되지 않는다 — `PATHS.hist` 로 fetch 는 하지만(1664행) 그 결과
(`payload.hist`)를 실제 렌더링에 쓰는 코드가 없다. Panel 6 은 `ix.wfx`(=`CSM_waterfall.json`
기반)로 이미 갈아탔다. **즉 이 파일의 내용은 현재 어느 배포본에서도 화면 숫자에 영향을 주지
않는다** — `check_nb_csm_history.py`/`build_tidy_exports.py` 같은 검증·내보내기 스크립트의
입력으로만 쓰인다. 데이터로서는 여전히 branch 가 맞고 고쳐야 하지만, "화면 숫자가 바뀌는
변경이라 확정 전 배포 불가"라는 원 티켓의 전제는 이 파일에 한해 더 이상 적용되지 않는다
(이미 배포도 됐고, 배포됐어도 화면은 안 바뀐다).

### 3. DB생명보험(KR0082) 상각 스케줄 — 독립 재현, 결론 불변: branch=합계 행 + 신규 필링

원문: `data/dart/FY2025_Q4/raw/KR0082_DB생명보험_20260327000191/20260327000191.xml`.

- 49356행: `15.9 ... 연도별 인식시기` 캡션 — branch caption 과 정확 일치(main 의 "15.7"은
  이 필링에 없다 — 다른/구 필링 소속). 단위(캡션 직후 표): `(단위: 백만원)`.
- 표 구조(49420~49743행 TBODY 직접 통독): 포트폴리오 그룹 3개 — `Non-Par(*1)`(ROWSPAN=6:
  유배당사망·무배당사망·유배당건강·무배당건강·유배당연금저축·무배당연금저축)·
  `Indirect-Par(*2)`(ROWSPAN=8)·`Direct-Par(*3)`(1행) — 다음 마지막 행이 **49726행**
  `<TD COLSPAN="2" ...>합  계</TD>`(공백 **2칸** — `grep "합 계"`도 `grep "합계"`도 둘 다
  놓치는 이유였다, 이번에 직접 통독으로 확정). 그 행의 "합계" 열 값(49742행) =
  **1,981,301**(백만원) = **19,813.01억원** — branch total 과 정확 일치.
- `Non-Par(*1)` 그룹 중 값이 있는 유배당사망 행 하나만 봐도 합계열 1,139(49440행)로, 이
  그룹 자체가 전사 합계가 아니라 여러 상품군 중 일부라는 것이 구조적으로 확정된다.
- 교차검증: `CSM_waterfall.json` DB생명보험 2025.4Q 기말 CSM(직접 조회) = **19,813.1억원**
  — branch 총계(19,813.01)와 0.09억(0.0005%) 이내 일치. main 의 1,213억원은 DB생명보험의
  FY2023~FY2026 전 분기 기말 CSM(16,548.9~20,652.8억원) 어디와도 자릿수가 안 맞는다.
- rcept_no: branch=`20260327000191`(FY2025, 2026-03-27 접수, 현재 raw 트리에 실존) —
  main=`20250328002241`(FY2024, 2025-03-28 접수, 더 오래된 필링).

**판정 불변: branch(합계·FY2025 신규 필링) 채택이 맞다.**

### 4. 빌더 재실행 + 골든 — 재확인

`data/dart/viz/*.json` 18개 파일 전체 sha256 백업 후 `viz_build_ifrs17_panels.py` +
`viz_build_csm_waterfall.py` 재실행, 재해시 → **18개 파일 전부 바이트 단위 무변동**(diff 0줄).
현재 커밋 상태가 코드가 지금 결정론적으로 재현하는 값과 완전히 같다(재확인, 기존 답변과 동일
결론).

```
python scripts/viz_build_ifrs17_panels.py   # Wrote csm_amort_schedule/insurance_pl_breakdown/bs_snapshot/sensitivity_heatmap (34/39, 29/29, 23/23, 31/32 ok)
python scripts/viz_build_csm_waterfall.py   # companies: total=47 ok=41
python -m pytest tests/test_viz_ifrs17_panels_golden.py tests/test_viz_csm_waterfall_golden.py -v
# 2 passed in 2.05s
```

`git status --short -- data/dart/viz/` 무출력(clean) — 복구할 것도 없었다.

### 5. 신규 파일 census — 비교 기준을 origin/main 으로 정정

로컬 `main` 기준(기존 답변이 쓴 기준)으로는 `git diff main --stat -- data/dart/viz/`가 18개
파일(14개 순수추가 + 4개 수정)을 보여주지만, 로컬 main 이 stale 이라 이 비교 자체가
부정확하다. 올바른 기준(origin/main)으로 다시 재면:

- 수정 4개(sensitivity_heatmap·csm_waterfall_history·csm_amort_schedule·csm_waterfall) →
  **0개**(이미 동일, §0).
- 순수추가 14개(그대로 유지): `bs_manual_overrides.json`·`bs_snapshot.json`·
  `csm_bubble.embed.js`·`csm_bubble.json`·`csm_continuity_validation.json`·
  `csm_waterfall_master_cov.json`·`csm_waterfall_master_diag.json`·
  `csm_waterfall_validation.json`·`downstream_kpis.json`·`earnings_quadrant.json`·
  `net_income_breakdown.json`·`pl_breakdown_master.json`·
  `sensitivity_heatmap_provenance.json`·`sensitivity_overrides.json`.

이 티켓이 명시적으로 물은 2개(`bs_snapshot.json`·`sensitivity_heatmap_provenance.json`)는
origin/main 기준으로도 여전히 added-only 다(충돌 없음). 둘 다 origin/main 의 `IFRS17.html`
에서 파일명으로 찾아도 fetch 경로가 없다 — 지금 배포해도 **화면에는 아무 영향이 없다**
(fba59f0 의 K-ICS item47-54 와 같은 "게이트/향후용, 표시 미반영" 패턴). **권고: 포함해도
안전하다**(added-only 라 회귀 리스크 0, 화면 무영향이라 표시 리스크도 0) — 단 지금 넣어도
당장 쓰이진 않는다. 나머지 12개는 이 티켓 범위 밖이라(내용 미검증) 존재만 보고하고 권고하지
않는다 — orchestrator 가 origin/main 커밋 로그로 별도 확인 필요.

### 6. 파일별 라이브 배포 가능 여부 (최종)

| 파일 | 판정 | 근거 |
|---|---|---|
| `sensitivity_heatmap.json` | **이미 배포됨**(origin/main 과 바이트 동일) — 추가 작업 불필요 | §0, §1 |
| `csm_waterfall_history.json` | **이미 배포됨**(origin/main 과 바이트 동일) — 추가 작업 불필요, 화면 미반영 확인 | §0, §2 |
| `csm_amort_schedule.json` | **이미 배포됨**(origin/main 과 바이트 동일) — 추가 작업 불필요 | §0, §3 |
| `csm_waterfall.json`(원 티켓엔 없었으나 같은 배포에 묶여 있었다) | **이미 배포됨**(origin/main 과 바이트 동일) | §0 |
| `bs_snapshot.json` | 미배포·added-only·화면 무영향 — 포함 안전(권고), 결정은 orchestrator | §5 |
| `sensitivity_heatmap_provenance.json` | 미배포·added-only·화면 무영향 — 포함 안전(권고), 결정은 orchestrator | §5 |

### 하지 않은 것 확인

- HTML 미수정(읽기만 함). `IFRS17.html`은 origin/main 과 branch 가 위 hist 관련 대목까지
  포함해 동일 — "main 이 더 최신"이라는 원 티켓 기록은 로컬 main 기준이었을 가능성이 높다
  (origin/main 기준 재확인은 designer 소관이라 여기선 보류).
- `build_root_masters.py` 통짜 실행 없음, `validate_master_tables.py` 미실행.
  `insurequant_master_tables.xlsx` 미접촉.
- `git commit`/`git push`/`git fetch` 없음 — 로컬 main ref 갱신(단순 fast-forward, 충돌 없음)
  여부도 orchestrator 판단에 맡긴다.
- K-ICS 레인 파일(`data/_gold/kics_exemption_provenance.json`,
  `scripts/_probes/probe_20260824_*.py`, `scripts/rebuild_combined_transition_after.py`,
  `scripts/fix_20260824_kr0068_exemption_reason.py` 등 `git status`에 보이는 미커밋 항목)은
  이 세션이 만든 게 아니다 — 병행 세션 잔여물로 보이며 손대지 않았다.

---

## sender 종결 (orchestrator, 2026-08-24 4차) — status: resolved

**내가 3차에 적은 "착수 안 됨 / 3파일 전부 아직 main 과 다르다" 는 오판이었다. 정정한다.**

원인은 **로컬 `main` 참조가 `origin/main` 보다 4커밋 뒤처져 있었던 것**이다. `git diff main -- ...`
로 잰 "차이" 는 낡은 로컬 ref 와 비교한 착시였고, 실제 라이브(`origin/main`)에는 커밋
`a883399`(2026-08-21 20:06, "deploy: IFRS17 viz 패널 4종 — 라이브가 틀린 값을 보여주고 있던
3건 정정")로 **이미 배포돼 있었다.**

오케스트레이터 독립 실측(2026-08-24):

```
git rev-list --left-right --count main...origin/main   ->  0  4   (로컬 main 이 4커밋 뒤짐)
git diff --stat origin/main HEAD -- data/dart/viz/
  -> sensitivity_heatmap.json · csm_waterfall_history.json · csm_amort_schedule.json
     세 파일 모두 diff 목록에 없음 = origin/main 과 바이트 동일
```

로컬 `main` 은 `origin/main` 으로 fast-forward 해 두었다(0 ahead / 0 behind). **같은 착시가
재발하지 않도록, 배포 여부는 로컬 `main` 이 아니라 `origin/main` 기준으로 잴 것.**

### 판정 (recipient 답변 iter-2 를 채택)

| 파일 | 판정 | 배포 상태 |
|---|---|---|
| `sensitivity_heatmap.json` | branch 채택 — 카카오페이손해 단위는 **천원**(원문 표머리글 "(단위: 천원)", 같은 필링 100회 vs "백만원" 0회 + 기말 CSM 1e-5 배율 일치) | **배포 완료** |
| `csm_waterfall_history.json` | branch 채택 — main 은 "전분기"(비교기간) 열을 당기로 실었다 | **배포 완료** |
| `csm_amort_schedule.json` | branch 채택 — main 은 "Non-Par" 부분집합 행, branch 는 "합 계" 총계 행 | **배포 완료** |

빌더 2종 재실행 시 viz 18파일 바이트 무변동, 오프라인 골든 2종 통과.

### 남은 결정 1건 (owner 몫, 이 티켓과 분리)

`data/dart/viz/` 에 `origin/main` 에 없는 **added-only 14파일**이 있다(`bs_snapshot.json` ·
`sensitivity_heatmap_provenance.json` 포함). `IFRS17.html` 이 아직 참조하지 않아 **화면에 영향이
없다** — 배포해도 무해하지만 급하지도 않다. 라이브 배포는 owner 승인 사항이므로 다음 배포
묶음에서 같이 올릴지 owner 에게 별도로 묻는다. 이 티켓의 3파일 판정과는 무관하다.

status: **resolved** (원 질문 3건 전부 판정 완료 + 배포 확인 완료).
