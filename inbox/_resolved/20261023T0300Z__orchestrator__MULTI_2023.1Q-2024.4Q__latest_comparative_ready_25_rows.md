---
from: orchestrator
to: parser
created: 20261023T0300Z
status: resolved
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

처리: parser-ifrs17 레인(단독 리더), 2026-10-23. 상태는 `open` 으로 둔다(오케스트레이터 재확인 대기). 커밋·push 안 함. 서브에이전트·docling 안 씀(중복 기동된 두 번째 에이전트는 오케스트레이터가 중단시켰고 흔적 `e21_ready25/second_agent/` 는 증거로 남김). 증거·재현 폴더 `data/_derived/remaining_20261022/e21_ready25/`(`INDEX.txt` 에 파일 지도·재현 순서·되돌림 순서).

### 1. 결과
시나리오 `READY_all` 을 적재했다: **PL 440칸 + CSM 55칸**(PL 후보 471칸 중 31칸은 규칙에 따라 제외, 아래 5절). NEEDS_OWNER 21행(KB라이프 8버킷 D1 · 롯데 2023.4Q D2 · ABL/KDB/현대해상 FY2023 D3) · 현대해상 IR 레그 · WFY 면제 · 연쇄용 gold 교체 · `pl_bridge_baseline.json` · `WFY_EXCEPTIONS` · `pl_csm_amort_missing_ledger.json` · `NB_CSM_multiple` · xlsx/panel/public_exports 는 건드리지 않았다. 게이트는 티켓이 예상한 것 말고 새 RED/FAIL 이 없다(6절).

### 2. 적재 내역 (git HEAD 대비 실측, `e21_diff_vs_head.txt` 49 PASS / ALL PASS)
| 파일 | 변경 |
|---|---|
| `PL_breakdown.json` | 9사 값 440칸 + 값_당분기 605칸(단일분기만 바뀐 166). 회사별 값: 농협생명 48 · 푸본현대 10 · ABL 3 · 미래에셋 52 · KB손보 106 · KB라이프 3 · 롯데 114 · 메리츠 58 · 한화생명 46 |
| `CSM_waterfall.json` | 4사 12버킷 값 55칸 + 값_당분기 77칸(롯데 17 · 미래에셋 11 · 메리츠 12 · 한화생명 15) |
| `data/_gold/user_pl_cells.json` | set 741→1171(신규 430 + 제자리 교체 7) · null_dangi 76→98(+30 −8) · set_dangi 40→37(+1 −4) |
| `data/_gold/user_csm_cells.json` | set 317→370(신규 53 + 제자리 교체 2) |
| `data/_gold/gold_overlay_ledger.json` | 박제 3건 제거(교체한 마스크 칸 PL\|KR0010\|2023.1Q\|16, PL\|KR0010\|2023.2Q\|16, PL\|KR0068\|2023.1Q\|20), **새 박제 0** |
| `PL_breakdown_provenance.json` | 42블록 교체(샌드박스 `emit_pl_provenance` 사본 출력): 농협생명 2023.1Q·2Q income_statement DISCLOSURE→OWNER_GOLD(4→24칸), 롯데 2023.1Q contract_notes `NO_PUBLISHED_VALUE_IN_BLOCK`→OWNER_GOLD(8/8칸; 블록은 이미 있었으므로 신규 삽입 아님) + 병합 노트 키 2개 |
| `CSM_waterfall_provenance.json` | 11블록 `owner_override` + 병합 노트 키 |
| `tests/test_rule_coverage_manifest.py` | `GOLD_OVERLAY_CENSUS` = CSM (317,77)→(370,77), PL (741,25)→(1171,22) · `_TAX22_LATEST_COMPARATIVE_ONLY` 23→33칸(교보 4 + 다른 9사 29) |
| `scripts/pl_breakdown/companies.py` | `extract_tier2_kblife` 3347행 `abs(jrr)`→`jrr`(1줄 + 주석 2줄) |
| `data/dart/viz/pl_breakdown_master.json` | KR0099 2024.1Q 항목 2·8·12 3칸만(빌더 소스, 6절 KB라이프) |
| `tests/fixtures/pl_breakdown_golden.json` · `master_tables_golden.json` · `builder_input_fingerprints.json` | `--update` 3건(사유 6절: KB라이프 3칸 · SUMMARY 4필드 이동 · 입력 해시) |
| `data/_derived/qoq_warn.json` · `pl_oci_vs_bs_aoci_warn.json` | master_tables 골든 테스트가 쓰는 부수 산출(이전 라운드와 같은 선례) |

