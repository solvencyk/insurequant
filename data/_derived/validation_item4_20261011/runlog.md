# validation 23차 런로그 -- PL 항목 4 주석 계보 허용 + owner 승인 등재 4칸 (2026-10-11)

티켓 `inbox/validation/20261011T2000Z__orchestrator__MULTI_2023.4Q-2026.2Q__item4_note_lineage_and_approved_registrations.md` (공유 티켓은 고치지 않음).
작업 파일·전후 출력: `data/_derived/validation_item4_20261011/` (dc_/mt_ before·after, sim_item4_lineage*, diff_dc.py, 등재 스크립트).
모델 Sonnet 5.5. 마스터 JSON 셀·xlsx·public_exports·HTML 무수정, `build_root_masters.py` 미실행, `validate_master_tables.py --no-build`, 골든 `--update` 없음.

## 전후 (PL 범위만 해석; CSM 계열 변동은 해석 안 함 -- 동시 세션이 CSM_waterfall·CSM_amortization·라이나 적재 진행 중)

| 항목 | 전 | 후 |
|---|---|---|
| 데이터계약 RED | 34 | 11 |
| 데이터계약 YELLOW | 143 | 147 (+4: 법인세 확정 3 + 하노버 원천부재 1, 전부 매 실행 인쇄) |
| §3d CONCEPT_MIXED_DISCLOSURE_INTO_DART | 20 | 0 |
| PL_YTD_COLLAPSE_TO_ZERO | 3 | 0 (YELLOW PL_YTD_COLLAPSE_OWNER_CONFIRMED 3) |
| PL MASTER_HOLE (하노버 2025.3Q) | 1 | 0 (YELLOW MASTER_HOLE_SOURCE_ABSENT 1) |
| master_tables ZERO_LEGS / src_na zleg / legcov | 23 / 181 / 269 | 9 / 195 / 269 |
| master_tables coverage_hole PL | 3 | 2 (서울보증 2024.2Q·2024.3Q 통째, 이번 티켓 범위 밖) |
| master_tables 신규 SUMMARY 토큰 | - | pl_src_absent:1ok/0red |
| 새 RED (PL 범위) | - | 0 |
| (범위 밖) master_tables.xlsx MASTER_XLSX_DRIFT CSM상각 | 0 | +1 (CSM_amortization.json 동시 수정) |

## 시뮬레이션 (수정 전, 전수)
`sim_item4_lineage_out.txt`: §3d 현행 RED 20 -> 제안 0 (닫힘 20 = 항목 [4], 새로 깨짐 0). ZERO_LEGS 현행 23 -> 제안 9 (닫힘 14, 새로 깨짐 0).
사이드카 how 분포에서 fs_note_csm_amort 는 정확히 20블록(contract_notes)이고, 항목 4 를 가진 DISCLOSURE 계보 contract_notes 블록 중 이 how 가 없는 것은 0.

## 변이시험
selftest 75 -> 92 (Q9 8 · Q10 5 · S7-S10 4). pytest 신규 37 (`tests/test_pl_fs_note_lineage.py` 12 · `tests/test_pl_source_absent_exemption.py` 24 · `tests/test_data_contract_selftest.py` 1) + `test_pl_ytd_collapse_owner_confirmed.py` 범위 pin/재확인 2.
전부 훅 번들(`scripts/prepush_check.py`)에 편입. 발견: `--selftest` 는 UH-4 이후 훅이 한 번도 안 돌렸다(호출처 0) -- 래퍼 테스트로 닫음.

## 움직이는 골든
`tests/test_master_tables_golden.py` 1종 (SUMMARY: `coverage_hole 3PL->2PL`, `pl_src_absent` 토큰 신설. zero_legs 9 / src_na 195 는 골든값으로 복귀. 같은 골든의 closing 381->390 · identity · qoq 이동은 라이나 CSM 적재분).
kics 룰 골든 · post_transition · 입력 지문(pl_breakdown ok) 불변. 지문 게이트 RED 3 = viz_ifrs17_panels (동시 세션의 csm_amort_schedule.json / viz_build_ifrs17_panels.py).
