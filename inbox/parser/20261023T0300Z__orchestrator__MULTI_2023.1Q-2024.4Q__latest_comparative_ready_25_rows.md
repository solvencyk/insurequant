---
from: orchestrator
to: parser
created: 20261023T0300Z
status: open
route: reparse
lane: ifrs17
company: MULTI (KR0104 KR0083 KR0070 KR0079 KR0010 KR0099 KR0003 KR0001 KR0068)
period: 2023.1Q-2024.4Q
iter: 1
---

## 미결 (sender 작성)

owner 지시(2026-10-22 밤, 「쭉 진행해라」)의 두 번째 적재다. 앞 티켓(`inbox/_resolved/20261022T1800Z…held_and_remaining.md`)의 단계 2 측정이 끝났고 결과는 `data/_derived/remaining_20261022/e20_held_and_remaining/measure/PLAN.md`(계획표 `plan_table.csv`, 칸 단위 후보 `ready_cells_ALL.csv`, CSM `ready_csm_cells.csv`, gold 교체 `gold_cells_replaced.csv`)에 있다. **READY 25행(PL 471칸 + CSM 55칸)을 적재한다.** NEEDS_OWNER 21행(KB라이프 8버킷 D1 · 롯데 2023.4Q D2 · ABL/KDB/현대해상 FY2023 D3)은 owner 결정 전이라 **건드리지 않는다**(현대해상 IR 레그, WFY 면제 등재, 연쇄용 gold 교체 포함).

### 적재 대상 (PLAN.md 1절 계획표 순위 1~10, 7.5 포함)
농협생명 KR0104 2023.1Q·2Q(48칸, 구양식 손익계산서 미독해 · provenance income_statement DISCLOSURE→OWNER_GOLD 교체 필수) · 푸본현대 KR0083 2024.4Q(PL 10 · 앞 티켓에서 비운 단일분기 8칸이 이 적재로 복원돼야 함) · ABL KR0070 2024.4Q(OCI 3) · 미래에셋 KR0079 2023.4Q(PL 11 · 단일분기 이음매 null_dangi 11) · KB손해보험 KR0010 2023.1Q·2Q·4Q, 2024.1Q~3Q(114칸) · KB라이프 KR0099 2024.1Q(마스터 오류 3칸 `abs()` 부호; 최신 비교열 문제와 독립) · 롯데손보 KR0003 2023.1Q·2Q, 2024.1Q~3Q(PL 133 + CSM 17 + PL4) · 미래에셋 KR0079 2024.1Q~3Q(PL 41 + CSM 11) · 메리츠화재 KR0001 2023.1Q·2Q(PL 59 + CSM 12) · 한화생명 KR0068 2023.1Q~3Q(PL 49 + CSM 15). 시나리오 `READY_all` 합계 PL 471 + CSM 55.

