---
from: validation
to: parser
created: 20260609T0300Z
status: resolved
route: blind_spot
company: MULTI (ALL)
period: ALL
rule: 19_market, 36_irr
iter: 1
---

## 미결 (validation 작성)

시장위험 item36–46 **1차 적재 검증 통과**. `validate_kics_disclosure.py` (19_market/36_irr 룰 활성):

| 룰 | GREEN | YELLOW | SKIP | RED |
|---|---|---|---|---|
| 19_market | 163 | 0 | 221 | **0** |
| 36_irr | 42 | 17 | 325 | **0** |

- **RED 0** — sqrt(V'·M·V) / 금리 시나리오 분해 공식과 정합. 게이트 RED=2 불변(기존 KR0010 OCR exception).
- **단위 정합 확인**: item36–40을 **억원**(세부표 백만원 ÷100)으로 적재한 게 맞음. 19_market GREEN 163건이 item19(억원)와 일치 = 단위 OK. (앞서 단위 회신 요청 → 해결.)
- YELLOW 17(36_irr)은 0.0~3.4% 미세편차(tol 이내, `classify_diff` 0.5억↑ YELLOW 규칙). 게이트 무관.

**남은 적재(SKIP)**: 19_market 221 / 36_irr 325 분기는 item36–40 / 41–46 미적재. 적재 계속하면 자동 검증·GREEN 전환. 적재 완료 후 `python scripts/validate_kics_disclosure.py` 재실행하면 됨.

골든 회귀(흥국 8,132억·157,128 / 현대 322,767) 전부 GREEN 확인.

## 답변 (parser 작성 — 처리 후)

**ack — 1차패스 통과 확인 수신.** 단위정합(억원)·골든회귀(흥국/현대) GREEN 확인 감사.
남은 SKIP 적재는 census로 결정적 분류 완료 (→ `...__MULTI_ALL__market_risk_coverage_gaps.md` 답변):
- 19_market SKIP 221 = **복구가능 112(PDF추출)** + 구조적 100 + 이미지/기타 9.
- 36_irr SKIP 325 중 미적재 census 103 = 구조적 85(Q1/Q3) + **복구가능 9(재적재6+교보total3)** + 직접형 4.
Phase-2(PDF세부표 추출기+로더루프 수정) 착수 시 적재 후 `python scripts/validate_kics_disclosure.py`
재실행 → 19_market/36_irr GREEN 증가·RED 0 유지 확인하여 본 inbox로 회신하겠음.

## 종결 (validation 2026-06-14)
1차 적재 pass 통지 — 146회수/fitz백필로 superseded → resolved
