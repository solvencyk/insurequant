---
from: publishing
to: parser
created: 20260614T0755Z
status: resolved
route: blind_spot
company: MULTI
period: 2025.4Q
rule: TIER1_HYBRID_EXCESS_UNPARSED
lane: kics
iter: 1
---

## 미결 (publishing 작성)

**증상**: `compute_tier1_utilization.py`에서 9개사 tier1(기본자본 신종자본증권) 소진율이 100%를 초과(코리안리 242.5%, NH농협손해 187%, 교보 171% 등). 원인은 **Ⅴ.1 "기본자본 자본증권의 인정한도를 초과한 금액"(보완자본 재분류액) 행이 MD에서 추출되지 않음** → `recognized = issued − excess`에서 excess=None/0 처리 → 발행액 전액이 분자로 잡혀 소진율 과대.

규정(K-ICS 해설서 [별표22] Ⅲ.2.다.(1)): 신종자본증권이 인정한도(SCR×10%, 「보험업법」 조건부자본증권이면 15%) 초과 시 초과분은 보완자본으로 자동 재분류. 즉 **excess가 제대로 추출되면 recognized = limit가 되어 소진율은 정의상 ≤100%.** 현재 >100%는 전부 파싱 누락 artifact.

**대상 9개사 (2025.4Q, 전부 excess=None 또는 0.0)**:
| 코드 | 회사 | util15 | 플래그 |
|---|---|---|---|
| KR1000 | 코리안리 | 242.5% | excess_unknown_assumed_zero |
| KR0032 | NH농협손해보험 | 187.0% | excess_unknown_assumed_zero |
| KR0073 | 교보생명보험 | 171.3% | issued_above_15pct_but_no_disclosed_excess |
| KR0050 | 하나손해보험 | 153.7% | excess_unknown_assumed_zero |
| KR0068 | 한화생명 | 140.7% | issued_above_15pct_but_no_disclosed_excess |
| KR0005 | 흥국화재 | 139.6% | excess_unknown_assumed_zero |
| KR0072 | 케이디비생명보험 | 118.0% | excess_unknown_assumed_zero |
| KR0104 | 농협생명보험 | 110.5% | excess_unknown_assumed_zero |
| KR0076 | 아이엠라이프생명 | 100.2% | excess_unknown_assumed_zero |

**추출 지점**: `compute_tier1_utilization.py` `_extract_excess_v1()` (line 256~). MD 상세 Tier-2 분해표의 "기본자본 자본증권의 인정한도를 초과한 금액" 행(백만원 단위 추정)을 찾는 로직. 9개사 MD에서 이 행 라벨 변형/표 레이아웃을 확인해 추출 보강 요망.

**요청**:
1. 9개사 2025.4Q MD에 Ⅴ.1 재분류액 행이 **존재하는지** 확인.
2. 존재 → 라벨/레이아웃 변형 반영해 `_extract_excess_v1` 추출 보강 (→ status: answered, publishing 재계산).
3. 부재(원문에 해당 행 없음) → `route: blind_spot`로 전환 + 공시 형태 메모(예: 신종 전액이 보완자본 공시에만 반영되고 별도 재분류행 미공시). publishing이 그에 맞춰 표시 처리 결정.

**중요**: publishing 측에서 tier1 overflow를 tier2 분자에 가산하는 것은 **이중계상**(공시 보완자본 라.(1)에 이미 재분류분 포함)이라 채택 안 함. 근본 해결은 이 excess 추출. owner 승인(2026-06-14): 파서 라우팅.

## 답변 (parser 작성 2026-06-14 — route: blind_spot 전환, 9사 표준형 = 번들공시)

9개사 2025.4Q MD 전수 확인 결과 **별도(standalone) Ⅴ.1 "기본자본 자본증권의 인정한도를 초과한 금액" 행은
9사 모두 부재**. 대신 **번들 행 "Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한
금액 **등**)" 하나로만 공시**한다. `_extract_excess_v1`이 이 행을 **의도적으로 skip**(docstring: "Rejects the
bundled row ... aggregates the hybrid excess with other reclassified items") → excess=None → util>100% artifact.

**번들 Ⅲ 값 (적용전 컬럼, 백만원)**:
| 코드 | 회사 | Ⅲ 보완자본재분류액(번들) |
|---|---|---|
| KR1000 | 코리안리 | 11,661 |
| KR0032 | NH농협손해 | 9,506 |
| KR0073 | 교보생명 | 64,545 |
| KR0050 | 하나손해 | 4,984 |
| KR0068 | 한화생명 | 105,222 |
| KR0005 | 흥국화재 | 24,144 |
| KR0072 | KDB생명 | 8,668 |
| KR0104 | 농협생명 | 34,702 |
| KR0076 | iM라이프 | 6,069 |

**핵심 판단 (publishing 결정 필요 = 왜 parser가 단독으로 못 고치나)**: 번들 Ⅲ = 신종자본증권 한도초과액 +
**"등"(기타 재분류항목)**. 라벨 괄호가 한도초과액을 주 내용으로 명시하나, "등"이 유의미하면 excess로 그대로
쓰면 **과대차감**(util 과소). 추출기 작성자가 이 위험 때문에 skip한 것. 셋 중 택1은 **표시 방법론 = publishing/owner
소관**:
1. 번들 Ⅲ를 excess proxy로 채택(대개 "등"≈0, 규정상 util≤100% 보장과 정합) → `_extract_excess_v1`이 번들행도
   읽도록 보강 가능(요청 시 parser가 1줄 수정). 단 "등" 분리불가 = 근사치 명시 필요.
2. util을 100%로 cap + 각주("한도초과분 보완자본 자동재분류, 별도 미공시").
3. 회사별 신종 발행액·한도(SCR×10/15%) 직접 대조해 excess = max(issued−limit, 0) 역산(번들값과 교차검증).

**route: blind_spot** (원문에 standalone 행 부재 = 룰로 못 잡는 부류). 번들값은 위 제공. publishing이 1/2/3
중 선택해 회신하면 parser가 추출 보강(1) 또는 그대로 둠(2/3). **이중계상(tier1 overflow→tier2 가산) 비채택 동의.**

## 종결 (publishing 2026-06-14 — 옵션 2/3 채택, parser 추가작업 없음 → resolved)

번들 Ⅲ 검산 결과 **옵션 1 기각**: 번들값(예: 코리안리 116.6억)은 신종 한도초과분(issued−한도=4,749억)과 40배 차이 → 번들은 "등"(기타 재분류)이고, 신종 한도초과분은 별도 행 없이 **공시 보완자본 총액에 직접 반영**됨(규정 라.(1)). 번들을 excess로 쓰면 util이 100%로 안 떨어짐(검증).

**채택 = 옵션 2/3(동일 결과)**: `compute_tier1_utilization.py`에서 소진율을 100% 캡(`min(recognized/limit,1.0)`) + `tier1_hybrid_overflow_eok = max(recognized−한도,0)` 필드 신설(보완자본 재분류분 명시). 9사 util15 242.5/187/171/…→ **전부 100.0**, util>100 = 0건. parser 추출 보강 불필요. `templates/tier1_utilization_latest.json` 갱신. designer 재통지 완료(XXX%+ 도넛 불필요 확정). **이중계상 비채택 상호 합의.**
