**2026-10-24 parser/ifrs17 답변 (티켓 20261023T1130Z, KB라이프 KR0099 2023.1Q 재보험 하위 항목 9·11·12)** — 적재 완료, 미커밋·미푸시. 증거 `data/_derived/remaining_20261022/e25_followups/`(색인 `INDEX.txt`, 이 회사 `kr0099_kblife/`).

| 칸 (2023.1Q, 백만원) | 옛 | 새 | 원문 (FY2024 1Q `20240516001445.xml`, 별도 주석 전분기 표 L38325, 합계 열) |
|---|---:|---:|---|
| 항목 9 재보험 CSM상각 | -1,131 | **-1,130** | L38658 제공받은 서비스의 재보험계약마진 (1,130) |
| 항목 11 재보험 예실차 | -614 | **-618** | L38560 발생 재보험금 및 재보험서비스비용회수액 478 − L38638 회수예상 보험금 및 보험서비스비용 (1,096) |
| 항목 12 기타 재보험손익 | -319 | **-316** | 8 − (9+10+11) = -2,146 − (-1,130 -82 -618) |

항목 10(-82, L38648)은 최신 열과 같아 건드리지 않았다. 항목 8(-2,146)은 불변이라 8 = 9+10+11+12 가 정확히 닫힌다(-1,130 -82 -618 -316 = -2,146).

**단일분기**: 2023.2Q 항목 9·11·12 가 -1,117 / -31 / 766 에서 **-1,118 / -27 / 763** 으로 파생됐다. 2Q 보고서(`20240814002882.xml`)의 전기 3개월 열 인쇄값(L42926 -1,118, L42894 -1,159 와 L42774 1,132 → -27, 파생 763)과 같다. 2Q·3Q 항목 9·10·11 파생 단일분기 6칸 모두 인쇄 3개월 열과 차이 0(`kr0099_kblife/k01_read_kblife.txt`). 2023.1Q 단일분기는 누계와 같다.

**방식**: `data/_gold/user_pl_cells.json` set 3칸 신규(별도 기준, was·note에 원문 줄 번호·옛 값). 박제·핀·잔차 끼움·게이트 예외 0. 3칸은 빌더 소스 값(-1,131 / -614 / -319)과 달라 마스크 칸이 아니다(`GOLD_OVERLAY_CENSUS` PL 마스크 22 불변). 출처표: 2023.1Q contract_notes 블록 raw_filing [5,6,9,10,11] → [5,6,10], owner_gold_overlay [4] → [4,9,11]; income_statement 블록 raw_filing_derived [8,12] → [8], owner_gold_overlay 에 12 추가(티켓 예상과 같다).

**독립 재독**: `x01_verify_e25.py`(표준 라이브러리만, 계획기·읽기 코드 임포트 0)가 인용 줄 4개를 다시 읽어 라벨·열 위치(6번째 = 합계)·단위·전분기 표 머리글·산식을 확인했다(문제 0, 변이 3종 모두 검출). 이 티켓분 파일 변경은 4건 공통 1회 적재의 파일 목록(INDEX.txt 1절)에 있다.

**게이트·테스트(티켓 4건 + 작업 5 합산, 적재 전 → 후; `gates/gates_compare_all.txt` · `gates/tests_final/`)**: master_tables SUMMARY 는 pl_bridge 3783P(진짜 1351 · 구성상 2089 · 부분 343)/18F/2629S/0NEW → 3787P(1351 · 2093 · 343)/18F/2625S/0NEW 한 필드뿐이다(ABL 항목 6 이 채워져 `3 = 4+5+6+7` 4버킷이 검사받기 시작; 기존 18 FAIL 목록 동일, 새 실패 0, pl_bridge_baseline 무변경). data_contract 는 RED 0 → 2 = MASTER_XLSX_DRIFT `손익분해PL` 66칸 · `CSM워터폴` 3칸으로 바뀐 칸 수와 정확히 같고(publishing 이 xlsx 동기화) YELLOW 168 은 동일하다. 연속성 flagged 1/RED 0 · 워터폴 41 pass · nb_csm 5/5 · live_artifacts RED 0 불변. 테스트: master_tables 골든은 SUMMARY 한 줄만 `--update`(사유 = 위 pl_bridge 한 필드), 입력 지문은 viz_ifrs17_panels 한 줄만 `--update`(CSM_waterfall.json 51,368,530 → 51,368,526 바이트; viz 골든 산출은 그대로 통과), PL 골든 1 passed(276초), 규칙 커버리지 105 passed + 1 failed(`test_master_xlsx_clean_state_has_no_red`, 위 xlsx 드리프트와 같은 원인), gold_overlay 10 · identity 14 · tautology 10 · viz 골든 2종 · dividend · deploy_assets 12 · push_gate_wiring 66 통과.

**남은 것**: publishing = xlsx `손익분해PL` 동기화(KB라이프 몫 9칸 = 값 3 + 단일분기 6: 2023.1Q 3 + 2023.2Q 3), panel/public_exports. 되돌리기: `e25_followups/backup_before_apply/` 의 사본을 같은 상대 경로로 복사한다(INDEX.txt 6절; `e25_apply.py --revert` 는 작업 5 가 같은 시험 파일을 바꿔 ABORT 한다).

**변경 파일(4건 공통 1회 적재 + 작업 5)**: `PL_breakdown.json` · `PL_breakdown_provenance.json` · `data/_gold/user_pl_cells.json` · `CSM_waterfall.json` · `data/_gold/user_csm_cells.json` · `scripts/build_root_masters.py` · `tests/test_rule_coverage_manifest.py` · `tests/test_gold_overlay_survives_rebuild.py` · `tests/fixtures/master_tables_golden.json` · `tests/fixtures/builder_input_fingerprints.json`. 원장(`gold_overlay_ledger.json`) 박제 변경 0, 제거한 박제 0.
