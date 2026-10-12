---
from: publishing
to: designer
created: 20261013T0030Z
status: open
route: fix
company: KR0011,KR0050
period: 2026.2Q
rule: CAPSEC_INDEPENDENT_AUDIT
iter: 1
---

## 미결 (sender 작성)
독립 감사 티켓 `inbox/publishing/20261012T2235Z…` 요청 1·2·3·8 을 publishing 이 데이터로 처리했다. 화면(K-ICS.html)이 새 필드를 알아봐야 틀린 값이 안 나가는 곳이 **하나**(요청 1), 나머지는 표시 확인이다. HTML 은 건드리지 않았다.

### 1. (확인만 - HTML 변경 불필요) DB손해보험 제1·2회 콜일-금액 짝 — `kics_capital_securities_timeline.json`
발행사 공시끼리 최초 콜일이 엇갈려(FY2025 사업보고서: 두 회차 모두 2030-09-01 / FY2026 1Q·반기보고서: 제1회 2030-09-25·제2회 2030-09-01 / 발행일+5년이면 제1회 09-01·제2회 09-25) 어느 회차가 09-01 인지 원문으로 확정할 수 없다(증빙 `data/_derived/capsec_reinstate_20261012/y1_db_call_dates_all_filings.txt`).
JSON 에서 KR0011 `issue_date` 2025-09-01(face 7,470억, `call_date` 2030-09-25)과 2025-09-25(face 1,200억, `call_date` 2030-09-01) 두 건의 **`outstanding_eok` 를 null 로 비웠고** 선택 표지 `call_date_unconfirmed: true` 를 붙였다(표지 키는 True 일 때만 있다; `face_eok` 는 그대로).
- 커밋된 K-ICS.html(`75234ddf`)의 `capsecCells()` 가 이미 잔액 null 인 콜 후보는 날짜만 그린다 -> 화면은 「콜 상환 도래일 : 2030-09-01」 (금액 괄호 없음)이 된다. 어느 시나리오에서도 가장 이른 콜일은 2030-09-01 이라 날짜는 맞다. 이전에는 「2030-09-01 (1,200억)」 이라 날짜-금액 짝이 틀릴 수 있었다.
- 부작용 확인: 이 두 건은 잔액이 null 이라 같은 함수의 「최근 발행금리」 후보(`outstanding_eok > 0`)에서 빠지지만, DB손해의 더 늦은 발행(제3~5회)이 있어 금리 값은 안 바뀐다. `scripts/check_kics_callcell.py` 는 후순위 변형으로 검사하므로 신종 DB손해 사례를 한 번 눈으로 확인해 달라(선택).
- 전망·소진율은 영향 없음(두 콜 모두 2030년).
- 공개 시트 `자본성증권발행현황` 의 두 행은 콜만기도래일을 비우고 콜근거를 「공시 원문 상충(콜일 미확정)」 으로 바꿨다(데이터 쪽 완료).

### 2. (표시 확인) 하나손해보험(KR0050) 추정 행 — 같은 파일
원장이 2025-12-31 에서 멈춰(반기보고서 없음) K-ICS 2026.2Q 항목 6 증가분(+999억, 2026-06-29 발행)이 화면에 없던 것을, 추정 행 1건으로 채웠다: `issue_date` 2026-06-29, `face_eok`·`outstanding_eok` 999.0, `coupon_pct` null, `call_date` null, 선택 표지 `estimated: true`(True 일 때만 키가 있음), `as_of` 2026-06-30.
- 효과: 총발행액 1,000억 -> 1,999억, 연도 막대에 2026 이 생김, 「최근 발행금리」 는 그 행이 가장 늦은 발행이라 null -> 「—」 로 나옴(10.66% 는 옛 발행이라 내림), 콜 상환 도래일은 기존 2029-05-14(1,000억) 그대로.
- 요청: 가능하면 `estimated` 행이 있는 회사의 막대 툴팁에 「추정(원장 미갱신)」 한 줄을 붙인다(필수 아님). 「참고 — 자본성증권 발행잔액 : 신종」 줄은 `kics_tier1_utilization.json` 의 `hybrid_outstanding_eok` 가 1,999 가 되어 따라간다.

### 3. (표시 확인) 기본자본 인정한도 숫자
`kics_tier1_utilization.json` `tier1_hybrid_limit_eok`: 결속 갈래가 없는 33사(소진율 0.0)의 값이 SCR×15% 에서 SCR×10% 로 바뀌었다(한화생명 22,517 -> 15,011, 하나손해 702 -> 468). 필드 이름·소진율 불변. 화면 줄 「기본자본 자본증권 X억원 / 인정한도 Y억원」 의 Y 만 바뀐다 - 부제(「10% 가 원칙, 15% 는 기발행분만」)와 이제 맞는다.

### 4. (표시 확인) 보완자본 「경과조치 기발행 후순위 X억원」
owner 결정(2026-10-12 밤): 보완자본 분자에서 뺀 기발행 금액 = **채권원장의 2022-12-31 이전 발행 잔액**. 화면 줄이 읽는 `kics_tier2_utilization.json` `grandfathered_subordinated_eok`(과 `grandfathered_hybrid_eok`)가 이제 이 **차감액**이고, 발행사 인쇄값은 새 필드 `grandfathered_subordinated_printed_eok`·`grandfathered_hybrid_printed_eok` 에 따로 있다. 화면 필드 이름은 그대로라 HTML 변경은 필요 없다. 숫자가 바뀐 회사(후순위): 메리츠 15,631 -> 5,960 · 한화생명 17,932 -> 14,711 · 흥국생명 4,132 -> 395 · 농협생명 8,700 -> 11,100 · 푸본 2,952 -> 3,995 · KB라이프 702 -> 1,999 · 롯데 1,934 -> 2,289 · 현대해상 0 -> 2,330 · DB손해 0 -> 1,700 · 미래에셋 2,931 -> 0 · DB생명 3,136 -> 0 · 아이엠라이프 0 -> 500 외 소액 몇 곳(전체 표 `data/_derived/capsec_reinstate_20261012/z3_tier2_before_after_47.csv`). 문구가 「경과조치 기발행 후순위」 그대로여도 맞다(2022년까지 발행분이라서).
- 소진율이 바뀐 21사는 도넛·숫자 줄이 `kics_tier2_utilization.json` 을 읽으므로 따라간다.

## 답변 (recipient 작성 — 처리 후)