### 3. 회사·분기별 전→후 (억원, 누계; 전체표 `e21_apply_report.txt`)
화면 숫자가 크게 움직이는 곳:
| 회사 | 분기 | 항목 | 전 | 후 | 차이 |
|---|---|---|---:|---:|---:|
| 메리츠화재 | 2023.1Q | CSM 기말 | 100,033.5 | 96,454.4 | −3,579.1 (−3.6%) |
| 메리츠화재 | 2023.2Q | CSM 기말 | 100,684.2 | 97,015.4 | −3,668.8 (−3.6%) |
| 메리츠화재 | 2023.1Q / 2Q | 당기순이익 | 4,057.15 / 8,383.58 | 3,965.26 / 8,160.04 | −91.9 / −223.5 |
| 한화생명 | 2023.1Q | 당기순이익 | 3,569.26 | 4,709.12 | +1,139.9 (+31.9%) |
| 한화생명 | 2023.2Q | 당기순이익 | 5,133.29 | 6,186.96 | +1,053.7 (+20.5%) |
| 한화생명 | 2023.1Q / 2Q / 3Q | CSM 기말 | 97,125.1 / 101,167.4 / 97,991.1 | 98,791.1 / 101,226.9 / 97,991.2 | +1,666.0 / +59.5 / +0.1 |
| 롯데손보 | 2023.1Q | CSM 기말 | 17,427.53 | 17,934.87 | +507.34 (+2.9%) |

그 밖의 버킷(보험손익 / 투자손익 / 당기순이익, 전→후):
| 회사 | 분기 | 보험손익 | 투자손익 | 당기순이익 | CSM 기말 |
|---|---|---|---|---|---|
| 농협생명 | 2023.1Q | 공란→986.12 | 공란→842.73 | 1,146.00→1,076.71 | |
| 농협생명 | 2023.2Q | 공란→1,916.60 | 공란→352.63 | 1,415.00→1,457.66 | |
| 푸본현대 | 2024.4Q | 불변 | 148.11→35.66 | −340.44→−426.91 | |
| ABL | 2024.4Q | | | 불변 (OCI −5,073.59→−5,071.08) | |
| 미래에셋 | 2023.4Q | | −22.29→−226.24 | 1,250.00→1,092.00 | |
| 미래에셋 | 2024.1Q | 214.92→222.98 | 285.74→211.58 | 394.35→323.23 | 20,916.3→20,925.2 |
| 미래에셋 | 2024.2Q | 671.99→680.16 | 22.75→−96.63 | 586.50→463.35 | 20,894.5→20,903.2 |
| 미래에셋 | 2024.3Q | 983.44→994.20 | −229.44→−376.31 | 621.71→473.82 | 20,645.6→20,654.1 |
| KB손보 | 2023.1Q | 2,588.81→2,489.07 | 957.10→1,056.31 | 2,632.26→2,642.85 | |
| KB손보 | 2023.2Q | 5,538.23→5,290.83 | 1,765.08→2,086.50 | 5,389.17→5,462.20 | |
| KB손보 | 2023.4Q | 8,329.22→8,319.79 | 2,105.20→1,577.18 | 7,763.86→7,367.66 | |
| KB손보 | 2024.1Q | 3,666.14→3,683.80 | 356.64→306.81 | 2,983.02→2,959.34 | |
| KB손보 | 2024.2Q | 6,881.66→6,960.31 | 1,082.06→996.27 | 5,890.93→5,885.67 | |
| KB손보 | 2024.3Q | 8,756.48→8,854.43 | 1,539.71→1,444.14 | 7,588.58→7,590.33 | |
| 롯데손보 | 2023.1Q | 공란→222.26 | 공란→538.34 | 793.75→564.12 | |
| 롯데손보 | 2023.2Q | 1,028.98→678.03 | 495.59→404.02 | 1,129.72→813.24 | |
| 롯데손보 | 2024.1Q | 413.61→369.91 | 97.87→52.10 | 408.67→339.87 | 24,305.8→24,192.5 |
| 롯데손보 | 2024.2Q | 837.92→750.45 | 1.71→−27.19 | 662.55→573.06 | 24,598.0→24,476.6 |
| 롯데손보 | 2024.3Q | 1,132.48→1,000.58 | −54.24→−108.68 | 844.14→697.19 | 24,529.9→24,400.9 |
| 한화생명 | 2023.1Q | 1,523.73→1,722.03 | 공란→4,304.44 | (위 표) | (위 표) |
| 한화생명 | 2023.2Q | 3,967.56→3,919.35 | 공란→3,490.90 | (위 표) | (위 표) |
| 메리츠화재 | 2023.1Q | 4,195.37→4,009.89 | 1,371.83→1,426.09 | (위 표) | (위 표) |
| 메리츠화재 | 2023.2Q | 8,226.07→7,793.02 | 3,111.91→3,229.31 | (위 표) | (위 표) |
KB라이프 2024.1Q 는 항목 2·8·12(백만원) 85,633→84,497 · −832→−1,968 · −24→−1,160 (이 3칸의 보험손익 가교 FAIL +1,136 이 닫힘). 기타포괄손익·총포괄손익도 버킷마다 움직였다(`e21_apply_report.txt`).

