---
from: orchestrator
to: parser
created: 20261008T1427Z
status: resolved
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

## 종결 (orchestrator 2026-10-24)

BS 184칸(전부 공란 25버킷 + 일부 공란 5버킷 → 0)과 PL 126칸(전부 공란 29버킷 → 0, KR0004 2025.3Q 는 10-09 후속에서 채움)을 정기경영공시에서 적재했다(커밋 ba32077e, 2026-10-10, 실행 기록 data/disclosure/_meta/bspl_backfill_runlog_merge.md). 2026-10-24 재측정: 634개 (회사, 분기) 버킷 중 BS 전부 공란 0, PL 전부 공란 0, KR0050 2026.2Q BS 자산 2,908,500 / 부채 2,274,900 / 자본 633,600(백만원, 항등식 정확). 범위 밖이라 따로 추적: PL 항목 17/20/21 보류, 검증 결함은 티켓 20261009T0330Z · 20261009T0700Z(이 티켓과 함께 종결, 잔여는 TODO_parser_ifrs17.md).
