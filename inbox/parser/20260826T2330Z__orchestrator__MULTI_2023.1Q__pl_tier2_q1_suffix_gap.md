---
from: orchestrator
to: parser
created: 20260826T2330Z
status: open
route: reparse
company: MULTI
period: 2023.1Q
rule: PL_BUCKET_ABSENT
lane: ifrs17
iter: 1
---

## 미결 (orchestrator 작성)

**2023.1Q 만 PL 버킷이 통째로 없는 회사가 4곳이다. 최소 1곳은 raw 에 값이 있는 것이 확인됐다.**

이건 배포 차단 사유가 아니다(main 라이브에도 이미 없는 선행 결함이고, `3z-b` baseline 에
비차단으로 등재돼 있다). 다만 **확정 근거가 곧 종결될 다른 티켓 말미에만 달려 있어** 유실될
자리라서 독립 티켓으로 고정한다.

### 대상

| 회사 | 분기 | 워터폴 상각 | 판정 |
|---|---|---|---|
| 삼성화재해상보험 | 2023.1Q | 3760.4억 | `PARSER_GAP_CONFIRMED` |
| NH농협손해보험 | 2023.1Q | 604.6억 | `UNADJUDICATED` |
| 롯데손해보험 | 2023.1Q | 392.8억 | `UNADJUDICATED` |
| 케이디비생명보험 | 2023.1Q | 111.2억 | `UNADJUDICATED` |

넷 다 **PL 은 2023.2Q 부터 시작하고 워터폴만 2023.1Q 부터** 있다. 회사 특성이 아니라
**축이 한 분기 잘린** 모양이다.

### 확정된 것 — 삼성화재 2023.1Q 는 raw 에 값이 있다

```
data/dart/FY2023_Q1/raw/KR0008_삼성화재해상보험/xml/20230515002508.xml
  '(10) 당분기와 전분기 중 주요 보종별 보험수익 및 재보험비용의 내역 · 1) 제74(당)기 1분기'
  구분 [장기|자동차|일반|합 계] 표에  보험계약마진 상각 = 376,038백만원 (= 3,760.38억)
  → 같은 분기 워터폴 상각 3,760.4억 과 일치
```

**추정 원인: 분기(1Q) 어미 변형을 안 태운다.** 2023.2Q 이후는 같은 노트가
`'당반기와 전반기 …/제74(당)기 반기'` 표기이고 그쪽은 추출에 성공한다(2023.2Q 누적
759,126백만원). 즉 `당분기/1분기` 형태만 캡션 매칭에서 빠지는 것으로 보인다.

**이 룰이 태어난 사고와 같은 회사·같은 축이다** — `validate_data_contract.py` L1331-1332 주석:
"라이브에 삼성화재 2026.2Q PL 생명장기 분해가 통째로 null(화면 0)인 채로 나갔다".

### 부탁

1. 캡션 매칭에 **분기 어미 변형**(`당분기`·`제N(당)기 1분기` 등)을 태워 삼성화재 2023.1Q 를
   먼저 닫아 달라. 닫히면 `3z-b` 가 자동으로 `PL_BUCKET_ABSENT_BASELINE_INERT` 를 인쇄하니
   `data/_gold/pl_amort_coverage_baseline.json` 에서 그 줄을 지우면 된다.
2. 나머지 3사(NH농협손해·롯데손해·KDB생명)는 `UNADJUDICATED` 다 — validation 판별기가
   대조군 7건 중 5건 위음성이라 "없다"고 말할 근거가 없다고 명시했다. **회사별로 raw 를 직접
   열어** 값이 있으면 닫고, 진짜 없으면 사유를 baseline note 에 적어 달라.
   raw 는 디스크에 있다(예: `data/dart/FY2023_Q1/raw/KR0032_NH농협손해보험/20230515002460.xml`).
3. **카테고리로 단정하지 말 것** — 생/손보나 상장여부로 뭉뚱그리지 말고 회사별 실데이터로.

전체 12건 등재부와 건별 근거: `data/_gold/pl_amort_coverage_baseline.json`
사각 자체의 발견 경위: `inbox/validation/20260826T2000Z__orchestrator__MULTI__pl_amort_crosscheck_blindspot.md`

## 답변 (parser 작성 — 처리 후)

<처리 결과. 못 했으면 왜 못 했는지.>
