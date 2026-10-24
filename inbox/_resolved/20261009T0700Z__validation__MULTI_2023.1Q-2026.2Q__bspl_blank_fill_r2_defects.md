---
from: validation
to: parser
lane: ifrs17
created: 20261009T0700Z
status: resolved
date: 2026-10-09
re: 20261008T1427Z bspl_blank_cells_from_disclosure (round 2)
---
# BS/PL blank fill, validation round 2 defects

Evidence and reproduction: data/disclosure/_meta/bspl_backfill_runlog_validation_r2.md

1. V2-1 (blocks push): KR0004 2025.3Q PL cells 1/22/23/24 hold the stub period 2025-06-16~09-30 (FY2025_Q3 PDF p25-26), not a 1/1-based YTD. Remove them from PL_breakdown (back to blank with reason) or get an owner-approved stub-period rule that also changes the YTD checks; make pl_from_disclosure_merge excluded and the master agree either way. Current state creates RED PL_YTD_COLLAPSE_TO_ZERO.
2. V2-2: record a per-cell reason for 22 blank cells: KR0004 item 16 (12 quarters), KR0008 item 1 and 16 2023.2Q, KR0032 item 16 2023.2Q, item 21 for KR0009/0069/0073/0099/0104/1000 2023.1Q-2Q.
3. V2-3: KR0004 2024.4Q and 2025.4Q item 2 (PL hole) needs the Tier-2 handler fix; do not fill by residual.
4. After 1: ask validation to regenerate tests/fixtures master_tables golden (do not --update before).

Answer: (parser fills in)

## 종결 (orchestrator 2026-10-24)

V2-1(KR0004 2025.3Q 구간 셀)은 owner 결정 2026-10-10 「유지 + 셀 등재」로 닫혔다(PL_YTD_COLLAPSE_OWNER_CONFIRMED, data contract YELLOW 비차단). V2-4 골든 재생성 완료(changelog_validation 20·32·33차). V2-2 중 아직 공란인 5칸의 사유와 V2-3 핸들러(extract_tier2_yebyeol)는 TODO_parser_ifrs17.md 로 옮기고 종결한다(2026-10-24).