### 4. owner gold 처리 (적재 직전 칸마다 재분류, ⓑ 0칸)
| 칸 | 옛 gold | 원 공시 인쇄값(별도 기준) | 새 값(최신 비교열) | 분류 |
|---|---:|---|---:|---|
| 롯데 2023.2Q 항목 19 | −71,316.307049 | 같음 (L6944) | −80,474.009144 | ⓐ |
| 한화생명 2023.1Q 항목 20 | 375,708.317423 | 같음 (L52688) | 602,647.143874 | ⓐ |
| 한화생명 2023.2Q 항목 21 | 189,467.309969 | 같음 (L62620 − L62629) | 9,851.919348 | ⓐ |
| KB손보 2023.1Q 항목 16 | 92,565 (연결 인쇄 L6171) | 91,710 (별도 L26886) | 91,710 | A_basis |
| KB손보 2023.2Q 항목 16 | 190,719 (연결 L7649) | 189,068 (별도 L29851) | 189,068 | A_basis |
| 메리츠 2023.1Q 항목 16 | −12,370.224177 (연결 L5994) | −11,048.069618 (별도 L27754) | −11,048.069618 | A_basis |
| 메리츠 2023.2Q 항목 16 | 71,546.566619 (연결 L9430) | 73,064.945045 (별도 L32739) | 73,064.945045 | A_basis |
| 롯데 CSM 2023.1Q 항목 4 | −681.62 | 원 공시에 CSM 표 없음 | −174.28 | class C |
| 롯데 CSM 2023.1Q 항목 6(기말) | 17,427.53 (= L15978 총 부채 기준 소계 1,742,753) | 원 공시에 CSM 표 없음 | 17,934.87 (L15956 기말순보험계약부채 1,793,487) | class C |
옛 값은 `was`, 줄 번호는 note/why 에 있다. KB손보 2024.2Q 항목 16(192,135→192,136, 1백만원 재인쇄 차이)은 티켓대로 제외했다. **편차(해석 확장 6칸)**: A_basis 4칸은 gold 가 「원 공시 인쇄값」이긴 하나 연결 기준이었다(별도 원 인쇄값이 최신 비교열과 같으므로 재작성이 아니라 기준 오류 정정). KB손보 2023.1Q 의 옛 Tier-1 보험손익 258,881(L6095)도 연결 값이었고 별도 원 인쇄값 248,907(L26810)이 최신 비교열이다. 롯데 CSM 2칸(class C)은 원 인쇄값이 존재하지 않아 ⓐ 의 정의에 정확히 들어맞지 않는다(옛 gold 는 같은 전기 표의 다른 줄 + 그 기말에 맞춘 닫힘 플러그). 원칙에 어긋난다고 보시면 이 6칸만 되돌릴 수 있다(`e21_apply.py --revert --apply` 는 전체, 부분은 gold 의 `was` 값).

### 5. 싣지 않은 PL 31칸
| 사유 | 칸 |
|---|---|
| 반올림만 다름·마스터와 같음·최종 레그로 재계산한 잔차가 같음 30 | KB손보 2023.2Q 항목 8·10·11·12 · 2023.4Q 항목 30·32 · 2024.2Q 항목 16(티켓 제외) · 롯데 2024.1Q 항목 11·13 · 2024.2Q 항목 5·16·18·21·28·29·30·32 · 2024.3Q 항목 11·13·16·18·21·28·29·30·32 · 메리츠 2023.2Q 항목 14 · 한화생명 2023.2Q 항목 16 · 2023.3Q 항목 4·7 |
| 마스크 칸이 되어 박제가 필요(새 박제 금지) 1 | KB손보 2024.3Q 항목 16 = 284,474. 마스터는 이전과 같이 공란이다: 빌더 소스는 284,474 이지만 `_zero_other_expense`(보험손익이 항목 16 없이 닫히면 null)가 지우고, 이웃 분기(2023.1Q~2024.2Q)는 owner gold 가 이 규칙을 덮어 값이 있다. 값을 채우려면 박제 허용이 필요하다(owner/validation 결정) |
측정 후보와 다르게 읽은 11칸은 PL4 정밀 인쇄값·반올림 보정이다(`e21_plan_report.txt` A절).

