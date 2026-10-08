---
from: orchestrator
to: parser
created: 20261007T1300Z
status: open
route: backlog
company: KR0076 · KR0051 · KR1000
period: 2024.4Q · 2025.2Q · 2023.4Q
rule: MI_COLUMN_SHIFT
lane: kics
iter: 1
---

## 미결 (sender 작성)

채널별 유지율 작업에서 채널 합을 루트 `management_indicators.json`(1-2 주요 경영효율 지표)과 대조하다가 발견했다.
아래 3개 (회사, 분기)는 1-2 표 **행 전체가 엉뚱한 열·행에서 읽혔다**. 계약유지율이 음수이거나 100 을 넘고, 같은 행의 다른 항목도 말이 안 된다.
`management_indicators.json` 은 `main` 에 없어 라이브 영향은 없다.

| 회사 | 분기 | 증상(현재 값) |
|---|---|---|
| KR0076 아이엠라이프 | 2024.4Q | 계약유지율 13~85회차 = △1.27 · 3.42 · △10.03 · △3.54 · △1.47 · 1.46 · △0.48(증감 열로 보임), 지급여력비율 △74, ROA 58.58 |
| KR0051 신한이지손해 | 2025.2Q | 37·49·61회차 = △79.8 · △45.0 · △55.6, 자본 3,760 > 자산 1,809, 지급여력비율_경과조치전 △157 |
| KR1000 코리안리 | 2023.4Q | 계약유지율_13회차 = 183.22(= 지급여력비율 값), 자산 2.5 · 부채 △0.38 |

### 할 일
1. `scripts/extract_management_indicators.py` 가 이 3건에서 열(당기/전기/증감)·행을 어떻게 잘못 짚었는지 원문 PDF(p4 근처 1-2 표)로 확인하고 고친다. 셀 단위 + guard 로 쓴다(통째 read-modify-write 금지).
2. 같은 원인으로 **값이 그럴듯해서 안 걸린** 칸이 더 있는지 전수로 본다. 최소한 이 대조를 쓴다:
   계약유지율 n회차 ↔ `data/persistency/persistency_channel.json` 의 채널 합(Σ유지계약액 ÷ Σ대상신계약액, `data/persistency/selfcheck.csv` 의 `COMPANY_SUM` 행) — 대부분 |차이| ≤ 0.01 이므로 0.5%p 넘는 87건이 후보다(채널 표 쪽 오류일 수도 있으니 원문으로 판정).
3. 결과는 이 티켓 `## 답변` 에 (회사, 분기, 항목, 이전 값 → 새 값, 원문 쪽). 루트 마스터 수정이므로 validation 재검을 거친다.

## 답변 (recipient 작성 — 처리 후)
