---
from: orchestrator
to: validation
created: 20260821T1810Z
status: answered
route: rule_wiring
company: KR0073,KR0094
period: MULTI
rule: 36_irr / TRANSITION_AFTER_IRR_MISMATCH
lane: kics
iter: 1
---

## 미결 (sender 작성)

**owner 가 명시적으로 승인한 documented exception.** 대상은 아래 5개 (회사,분기)뿐이고,
**게이트를 YELLOW 로 강등하지 말라고 owner 가 못박았다.** 룰은 RED 그대로 둔다.

| 회사 | 분기 |
|---|---|
| KR0073 교보생명 | 2025.2Q |
| KR0094 신한라이프 | 2024.2Q · 2024.4Q · 2025.2Q · 2025.4Q |

`36_irr` 4건 + `TRANSITION_AFTER_IRR_MISMATCH` 4건 = 현재 게이트 RED 8건 전부.

### 근거 — 데이터가 아니라 재현식이 이 회사들에 안 맞는다

**① item36 자체는 정상값이다.** 같은 item36 을 시장위험 축에 넣으면 완전히 닫힌다:
`item19 == sqrt(item36~40 · MARKET_M)` 잔차 **0.002% 이내**(교보 0.000% · 신한 4분기 ±0.33억).
즉 공시 금리위험액은 다른 축에서 검산되는 값이고, 안 맞는 것은 41~46 부속표에서의 재현뿐이다.

**② 41~46 은 원문 그대로다.** 파서가 당기 열에서 직접 판독해 적재했다(전기 열 오독은 정정 완료).

**③ 현행 식이 옳다 — 전사로 검증했다.** owner 가 "평균회귀 충격량도 0 으로 절단해야 하지 않냐"고
지적해 전사 재측정했다. 41~46 완비 226버킷 기준:

| 식 | 통과 |
|---|---|
| **A 현행** `sqrt(max(상승,하락)² + max(평탄,경사)²) + (충격전−평균회귀)` **signed** | **221/226 (97.8%)** |
| B 평균회귀도 0 절단 | 123/226 (54.4%) |

판정이 갈리는 **102건이 전부 "A만 통과"**. A 로는 소수점까지 맞는다(메리츠 2023.4Q 공시 5,061 vs
A 5,060.7 · 삼성화재 2023.2Q 공시 19,010 vs A 19,010.5). **평균회귀 이익을 상계하는 것이 실제 서식이다.**
따라서 식은 건드리지 않는다. owner 식(B)이 신한 2025.2Q(+2.4%)·2025.4Q(+0.5%)에 잘 맞은 것은
2024년 두 분기(−12.5%·−20.4%)와 교보(+49.7%)에서 깨지므로 우연으로 판단했다.

**④ 교보는 하한 자체를 못 지킨다.** 2025.2Q 금리상승 시나리오 **단일 충격량 684,600 백만원**이
공시 금리위험액 **459,988** 보다 크다. 어떤 합성식을 써도 최악 단일 시나리오보다 작아질 수 없다.
표의 순자산가치와 공시 위험액이 같은 기준이 아니라는 뜻이다.

**⑤ 회사가 작성기준 변경을 명시했다.** 신한라이프 2024.4Q raw **p144 주2**(원문 그대로):
> 2024년부터 금리위험액 현황의 자산 및 부채는 금리위험에 직·간접적으로 노출된 자산 및 부채를 대상으로 작성

단 이 문구만으로 잔차가 설명되지는 않는다(노출 없는 항목은 모든 시나리오 열에 동일하게 들어가므로
열 간 차이에는 영향이 없어야 한다). **원인 미규명 상태임을 면제 사유에 그대로 적어라.** "스코프 때문"
이라고 단정하지 마라 — 근거가 약하다.

## 할 일

1. 위 5건에 대한 면제를 만든다. **KR0079 8_life 때 쓴 잔차 박제 방식**을 그대로 써라 —
   통째 skip 금지. 기대잔차(A식 기준 −5.2% / −17.2% / −25.6% / −7.5% / −14.9%)를 박아 두고,
   값이 바뀌어 잔차가 달라지면 **다시 RED** 가 되게 하라.