### 6. 이음매(단일분기)와 게이트·테스트
**이음매**: 건드린 단일분기 칸 440개를 분류했다(`e21_plan_report.txt` 이음매 표) — Q2/Q3 Tier-1 항목이 후속 공시 3개월 열 인쇄값과 일치 239 · Q4 연간·9개월 비교열이 둘 다 새 판이라 파생 유지 9 · 한쪽 누계가 공란이라 단일분기를 만들 수 없는 칸 12 · Q2/Q3 LOB 노트 항목(3개월 열 직접 대조 불가, 같은 버킷 Tier-1 3개월 열 일치로 대리 확인) 103 · Q4 는 그대로 두고 Q3 만 채택(Q4 인쇄가 이미 새 판과 같음을 확인) 46 · 3개월 열 인쇄값과 어긋나 `set_dangi` 1 · Q4 연간 비교열만 새 판(9개월은 옛 판)이라 `null_dangi` 30. 결과: `null_dangi` +30(KB손보 2023.4Q 15 · 미래에셋 2023.4Q 11 · ABL 2024.4Q 항목 26·31 · 푸본현대 2024.4Q 항목 26·31) · 푸본현대 2024.4Q 핀 8칸 제거(앞 티켓에서 비운 단일분기 8칸 복원) · `set_dangi` +1(농협생명 2023.3Q 항목 32 = 278.925315) −4(빌더 차분과 같아진 항목 16·22·23·24, 값 동일). 기존 공란 1칸(롯데 2023.3Q 항목 16)이 후속 공시 3개월 열 인쇄값과 같은 파생값 10,382.555472 로 채워졌다.

**KB라이프 `abs()` 결함**: 3347행 `out["_jang_rerev"] = abs(jrr)` → `jrr`(재보험수익은 음수일 수 있다; 2024.1Q (568)이 +568 로 뒤집혀 항목 8 −832). 고친 코드로 `build_pl_breakdown.py` 를 돌려 비교(`e21_klife_fix.py`): 바뀐 셀은 `pl_breakdown_master.json` 의 KR0099 2024.1Q 항목 2·8·12 **3칸뿐**(커버리지 파일 동일) → 티켓 규칙대로 골든 `--update`(`sha256_master` f9c841fd…→b7137dab…, 한 필드). 빌더 소스가 같은 값을 내게 되어 gold 로 적재했던 3칸은 마스크가 되므로(새 박제 금지) `e21_post_klife.py` 로 gold 에서 제거했고 마스터 3칸은 새 빌드가 그대로 만든다.