### 원칙 (앞 티켓과 같다)
- 최신 비교열 우선 · 별도(OFS) 기준 · 블록이 닫힐 때만 · 박제·잔차 끼워 맞추기·게이트 예외 등재 없음. owner gold 칸은 gold 값 = 원 공시 인쇄값(ⓐ)일 때만 최신 값으로 교체하고 `was`·note 에 줄 번호를 남긴다. ⓑ(원 인쇄값도 최신 값도 아닌 값)는 건드리지 않고 그 버킷을 보류해 보고한다. `gold_cells_replaced.csv` 31칸 중 READY 몫은 전부 ⓐ 로 측정됐지만 **적재 직전에 칸마다 다시 분류**한다. KB손보 2024.2Q 항목 16(192,135→192,136, 1백만원 재인쇄 차이)은 반올림 규칙에 따라 제외한다. 반올림만 다른 칸·새 마스크 칸·새 박제는 만들지 않는다.
- **적재 전 필링 XML 줄 번호로 전 칸 독립 재독**(값·단위·부호·행 라벨·열). PLAN.md 가 적은 줄 번호와 독립 리더 결과를 믿고 넘어가지 말고 `e20_verify_plans.py`(`data/_derived/remaining_20261022/e20_held_and_remaining/apply/`)와 같은 방식의 별도 코드로 다시 읽는다. 앞 티켓의 적재 도구 `apply/e20_apply.py`·`e19_*.py`·CSM 쪽 `a_oci/apply_kr0073_oci.py` 와 17차 `scripts/apply_kr0073_bs_ilp_restated_20261022.py` 를 재사용하되 CSM 은 `data/_gold/user_csm_cells.json` 셀 단위 set 으로 영속화한다.
- 영속 경로: PL 은 `data/_gold/user_pl_cells.json`(이음매는 `set_dangi`/`null_dangi`), CSM 은 `user_csm_cells.json`. 실제 `build_pl()`/CSM 빌더 사본을 옛 gold/새 gold 로 두 번 돌려 **달라진 칸만 셀 단위로 마스터에 반영**한다(마스터 통째 쓰기 금지). 출처표는 `scripts/emit_pl_provenance.py` 의 **샌드박스 사본**으로(import 금지) 만든다: 농협생명 income_statement 블록 교체, **롯데 2023.1Q contract_notes 블록 신규**(없으면 MISSING_PROVENANCE · SOURCE_ID_LINEAGE_MISMATCH RED 2). `GOLD_OVERLAY_CENSUS` PL·CSM 튜플을 바뀐 gold 칸 수에 맞게 갱신(푸시 훅 필수).
- 인접 분기가 옛 판으로 남아 단일분기가 두 판에 걸치면 3개월 열 인쇄값이 있으면 `set_dangi`, 없으면 `null_dangi`.
- 리더(핸들러) 코드: gold 로 영속화하는 경로면 PL 골든 영향이 없다. `extract_tier2_kblife` 의 `_jang_rerev = abs(jrr)`(3347행 근처) 결함은 **고치되**, `RUN_PL_GOLDEN=1 tests/test_pl_breakdown_golden.py` 로 바뀌는 셀이 KB라이프 2024.1Q 3칸(2·8·12) 뿐이면 골든 `--update`(이유를 커밋 메모에 남김), 더 바뀌면 코드는 되돌리고 gold 로만 적재한 뒤 사실을 보고한다. 나머지 리더 변경(KB손보·롯데·메리츠 전기 표, OLD 생보 PL4, 푸본·미래에셋 CSM 전기열 라벨러)은 PLAN.md 6절의 프로토타입을 근거 자료로 TODO 에 남기고, 이번에는 마스터·gold 적재만 한다(이미 같은 필링으로 재현 검증됨).
- 이번에 하지 않는 것(오케스트레이터가 다음 단계에서): `data/_gold/pl_bridge_baseline.json` 해소 5줄·`WFY_EXCEPTIONS` 불용 항목·`pl_csm_amort_missing_ledger.json` 롯데 2023.1Q 줄 정리(validation 몫), `NB_CSM_multiple` 4행(메리츠 2023.1Q·2Q, 한화 2023.1Q·2Q) 재빌드와 xlsx/패널/public_exports(publishing 몫). 단 `NB_VS_WATERFALL` RED 4 와 `PUBLIC_EXPORT_DRIFT`, xlsx 동기화 RED 2 가 적재 직후 게이트에 나오는 것은 예상된 값이다 — 그 밖의 새 RED/FAIL 은 적재하지 말고 원인을 적는다.
- 게이트 전후: `validate_master_tables --no-build` · `validate_data_contract` · `validate_csm_continuity` · 워터폴/NB/live_artifacts, 테스트 `RUN_PL_GOLDEN=1`(위 규칙) · `test_rule_coverage_manifest` · gold_overlay · identity · `test_master_tables_golden`(SUMMARY 지문이 pl_bridge 합계를 포함하므로 의도된 이동이면 `--update` + 사유). 기대 결과(PLAN.md): pl_bridge 3697P/FAIL 23 → 3755P/FAIL 18, NEW 0.
- 화면 숫자가 크게 움직이는 곳(메리츠 2023.1Q/2Q CSM 기말 −3.6% · 한화생명 2023.1Q/2Q 당기순이익 +32%/+21% · 롯데 2023.1Q CSM 기말 +507억)은 owner 규칙으로 허용되는 변경이지만 답변에 회사·분기별 전→후 표(억원)로 적는다.
- **커밋·push 금지**. python 은 풀패스 + 스크립트 파일 + stdin `/dev/null`. 메모리가 빠듯해 무거운 게이트는 한 번에 하나. 증거는 `data/_derived/remaining_20261022/e21_ready25/` 에 새로 만든다. 끝나면 TODO_parser_ifrs17.md 맨 위(항목당 5줄)와 changelog 를 갱신하고 이 티켓 `## 답변` 을 채운다.

## 답변 (recipient 작성 — 처리 후)

(처리 전)