2. `TRANSITION_AFTER_IRR_MISMATCH` 4건도 같은 근본원인이므로 같은 방식으로 함께 처리하되,
   **적용전·적용후 각각** 박제하라(KR0079 때 적용전만 면제했다가 적용후가 그대로 막은 전례).
3. provenance 원장에 등재. 인용은 신한라이프 p144(주2) + 교보 p21. 이 PDF 들의 판독 가능성을
   먼저 실측하고, 텍스트로 기계검증이 안 되면 `VERIFIED_BY_IMAGE` 경로를 쓰되 그 사유를 적어라.
4. 변이시험: 면제를 끄면 8건이 되살아나고, item36 이나 41~46 중 하나를 흔들면 면제가 있어도
   RED 가 뜨는 것을 증명하라.
5. `tests/test_rule_coverage_manifest.py` 매니페스트가 영향받으면 같이 갱신하라(안 그러면 훅이 막는다).

## 하지 말 것

- **게이트를 YELLOW 로 강등하지 마라. owner 가 명시적으로 거부했다.**
- 식(A)을 바꾸지 마라. 221/226 이 그 식으로 맞는다.
- 허용오차를 넓혀 무마하지 마라. 잔차가 5~26% 다.
- 면제를 이 5건 밖으로 넓히지 마라.
- `kics_disclosure.json` 손대지 마라.

## 답변 (recipient 작성 — validation, 2026-08-21)

**배선 완료. 게이트 RED 8 → 0.** 통째 skip 이 아니라 **잔차 박제**이고, 적용전·적용후를
각각 따로 박았다. 룰은 다른 모든 (회사,분기)에서 RED 그대로다 — YELLOW 강등 안 했다.

### 0. 티켓 근거를 먼저 재측정했다 (가정하지 않음)

전부 재현됐다. **한 군데만 티켓 수치와 다르다:**

| 티켓 주장 | 내 실측 | 판정 |
|---|---|---|
| ① item19 == sqrt(36-40·MARKET_M) 0.002% 이내 | 최대 상대잔차 **0.0022%**(KR0094 25.4Q +0.4791억). 나머지 −0.0042 / −0.3312 / −0.2521 / −0.3338 | 확인 |
| ③ A식 221/226(97.8%) · B식 123/226(54.4%) | **동일** (226버킷, 적용전) | 확인 |
| ③ "갈리는 102건이 **전부** A만 통과" | **아니다.** 102건 중 **A-only 100 · B-only 2**. B-only 2건 = KR0094 2025.2Q·2025.4Q(면제 대상 자신) | **정정** |
| ④ 교보 단일 충격량 684,600 백만원 > 459,988 | 정확값 **684,627** = −5,667,711 − (−6,352,338). 부등호 성립 | 확인(수치만 정밀화) |
| ② 41-46 원문 그대로 | 5건 전부 raw fitz 로 백만원↔억원 환산까지 정확 일치 재확인 | 확인 |

정정 1건이 결론을 바꾸지는 않는다(A 우세는 그대로). 그래도 원장에 그대로 적었다 —
"전부"라는 말이 다음 사람에게 재검증을 건너뛰게 만든다.

**식·허용오차 안 건드렸다.** 잔차가 5.25~25.62% 라 어떤 tol 로도 못 덮는다.

### 1. 무엇을 어떻게 박았나

`src/solvency/validation/kics_json_rules.py` — 두 축이 **같은 함수**를 쓰도록 단일 소스화:

- `IRR_DERIVE_ISSUER_INCONSISTENT` (5건 × `{적용전, 적용후}` 잔차) · `IRR_PIN_TOL = 0.01`
- `irr_derive_expected(values)` — 도출식 하나. 룰엔진과 게이트가 **import** 한다(재타이핑 금지).
- `irr_pin_verdict(code, quarter, column, values)` → `NOT_PINNED | MATCH | DRIFT | INPUT_MISSING`

잔차 = `item36 − derive(41-46)` (전부 양수):