**게이트 전→후** (`gates_before/` · `gates_final/`, 둘 다 이 PC 에서 한 번에 하나씩):
| 게이트 | 전 | 후 | 티켓 기대 |
|---|---|---|---|
| `validate_master_tables --no-build` SUMMARY | pl_bridge 3697P(진짜1300)/23F/0NEW · csm_amort_identity 387P/5S · qoq_warn 262Y · oci_vs_bs_aoci 21Y | pl_bridge 3755P(진짜1333)/18F/0NEW · 388P/4S · 263Y · 26Y(YELLOW) | pl_bridge 3697P/23F → 3755P/18F NEW 0: 일치 |
| `validate_data_contract` | RED 0 · YELLOW 169 | RED 2(MASTER_XLSX_DRIFT `CSM워터폴` 132칸 · `손익분해PL` 1,045칸) · YELLOW 169 | xlsx 동기화 RED 2: 일치 |
| `validate_live_artifacts` | RED 0 · 기준선 YELLOW 25 | RED 4(NB_VS_WATERFALL KR0001·KR0068 2023.1Q·2Q) | NB_VS_WATERFALL RED 4: 일치 |
| `validate_csm_continuity` | 44사 flagged 2 · RED 0 | flagged 1 · RED 0 | |
| `validate_csm_waterfall` / `validate_nb_csm` | pass 41 fail 0 / 5 pass | 동일 | |
| `PUBLIC_EXPORT_DRIFT` | | **안 나옴** | 이 게이트는 커밋된 HEAD 마스터와 스냅샷을 비교하므로 미커밋 상태에서는 나오지 않는다. 커밋 뒤에 예상대로 나온다(`validate_live_artifacts.py` 의 `read_committed_json`) |
xlsx 드리프트 칸 수(132 / 1,045)는 이번에 바뀐 칸 수(CSM 55+77 / PL 440+605)와 정확히 같다 = 동기화 지연뿐. pl_bridge 에서 사라진 FAIL 5건: KB라이프 2024.1Q 보험손익(dual) · 롯데 2023.2Q · 한화생명 2023.1Q·2Q (leg-coverage) · 메리츠 2023.2Q(dual).
**테스트**: `RUN_PL_GOLDEN=1 tests/test_pl_breakdown_golden.py` 통과(263초, fixture 갱신 뒤) · `test_gold_overlay_survives_rebuild` 7 passed · `test_identity_registry` 14 passed · `test_master_tables_golden` 통과(SUMMARY 4필드 이동으로 `--update`, 사유 = 위 표) · `test_viz_ifrs17_panels_golden`·`test_viz_csm_waterfall_golden` 통과(패널 산출 불변) · `test_rule_coverage_manifest` 103 passed / 1 failed(`test_master_xlsx_clean_state_has_no_red` = 같은 xlsx RED 2; 적재 전 104 passed) · `validate_golden_input_fingerprints.py` RED 3(pl_breakdown CODE_MOVED·FIXTURE_MOVED, viz_ifrs17_panels INPUTS_MOVED = `CSM_waterfall.json` 해시) → 위 골든이 전부 통과한 뒤 `--update`(6줄) → RED 0.

### 7. 독립 재독·검증
- 적재 전 필링 XML 물리 줄 재독: 계획기(`e21_plan_*.py`, 자체 판독기)와 별개의 `e21_verify.py`(계획기 코드를 import 하지 않는 정규식 판독)가 PL 440칸 전부의 인용 줄에서 값 · 부호 · 단위 · 표 구분(별도/연결 `<TITLE>`) · 행 라벨 · 열 위치 · ACONTEXT · 이전 마스터값(git HEAD)을 다시 읽었다: problems 0. 합성 벡터 항등식 잔차 최대 1.0 백만원.
- 적재 뒤: `e21_apply.py --verify`(실제 `build_pl()`/CSM 빌더 사본이 새 gold 로 만든 값 = 마스터: PL 440 · 단일분기 31 · CSM 55 일치, 새 드리프트 0; 종료코드 2 는 대상 9사 출처표 12블록이 적재 전부터 emitter 와 달랐기 때문이며 HEAD 16 → 12, 새로 어긋난 블록 0: `e21_prov_check.txt`) · `e21_diff_vs_head.py`(HEAD 대비 칸 단위 차분 49 PASS: 바뀐 필드는 값·값_당분기뿐, 계획 밖 행 0, gold 교체는 값·was·note 만) · 마스터 통째 쓰기 없음(셀 단위 반영, 행 수·순서 동일).

### 8. 발견·남은 것
1. **KB손보 2024.3Q 항목 16 공란 · 2024.4Q 항목 16 낡은 60,900**: 5절 참조. 2024.4Q 는 마스터 60,900 인데 새 빌드는 공란(`_zero_other_expense`), 빌더 소스 380,949 = FY2025 연간 비교열. 이번 범위 밖이라 그대로 두었다. 처리 방향(박제 허용 / 2024.1Q~4Q 항목 16 을 gold 로 통일)은 owner/validation 결정.
2. 푸본현대·ABL 2024.4Q 항목 26·31 단일분기 4칸이 새로 공란(연간 비교열만 새 판이고 9개월 비교열은 옛 판) — 공란은 의도다. 2025.3Q 26칸 공란은 FY2026 3분기 보고서 제출 뒤.
3. 한화생명 2023.1Q·2Q LOB 노트 항목 5·6·9·10·11 은 후속 필링 전기 표가 달라 옛 판 그대로(리더 변경 필요, 프로토타입 `measure/p_hanwha.py`). 다른 리더 변경(PLAN.md §6 1~4·6~10)도 이번에는 하지 않고 TODO 에 남겼다.
4. 대상 9사 출처표 12블록이 emitter 와 다름(적재 전부터, HEAD 에서는 16블록이었고 이번에 4블록이 해소됨; 이번 범위 밖): KR0001 2023.3Q(contract_notes · income_statement) · KR0010 2024.4Q·2025.2Q · KR0070 2023.1Q~4Q · KR0083 2023.1Q·2Q · KR0099 2023.1Q·2Q (income_statement).
5. 후속(오케스트레이터가 다음 단계에서): publishing = xlsx `손익분해PL`·`CSM워터폴` 동기화, `NB_CSM_multiple` 4행(메리츠·한화생명 2023.1Q·2Q) 재빌드, panel·public_exports 재생성 / validation = `pl_bridge_baseline.json` 해소 5줄(KB라이프 2024.1Q · 롯데 2023.2Q · 메리츠 2023.2Q · 한화생명 2023.1Q·2Q 줄이 이제 닫힘), `WFY_EXCEPTIONS` 불용 항목, `pl_csm_amort_missing_ledger.json` 롯데 2023.1Q 줄(게이트가 `PL_CSM_AMORT_MISSING_LEDGER_INERT` YELLOW 로 알림) / owner = NEEDS_OWNER 21행 D1~D3, 위 1번.

