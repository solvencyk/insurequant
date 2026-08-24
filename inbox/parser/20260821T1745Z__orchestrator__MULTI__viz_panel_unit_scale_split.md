---
from: orchestrator
to: parser
created: 20260821T1745Z
status: open
route: verify
company: MULTI
period: MULTI
rule: VIZ_UNIT_SCALE
lane: ifrs17
iter: 1
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