| 회사 | 분기 | 박제잔차(적용전=적용후) | rel |
|---|---|---|---|
| KR0073 교보생명 | 2025.2Q | 241.4373504145833 | +5.25% |
| KR0094 신한라이프 | 2024.2Q | 1287.8295634268043 | +17.17% |
| KR0094 신한라이프 | 2024.4Q | 1622.0506399332953 | +25.62% |
| KR0094 신한라이프 | 2025.2Q | 698.1839921629144 | +7.49% |
| KR0094 신한라이프 | 2025.4Q | 863.8221082879018 | +14.92% |

**두 축에 각각 배선했다** (KR0079 때 적용전만 걸어 적용후가 그대로 막힌 전례를 반복하지 않으려고):

| 축 | 파일 | MATCH | DRIFT | INPUT_MISSING |
|---|---|---|---|---|
| 적용전 `36_irr` | `kics_json_rules._validate_market_irr` | SKIP(사유 인쇄) | **RED** `IRR_EXEMPTION_RESIDUAL_DRIFT` | **RED** `IRR_EXEMPTION_INPUT_MISSING` |
| 적용후 `TRANSITION_AFTER_IRR_MISMATCH` | `validate_kics_disclosure._transition_irr_after` | `DOCUMENTED_EXEMPT_PINNED` 집계 | **RED**(fails 로 내려감) | **RED**(fails) |

추가로 `_irr_pin_recheck()` 가 매 실행 두 컬럼 잔차를 인쇄하고, 잔차가 **룰 자신의 허용오차
안으로 들어오면** `IRR_EXEMPTION_INERT` review 로 "등재를 풀어라"를 찍는다(면제가 무용해진
채 사각으로 남는 경로 차단).

### 2. provenance — PDF 5개 전부 **기계검증 가능**이라 `VERIFIED_BY_IMAGE` 안 썼다

먼저 실측했다. 인용 페이지 텍스트밀도 **1,829~3,093자/페이지**로 게이트의 image-only 반증
임계(800자/p)를 크게 넘는다. 그래서 `status: VERIFIED` + `present_markers` 로 등재했고,
게이트가 매 실행 그 페이지를 열어 마커를 재대조한다.

마커는 라벨 + **원문 수치 그 자체**다(순자산가치 6열 + Ⅳ.금리위험액). 예: 교보 25.2Q p21
`-5,667,711 … -5,742,051` · `459,988`. 신한 24.4Q p144 는 주2 원문 문장도 함께.

`data/_gold/kics_exemption_provenance.json` 에 5건 추가(총 20건). 레지스트리를
`_exemption_registries()` 에 등록했고 — 등록 전에 돌렸더니 게이트가 즉시
`EXEMPTION_PROVENANCE_MISSING` RED 5건을 띄웠다(등재 경로가 실제로 막혀 있다는 증거).

**원인은 `UNEXPLAINED` 로 적었다.** "스코프" 라고 안 썼다. 이유를 원장에도 적었다:
① 금리 비민감 항목은 충격전·5시나리오 열에 같은 금액으로 들어가 **열 간 차이에서 상쇄**되므로
대상 범위를 바꿔도 도출식 결과가 안 바뀐다. ② 그 주2 는 **2025.2Q(p28)·2025.4Q(p131)에는
아예 없는데** 잔차는 +7.49%·+14.92% 로 그대로다. ③ 교보 건에는 그런 각주조차 없고,
대신 하한 위반(단일 충격량 > 공시 위험액)이라 "같은 기준의 표가 아니다"까지만 말할 수 있다.

### 3. 변이시험 (요구사항 4)

`kics_disclosure.json` 은 **한 바이트도 안 건드렸다** — 게이트에 records 를 주입해 돌렸다.

| 실험 | 결과 |
|---|---|
| A) 면제 ON (배포본) | `validate_data_contract` **RED = 0** |
| B) 면제 OFF (레지스트리만 비움) | **RED = 8** — `KICS_36_irr` 4 + `TRANSITION_AFTER_IRR_MISMATCH` 4, 원래와 동일한 (회사,분기) |
| C) 면제 ON + 5버킷 item36 ×1.02 | IRR 축 RED **10** (적용전 5 + 적용후 5) |
| D) 면제 ON + 5버킷 item43 ×1.02 | IRR 축 RED **6** — 아래 설명 |
| E) 면제 ON + 5버킷 item44 삭제 | IRR 축 RED **10** (결측 = RED, SKIP 아님) |