### 9. 재현·되돌림
```
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe ; cd C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25
$PY e21_verify.py < /dev/null            # 독립 재독 (problems 0)
$PY e21_apply.py --verify < /dev/null    # 새 빌드와 일치 확인
$PY e21_diff_vs_head.py < /dev/null      # HEAD 대비 49 PASS
bash run_gates.sh gates_final ; $PY compare_gates.py gates_before gates_final out.txt
bash run_tests_final.sh final            # 약 9분: 7개 테스트 파일 순차
cd ../../../.. ; $PY scripts/validate_golden_input_fingerprints.py   # RED=0
```
되돌림: `e21_post_klife.py --revert --apply` → `e21_apply.py --revert --apply` → `git checkout -- data/dart/viz/pl_breakdown_master.json scripts/pl_breakdown/companies.py tests/fixtures/pl_breakdown_golden.json tests/fixtures/master_tables_golden.json tests/fixtures/builder_input_fingerprints.json data/_derived/qoq_warn.json data/_derived/pl_oci_vs_bs_aoci_warn.json`(`INDEX.txt` 4절).

변경 파일(절대 경로, 모두 미커밋): `C:\Users\sangwook.cho\Desktop\insurequant\` 아래 `PL_breakdown.json` · `CSM_waterfall.json` · `PL_breakdown_provenance.json` · `CSM_waterfall_provenance.json` · `data\_gold\user_pl_cells.json` · `data\_gold\user_csm_cells.json` · `data\_gold\gold_overlay_ledger.json` · `data\dart\viz\pl_breakdown_master.json` · `scripts\pl_breakdown\companies.py` · `tests\test_rule_coverage_manifest.py` · `tests\fixtures\pl_breakdown_golden.json` · `tests\fixtures\master_tables_golden.json` · `tests\fixtures\builder_input_fingerprints.json` · `data\_derived\qoq_warn.json` · `data\_derived\pl_oci_vs_bs_aoci_warn.json` · `TODO_parser_ifrs17.md` · `docs\todo_archive_parser_ifrs17.md` · `docs\changelog_parser_ifrs17.md` · 이 티켓 · 신규 증거 폴더 `data\_derived\remaining_20261022\e21_ready25\`.

### 오케스트레이터 종결 메모 (2026-10-23)
READY 25행 적재(PL 440 + CSM 55칸)는 validation 독립 검수 PASS(`data/_derived/remaining_20261022/e21_ready25/verify/INDEX.txt`, 7개 점검). 판단 3건: (a) KB손보·메리츠 항목 16 gold 4칸 교체 = 수용(옛 gold 는 연결 표 값이었고 owner xlsx 가 아니라 2026-08-25 파서 판정 gold) · (b) 롯데 CSM 2023.1Q 항목 4·6 gold 2칸 교체 = 검수는 owner 확인 권고, 옛 값이 닫힘 플러그이고 gold why 에 「출처 불명」이 적혀 있어 「플러그 금지」 방침대로 두고 owner 보고에 올림(되돌리려면 2칸) · (c) KB손보 2024.3Q 항목 16 미적재 = 수용. 후속: validation 티켓 `20261023T0600Z…KR0104…nh_life_17_20_21_vintage_gap.md`(저강도), 게이트 정리, publishing(xlsx 2시트·NB 4행·패널·public_exports).
