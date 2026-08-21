---
from: owner
to: designer
created: 20260620T0238Z
status: resolved
route: html
company: MULTI
period: "-"
lane: "-"
iter: 1
---

## 미결 (owner) — K-ICS.html "자본성증권 인정 한도 소진율" 도넛 잠정 숨김 (분자 재작업 대기)

K-ICS.html의 **"자본성증권 인정 한도 소진율"** 섹션(`#donut-row` = `#donut-tier1` 기본자본/신종 + `#donut-tier2` 보완자본/후순위, 대략 line 157~173, `#donut-note`·`#donut-placeholder` 포함)을 **잠정적으로 숨겨라.**

**사유:** 두 도넛 모두 **분자 정의 오류**로 신뢰 불가 —
- **tier2(보완자본)**: proxy 회사가 item3(보완자본 총액)을 분자로 써서, 한도-제외 항목(해약환급금준비금 초과분/조정준비금)까지 포함 → 전 회사 소진율 과대(>100%). 일부 table사는 반대로 분자 붕괴(삼성화재 1.8%·메리츠 0.3%).
- **tier1(신종)**: excess 추출 누락 artifact.
→ DART "증권의 발행을 통한 자금조달"의 발행 잔액으로 분자 재작업 발주됨(ifrs17, `20260620T0238Z`). 그게 들어오면 복구.

**방식 (비파괴 필수):** 섹션을 `display:none` 또는 주석 처리로 숨기되 **마크업/JS/데이터 코드는 보존**(삭제 금지) — 재작업 후 그대로 복구. 헤더(`<h2>자본성증권 인정 한도 소진율…`) 포함 **섹션 통째**로 숨겨 레이아웃 안 깨지게. 같은 페이지 다른 차트(민감도·forward capital 등)는 **건드리지 말 것**. common.css 토큰/chrome 규칙 준수.

**복구 조건:** ifrs17이 `capital_securities_issuance` JSON 제공 + 분자 wiring 완료 후 (owner가 신호).

근거 메모리: `reference_tier2_utilization_provenance`.

## 답변 (designer 2026-06-20)

완료. K-ICS.html L156 `<div class="panel">` 에 `style="display:none"` + `id="donut-section-panel"` 추가 (비파괴).

- 섹션 통째 숨김: h2 제목 + ul.subtitle + #donut-placeholder + #donut-row + #donut-note 전부 포함
- 마크업/JS/데이터(Chart.js 렌더 함수 포함) 일절 삭제 없음
- 복구: `style="display:none"` 제거만으로 원상복구 가능
- 기준 인라인 주석 `<!-- provisional: donut numerator rewrite pending (inbox 20260620T0238Z) -->` 삽입
- 인접 패널(금리 민감도·Forward Outlook) 레이아웃 무영향 확인
