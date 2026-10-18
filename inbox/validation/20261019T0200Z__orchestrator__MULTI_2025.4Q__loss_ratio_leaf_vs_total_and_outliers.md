---
from: orchestrator
to: validation
created: 20261019T0200Z
status: open
route: defect
company: MULTI
period: 2025.4Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

손해율 가정 구분 선택기의 기본값을 Non-Par 로 바꾸고(2026-10-19) 비교 단위 조사(`docs/loss_ratio_comparable_unit_20261019.md`)를 하면서 나온 데이터 의문 5건. 모두 2025.4Q `data/loss_ratio/master_loss_ratio.json` 기준이고, 원문 PDF 대조가 필요한 것은 validation 몫이다.

1. **카카오페이손보 KR1098 — 잎 행 합과 공시 합계 행이 한 칸에서 14.3%p 어긋난다.** 10년 칸: 마스터 Non-Par 잎 행을 합산하면 85.7, 공시 합계 행은 100.0. 이 회사는 Non-Par 만 공시한다. 잎 행 누락(미추출)인지, 공시 합계 행 자체가 다른 범위인지 원문에서 가린다. 합계 행이 있는 회사 전부에 대해 같은 대조(잎 합 대 합계 행, 허용오차 반올림)를 돌려 어긋나는 칸을 목록화한다(기존 조사는 합계 대비 잎 합이 ±0.4% 안이라고 했으나 소규모사는 따로 확인하지 않았다).
2. **이상치 4건 원문 대조** (같은 단위의 회사 간 분산 밖에 있다):
   - 농협생명 KR0104 — Non-Par 무배당사망
   - 아이엠라이프 KR0076 — Indirect-Par 무배당사망
   - 삼성화재 KR0008 — Non-Par 무배당상해
   - 하나손보 KR0050 — Indirect-Par 무배당질병
   각 건에서 원문 표의 값(위험보험료 · 예상보험금 · 손해율)과 마스터가 같은지, 단위(억원/백만원)가 맞는지 본다.

## 수용 기준

- 1번: 원인(추출 누락 / 공시 자체 불일치 / 범위 차이)과 해당 칸 목록, 고칠 것은 parser-ifrs17 inbox 로 route.
- 2번: 4건 각각 일치 여부와 근거 페이지.

## 현황 (receiver 작성)