**D 가 10 이 아닌 이유는 면제 탓이 아니다.** 도출식이 `max(R,0)` 로 각 쌍의 열위 시나리오를
절단하므로, 그 입력은 도출값을 **구조적으로** 못 움직인다(면제를 꺼도 룰이 못 본다).
(회사,분기)×항목 전수 스윕 결과:

- 도출값이 실제로 움직이는 입력 → **전부 DRIFT = RED** (버킷당 5개: 36·41·42 + 각 쌍의 우위 1개)
- 절단되는 입력(교보 44·45 / 신한 24.2Q·24.4Q 44·46 / 신한 25.2Q·25.4Q 43·46) → MATCH 유지
- **결측 경로는 7개 입력 전부를 덮는다** — 어느 칸이든 없어지면 `INPUT_MISSING` RED

즉 "면제가 있어도 값이 흔들리면 RED" 가 도출식이 볼 수 있는 모든 입력에서 성립한다.

**이 변이시험은 일회성이 아니라 상주한다:** `tests/unit/test_irr_pin_exemption.py` 9건
(pre-push 훅이 `tests/unit/` 을 통째로 돌린다). 범위(5건 밖으로 못 넓힘)·tol(0.01 고정)·
면제 OFF 복원·결측 RED·민감입력 DRIFT·provenance 등록까지 기계로 잡아 둔다.
골든이 아니라 변이시험으로 만든 이유: 골든은 면제가 blanket skip 으로 퇴화해도 그 상태를
그대로 박제한다.

### 4. 게이트 전후 · 훅

```
scripts/validate_data_contract.py     RED 8 → 0     (SUMMARY RED=0 YELLOW=296)
scripts/validate_kics_disclosure.py   Status RED 6 → 1 (남은 1 = KR0079 8_life 기존 면제분,
                                      blocking RED 5 → 0) · 적용후 36_irr 불일치 5 → 0
                                      · 면제 근거 provenance RED=0
tests/fixtures/kics_rules_golden.json  --update (RED 6→1, 36_irr RED 5 → SKIP 5.
                                       YELLOW/GREEN 한 건도 안 움직임)
tests/test_rule_coverage_manifest.py   FULL_COVERAGE_SWEEP=1 3 passed (226s) — 매니페스트
                                       수정 불필요(36·41-46 커버리지 불변, 신규 사각 0)
```

`sh .githooks/pre-push < /dev/null` → **exit 0**

```
PRE-PUSH VERDICT: gate RED=0 · inbox 기계적위반=0 · offline tests=pass → gate-clear  |  anomaly review queue=83
```

(오프라인 테스트 140 passed / 242.85s. `anomaly review queue=83` 은 차단 항목이 아니라
publishing §3 LLM-skeptic 큐이고 이번 변경과 무관하다 — REAL=77 · UNCERTAIN=6, 세션 전부터 있던 값.)

재현:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest -q tests/unit/test_irr_pin_exemption.py
sh .githooks/pre-push < /dev/null
```

### 5. 안 한 것 (요구사항 5)

- 룰 YELLOW 강등 **안 함**. 다른 (회사,분기)에서 `36_irr` 은 RED 그대로다.
- 식 **안 바꿈**(A식 유지). 허용오차 **안 넓힘**(룰 tol 불변, 박제 tol 0.01).
- 면제 5건 밖으로 **안 넓힘**. 실측으로 확인했다 — 적용전 226버킷 중 A식 FAIL 은 정확히 이
  5건뿐이라 면제 범위 == 현 RED 범위다(테스트가 이 등식을 강제한다).
- `kics_disclosure.json` **무수정**(변이시험도 주입으로 처리, 사후 바이트 동일 확인).
- 축 평가율 census 의 `36_irr` exempt 집합에는 **안 넣었다.** 이 면제는 "판정 안 함"이
  아니라 "매 실행 재계산해서 이 잔차인지 확인함"이라, 평가율 분모에서 빼면 면제가 지표를
  올려 주는 셈이 된다. `36_irr 적용전 평가 226/226` 그대로다.
