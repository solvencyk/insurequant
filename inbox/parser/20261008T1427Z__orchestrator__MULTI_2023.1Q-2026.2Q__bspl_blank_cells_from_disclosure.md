---
from: orchestrator
to: parser
created: 20261008T1427Z
status: open
route: reparse
company: MULTI
period: 2023.1Q-2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-08): "정기경영공시를 내는 회사라면 BS 전부 공란인 건 말이 안 된다 — 하나손보 2026.2Q BS 가 공란이다. 전사 전기간 채워라."
census(read-only, `data/_derived/bspl_blank_census_20261008.json`): IFRS17_BS 에서 자산·부채·자본 총계가 모두 없는 칸 25(+부분 5), PL_breakdown 에서 보험손익·투자손익·세전·법인세·순이익이 모두 없는 칸 29 (서울보증 KR0150 은 원천 부재라 제외).
하나손보(KR0050) 9칸이 최대, 예별(KR0004) PL 12칸이 두 번째. 해당 PDF 는 data/disclosure/FY*/raw/ 에 전부 있다.
방법은 기존 `scripts/extract_bs_from_disclosure.py` + `merge_bs_disclosure_parts.py` + `data/dart/viz/bs_manual_overrides.json` 경로(inbox 20260911T0109Z)를 재사용한다. PL 은 같은 §2-1/손익계산서 경로.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 workflow 결과를 모아 채운다)
