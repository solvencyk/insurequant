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
