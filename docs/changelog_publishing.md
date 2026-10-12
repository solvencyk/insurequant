# Insurequant Changelog — Publishing Stage

> Last updated: 2026-10-12 · Stage 4/5 — publishing
> Prompt: docs/agents/claude-agent-publishing.md · TODO: TODO_publishing.md

**Scope:** master JSON assembly + change reporting + git push command recommendation. HTML structure/styling is **designer** ([`docs/changelog_designer.md`](changelog_designer.md)).

**Cross-stage history:** `docs/claude-changelog.md`.
**This file:** entries scoped to publishing work only.

---

## 2026-10-12 — 소진율 도넛 · Forward Outlook 재공개 (티켓 `20261012T2030Z`, 커밋 `ef62969`·`2729a53`, 커밋만 · push 보류)

owner 「분류 근거가 확정돼 소진율 도넛과 Forward Outlook 을 다시 살린다」, 정의(계정 단위 · 해설서 p13 각주 ⑴)는 불변. 증빙 `data/_derived/capsec_reinstate_20261012/`.

- **등재부** `data/bonds/capital_tier_registry.json`: tier2 확정 4사(하나생명 제1회 1,799 · 푸본 2023-02 600 · 농협생명 제5회 2,500 · 코리안리 제5/6회 2,500+2,300) = 증권 6건, `type_unconfirmed` 5건 해제(푸본의 채권원장에 없는 50억만 미확정으로 남음). 교보 2024-11 6,000억은 `type`=tier2(발행조건 스텝업) + 새 필드 `issuer_type`=tier1(발행사 K-ICS 표 처리), 하나생명은 `type`=tier2 + `issuer_type`=tier1. DB손보 5건·하나손해 2건은 분류 불변, 근거 문구에 owner 확정 추가. 새 필드 `issuer_type` 은 `type` 과 다를 때만 적는다(시험이 하나생명·교보 두 건임을 강제).
- **소진율** (`apply_disclosure_utilization.py --quarter 2026.2Q`): tier1 4사만 변경 - 하나생명 238.2->0.0 · 코리안리 205.1->94.0 · 농협생명 72.7->48.5 · 푸본 42.1->17.3. 교보 70.1(결속 쪽이 기발행이라 불변)·tier2 47사 불변. 전후 47사 표 `utilization_before_after_47.csv`, 분자 자기검산 47사 불일치 0(`r7_numerator_selfcheck.txt`).
- **Forward Outlook** (`forward_capital_simulation.py`): 신종 기본자본 기여 = legacy_tfi `min(잔액, SCR_y x 15%)` + tier1 `min(잔액, SCR_y x 10%)`, tier2(보완자본형)는 0 -> 콜은 총자본에서만 빠진다. 한도는 매 연말 SCR 로 다시 계산하므로 「한도 초과로 재분류된 부분이 먼저, 그다음 기본자본」이 자동으로 나온다. 계층 정본은 `issuer_type`(없으면 `type`): 기준시점 기본자본이 회사 공시값이라 콜 차감 계정은 발행사 실제 처리를 따른다. **총자본(지급여력비율) 경로: 47사 전 연도 바이트 동일**(`forward_before_after_summary.txt`: total-path diffs 0, confidence diffs 0). 기본자본비율 경로가 바뀐 회사 11곳. 한화생명 56.76 -> 56.76 -> 56.76 -> 54.97(2029) -> 41.76(2030) 이던 것이 2026~2030 내내 56.76 (신종 4건 전부 보완자본형). 표 `forward_before_after_47.csv`, 손계산(한화생명·DB손보·하나손해·하나생명·교보·메리츠) 불일치 0(`handcheck.txt`).
- **새 필드(additive, 기존 이름·뜻 불변)**: 회사 행 `baseline_basis_flag`(하나생명·교보만 true) · `baseline_basis_note`(기본자본 경로를 발행사 처리 기준으로 계산했고 우리 분류 기준 경로는 `basic_ratio_by_type_pct` 라는 한 줄) · `type_unconfirmed` · `outstanding_hybrid_by_type_eok` · `hybrid_classification[]`(증권별 type/issuer_type/출처). 연도 행 `hybrid_legacy_remaining_eok` · `hybrid_tier1type_remaining_eok` · `hybrid_tier2type_remaining_eok` · `hybrid_limit_tier1type_eok`(SCR x 10%) · `basic_capital_by_type_eok` · `basic_ratio_by_type_pct`(어긋난 회사만) · `basic_ratio_if_tier2_type_pct`(미확정 증권이 있는 회사만). 기존 `hybrid_tier1_eok` = 기본자본 인정분 합, `hybrid_tier2_overflow_eok` = 두 한도 초과 재분류분 합, `hybrid_limit_eok` = SCR x 15% 그대로.
- **재공개**: `export_public_sheets.PRIVATE_SHEETS`·`PRIVATE_ROOT_JSONS`·`android_push_and_deploy.sh PRIVATE_PATHS` 를 비움(메커니즘·시험은 합성 목록 주입으로 유지). main 이 비공개 배포로 6개 경로를 이미 지웠으므로 `NEW_FILES` 에 `kics_tier1_utilization.json` `kics_tier2_utilization.json` `kics_forward_capital.json` `public_exports/{기본자본소진율,보완자본소진율,자본비율전망}.json` 추가. `public_exports` 3시트 신규 + manifest, 다른 13시트 바이트 동일. xlsx 시트 `기본자본소진율`(10칸·6행 교체)·`자본비율전망`(127칸·3행 교체)은 `sync_master_xlsx_sheet.py` 로, 열 구성 불변, `check_master_xlsx_drift` 드리프트 0.
- **되돌리는 방법**: `PRIVATE_SHEETS = ("기본자본소진율", "보완자본소진율", "자본비율전망")` · `PRIVATE_ROOT_JSONS = (3개 파일)` 복원 + 배포 스크립트 `PRIVATE_PATHS` 에 같은 6개 경로 복원(+ NEW_FILES 에서 6개 제거) + exporter 재실행. 분류만 되돌리려면 registry 커밋 `ef62969` 의 해당 줄을 되돌리고 `apply_disclosure_utilization.py` -> `forward_capital_simulation.py` 순으로 재실행.
- **미결/불일치 보고**: (a) census 최종본 `census_securities_final.csv`(20:02 생성, 작업 중간에 도착)를 등재부와 대조했다(`vs_final_census.txt`): 43건 중 같음 37, 「다름」 6건은 전부 이 라운드 이전 등재부 기준이고 최종본 type 이 지금 등재부(tier2)와 일치한다 - 교보 2024-11(스텝업, 발행사 표 상충 병기)·푸본 600·하나생명 제1회·농협생명 제5회·코리안리 제5/6회. DB손보 5건 tier1·하나손해 2건 tier2 도 최종본과 같아 등재부 추가 변경 없음. (b) 하나생명·교보는 발행사 처리와 분류가 달라 `baseline_basis_flag`. (c) 경과조치 기발행분 15% 는 2032 까지라 전망 범위(2026~2030) 안이다 - 2032 이후 처리는 범위 밖이라 모델에 넣지 않았다. (d) 한도 분모는 종전대로 보간한 SCR_y (규정상 Ⅵ.1.라 경과조치 적용 전 총요구자본과의 차이는 종전 모델과 같다). (e) 하나손해 2026-06 신규 신종(약 1,000억)은 채권원장 미등재라 콜 차감에 안 들어간다(콜 2031 이후라 범위 밖).
- 시험: `tests/unit/test_capital_utilization_rules.py`(재분류 이유로 값 4개 갱신 + 변이 3건 추가) · 신규 `tests/unit/test_forward_capital_tiers.py` 13건(한도 분리·보완자본형 기본자본 불변·총자본 불변·종전식 재현·issuer_type 플래그·미확정 대체 경로·한도 비율 변이·유형 뒤집기 변이·배포본 == 모델) · `test_private_deploy` 14 · `test_push_gate_wiring` 63(1 skip) · `test_deploy_assets` 12 · `test_rule_coverage_manifest` 102. 게이트 `validate_data_contract` RED=0 · `validate_live_artifacts` RED=0(baselined 25) · `check_master_xlsx_drift` 0.

## 2026-10-12 — 타임라인 JSON 읽는 검사기 선언 + 죽은 선언 정리 (티켓 `20261012T1945Z`, 커밋만 · push 보류)

- 원인: owner 가 작업 브랜치를 배포하자 라이브 `K-ICS.html` 이 `kics_capital_securities_timeline.json` 을 fetch 하는데 `tests/test_push_gate_wiring.py::LIVE_ARTIFACT_READERS` 에 그 파일의 선언이 없었다(`test_every_live_fetched_artifact_has_a_declared_reader`). 같은 시험의 ghost 검사도 실패: `kics_forward_capital`·`kics_tier1_utilization`·`kics_tier2_utilization` 은 비공개 3시트가 돼 화면이 더는 fetch 하지 않는데(원격 main HTML 도 0건) 선언만 남아 있었다. designer 가 말한 「나머지 1건」은 이것이다(마스터 시트 요구 시험 `test_every_live_fetched_artifact_lands_in_a_master_sheet` 는 `PANEL_DERIVED_FROM` 선언이 없어 같이 걸렸다).
- 검사기: `scripts/validate_live_artifacts.py::check_capsec_timeline`(게이트 check 8) - ① 구조(`securities[코드][]`, `tier`·`issue_date`·`face_eok`·`outstanding_eok` 필수·형식) ② 허용 필드 밖의 키(인정액·한도·분류 계열 포함) 금지 ③ 회사별 건수·`face_eok` 합이 `data/bonds/capital_securities_fy2026h1.json` 에서 독립 파생한 값과 일치(회사 census 포함). 룰 id `CAPTL_STRUCTURE`·`CAPTL_EXTRA_FIELD`·`CAPTL_SOURCE_MISMATCH`. 실측 배포본: 26사 125건, RED 0.
- 선언: `LIVE_ARTIFACT_READERS["kics_capital_securities_timeline.json"] = ["validate_live_artifacts"]`, `PANEL_DERIVED_FROM[...] = "kics_capital_securities.json"`(`자본성증권발행현황` 시트. 실측 타임라인 125건 중 122건이 시트와 (회사,발행일,권면) 일치, 3건 타임라인 전용, 시트 전용 1건은 발행일 없음). 죽은 선언 3개 삭제(파일 자체는 검사기가 계속 읽는다).
- 변이시험: `tests/test_rule_coverage_manifest.py` 의 `test_capsec_timeline_gate_*` 3개(정상 통과 · 변이 11종 + 원천 변조 각 룰이 잡힘 · 배포본 통과).
- 시험: `test_push_gate_wiring` 63 passed 1 skipped(기존 skip) · `test_deploy_assets` 12 · `test_prepush_scope` 65 · `test_rule_coverage_manifest` 102 · `unit/test_capital_securities_timeline` 15 passed. 게이트 `validate_live_artifacts` RED=0.
- 놓친 이유: 「새 fetch 파일 → 선언」 시험은 `origin/main` 의 HTML 만 보는 구조라 배포 후에야 걸린다. 의견: 같은 시험의 fetch 목록을 `origin/main ∪ 작업트리 HTML` 로 넓혀 gap 검사도 배포 전(작업 브랜치 push 훅)에 걸 수 있다. `_worktree_fetches()` 가 이미 있어 한 줄 수준이고, 부작용은 작업 브랜치에 임시로 붙인 fetch 도 선언을 요구받는다는 것뿐이다(구현은 별도).

## 2026-10-12 — 비공개 3시트 · 자본성증권 공개 열 제한 · 뮌헨/스위스리 재동기화 (티켓 `20261012T1420Z`·`1440Z`, 커밋만 · push 보류)

owner 지시 「내린 시트들은 비공개로 돌리고」 / 「3 승인」. 저장소의 마스터 JSON·마스터 xlsx 시트·`output/` 은 그대로, 공개 스냅샷과 main(라이브)에서만 내렸다.

- **비공개 시트**: `export_public_sheets.PRIVATE_SHEETS`(기본자본소진율·보완자본소진율·자본비율전망)는 스냅샷을 만들지 않고 manifest 에 싣지 않으며 옛 파일이 있으면 지운다. `PUBLIC_MASTERS`(= MASTERS - 비공개 3)가 게이트의 검사 대상이다. 새 룰 `PUBLIC_EXPORT_PRIVATE_SHEET_PRESENT`(비공개 시트 파일이 있으면 RED).
- **main 에서 지우기**: `scripts/android_push_and_deploy.sh` 의 `PRIVATE_PATHS`(공개 스냅샷 3 + 루트 `kics_tier1_utilization.json`·`kics_tier2_utilization.json`·`kics_forward_capital.json`)는 갱신 대상에서 빠지고 main 에 있으면 배포 커밋에서 `git rm`. tier1 은 designer `1624aba`(타임라인 JSON 계산, tier1 fetch 제거) 뒤에 넣었다. 목록 일치는 `tests/test_private_deploy.py` 가 exporter `private_paths()` 와 대조한다.
- **자본성증권발행현황 공개본**: `_SHEET_DROP_COLS` 로 기본자본인정액_억·보완자본인정액_억·기본자본한도_억·SCR_억·보완자본인정율·경과조치·경과조치종료일 제외(경과조치는 발행일로 우리가 붙인 구분이라 같이 뺐다). 남은 열: 회사명·구분·종류·발행일·콜만기도래일·법정만기일·콜근거·액면가_억·잔액_억·공시분기·잔액기준일·출처·비고. 게이트는 시트별 제외 열(`drop_cols(sheet)`)로 대조한다(느슨하게 풀지 않고 제외 열만 뺀 기대값과 셀 단위 일치).
- **재동기화**: 뮌헨 KR1101 2026.2Q +3행(`33635d1`) -> xlsx `K-ICS공시` 30008->30011, 스위스리 KR1102 2026.1Q +8행(`4147fc1`) -> xlsx `보험계약부채` 6335->6343. `build_master_xlsx._ilp_basis_note` 가 provenance `how=derived_sum_of_rows` 를 읽어 기준표시 「계산값(전 행 합)」 + 비고(인쇄 합계가 Indirect-Par 행을 뺀 값이라 전 행을 더함)를 붙인다. `csm_combo` 패널은 KR1102 2026.1Q 노드 1개(+18 슬롯)와 `meta.lic_recon` 문구만 바뀌었다.
- **되돌리기**: `PRIVATE_SHEETS`/`PRIVATE_ROOT_JSONS` 와 `PRIVATE_PATHS` 에서 경로 제거 + `download-survey.js` 주석 해제 + exporter 재실행. 공개 열 복원은 `_SHEET_DROP_COLS` 에서 열 제거 후 재실행.
- **증빙**: `data/_derived/private_sheets_20261012/`(`proof_changes.txt` = HEAD 대비 공개본 변화, `panel_csm_combo_diff.txt`).

---

## 2026-10-12 — 최종 재동기화 (push 직전 정합, 티켓 `20261012T1330Z`, 커밋만 · push 보류)

오늘 바뀐 마스터(재보사 손해율 세그먼트 `268002b`, 재보사 PL 7칸 복원·처브 BS 20/ILP 14-15·분할표 상각 `3bf1690`, K-ICS 퍼시픽 +16행·악사 4칸 `acd351a`)에 xlsx·공개본·패널을 맞췄다.

- **패널**: `viz_build_persistency_lossratio_panels.py` -> `panel_loss_ratio.json` 41노드(재보사 KR1101~1107 의 세그먼트가 `생명보험`/`장기손해보험` 으로 나뉘고 옛 `손해보험`·빈 구분 노드 삭제, `--check` OK), `viz_build_csm_combo_panel.py` 21노드(처브 KR0100 만, 포트폴리오 부채열), `viz_build_compare_panel.py` 2칸(악사 K-ICS 2024.3Q 286.4->286.5, KR1101 투자손익 null->0). ifrs17 viz 4패널·`csm_waterfall` 은 재빌드해도 바이트 동일. 증빙 `data/_derived/final_resync_20261012/panel_*.txt`.
- **xlsx**(`sync_master_xlsx_sheet.py` 시트별, 백업 `.bak_20261012_final_pre`): `17BS` 6칸(처브 보험계약부채 K-IFRS 기준 값->값), `CSM상각` 18칸(메트라이프·BNP·AIA·처브 2025.4Q 9·10년차 빈칸->값 8, 한화생명 분할표 정정 10), `손익분해PL` +7행·1칸(`값_당분기`), `보험계약부채` 18칸(처브 값->값), `K-ICS공시` +16행(퍼시픽 2025.3Q·2026.2Q 47~54)·4칸(악사 2024.3Q). 삭제 0, 나머지 12시트 값 SHA 동일(`xlsx_invariance.txt`), `요약` 은 행수 칸만 다름.
- **공개본** `export_public_sheets.py`: 5시트 + `manifest.json`(`build_id` `538cbe7`). 임시로 목록에서 내린 3시트 파일은 그대로 둠.
- **게이트**: `check_master_xlsx_drift` RED 7 -> 0, `validate_data_contract` RED 0(YELLOW 152), `validate_live_artifacts` RED 0(baselined 25), `validate_master_tables --no-build` 실행(exit 2 는 골든이 고정한 값), 골든 3종(master_tables·ifrs17 panels·csm_waterfall) passed, `test_deploy_assets`+`test_push_gate_wiring`+`test_prepush_scope` 142 passed.
- **미반영(의도)**: `downstream_kpis.json`(213칸 어긋남, 옛 `cf66dce` 미반영분이라 이번 범위 밖·HTML 무참조), `viz_build_nb_csm_ratio.py`(IR 원문 입력).

## 2026-10-12 — `kics_capital_securities_timeline.json` 신설 (티켓 `20261012T1210Z`, owner 정정으로 채권 단위 발행 내역으로 축소, 커밋만 · push 보류)

K-ICS 「자본성증권 발행현황」 누적 막대(발행일 기준, 아래 신종자본증권 + 위 후순위채)의 원천. owner 지시(2026-10-12): 시점별 잔액을 DART 에서 새로 뽑지 않고 이미 있는 채권 단위 자료만 쓴다(중간에 만들던 시점별 추출기는 폐기).
- 파일 `kics_capital_securities_timeline.json`(루트, 배포 keep-list 등재: `android_push_and_deploy.sh` NEW_FILES · 발행 프롬프트 §1 표), 빌더 `scripts/build_capital_securities_timeline.py`, 입력 `data/bonds/capital_securities_fy2026h1.json`(`securities_summary` 와 같은 입력 = 회사별 최신 기준일 자료).
- 명세: `{"generated":"YYYY-MM-DD","unit":"억원","source":"...","securities":{"<회사코드>":[{"tier":"hybrid"|"subordinated","issue_date":"YYYY-MM-DD","call_date":"YYYY-MM-DD"|null,"coupon_pct":number|null,"face_eok":number,"outstanding_eok":number,"as_of":"YYYY-MM-DD"}]}}`. 회사코드는 JSON 키로만. 회사 안에서 발행일 순. 억원 = 백만원/100, 소수 둘째 자리. `face_eok` = 발행 권면, `outstanding_eok` = `as_of` 시점 잔액(상환돼 0 이어도 발행 내역이라 싣는다). `as_of` 는 채권별 기준일(2025-12-31 또는 2026-06-30). tier 는 원천 그대로이고 기본자본/보완자본 판단·인정액 필드는 없다.
- 범위: 26사·125건(신종 45·후순위 80). 원천 127건 중 2건 제외(동양생명 2020 신종 - 권면 없음·잔액 0, 악사손해 JPY 후순위 - 발행일 없음; 추측하지 않는다). **원천에 한 번도 오르지 않은 과거 상환 증권은 없다**(원천이 2025-12-31·2026-06-30 잔액 기준 목록이라 그 전에 상환된 채권은 발행 막대에서 빠진다 - 과거 연도의 발행량이 낮게 보일 수 있다).
- 시험 `tests/unit/test_capital_securities_timeline.py` 15 passed(단위 변환 · 상환 0 포함 · 발행일/권면 없음 제외 · 정렬 · 변이 3종 검출 · 배포본 = 원천 재생성 · 분류 필드 없음 · 한화생명 신종 4건 손계산).

## 2026-10-12 — `보험금예실차비율` xlsx 시트·공개 스냅샷 신설 (티켓 `20261012T1130Z` 3번, 커밋만, push 보류)

owner 승인 「나머지는 다 승인」(스키마 변경, `TODO.md` ㉓). 소스 `data/loss_ratio/claims_ae_ratio.json`(44사, 162행). 빌더 `scripts/build_master_xlsx.py` 의 `MASTERS` 에 항목 1개 + `FLATTEN`(`_flatten_claims_ae_ratio`), `scripts/export_public_sheets.py` 의 `MASTERS` 1개.
- 열(13): 원보험사코드 · 원수사명 · 티커 · 생손보여부 · 공시분기 · 기준연도 · 사업구분(코리안리 공동재보험 등 6행만) · 예상손해율 · 실제손해율 · 예실차비율 · 단위 · 출처쪽(PDF 쪽 번호) · 플래그(영문 코드는 한글 문구로: 기준연도 읽은 위치·전치 표·빗금 등, 모르는 코드는 KeyError). 내부 파일 경로·추출방식·원문은 JSON 에만 남긴다. 공개본은 원보험사코드 제외 12열.
- `sync_master_xlsx_sheet.py "보험금예실차비율"` 로 그 시트만 추가(백업 `insurequant_master_tables.xlsx.bak_20261012_ae_sheet`): 162행 x 13열, 마스터와 셀 단위 일치. **다른 17시트 값 해시 동일, 요약 시트만 1행 증가(21→22)** (`data/_derived/ae_sheet_20261012/v1_other_sheets_identity.txt`).
- 공개본 `public_exports/보험금예실차비율.json` 162행 + manifest 항목 1개(`export_public_sheets.py --only`, 다른 시트 파일·항목 불변).
- 선언 갱신: `PUBLIC_EXPORT_SHEETS` 15→16, `MASTER_XLSX_SHEETS` 17→18(`tests/test_rule_coverage_manifest.py`), 공개본 대조 식별열에 `기준연도`·`사업구분` 추가(`validate_live_artifacts._PE_ID_COLS` — 안 하면 74행 중복으로 KEY_AMBIGUOUS), `android_push_and_deploy.sh` NEW_FILES 에 신규 파일 등재, 발행 프롬프트의 공개 파일 수(17개).
- **designer 용 위치**: 시트 이름이 나열된 곳은 `download-survey.js` 의 시트 목록(`SHEETS`, 보험계약부채 다음 줄에 `{ name: "보험금예실차비율", file: "public_exports/보험금예실차비율.json", code: ..., label: ... }` 한 줄 추가가 필요 - 안 하면 사이트 다운로드에 안 보인다). `공시보고서.html` 등 다른 HTML 에는 시트 목록이 없다.
- 게이트: `check_master_xlsx_drift` 새 시트 드리프트 0(전체 RED 5건은 다른 시트 - 17BS·CSM상각·손익분해PL(2)·보험계약부채 - 로 파서 ifrs17 의 미반영 마스터 변경), `validate_live_artifacts` RED 0(공개본 16시트 중 이 시트 포함), `tests/test_rule_coverage_manifest.py` 98 passed·1 failed(=위 다른 시트 드리프트), `test_push_gate_wiring` 65 passed.

## 2026-10-12 — `securities_summary` 필드 신설 (K-ICS 소진율 도넛 밑 신종·후순위 큰 셀용, 커밋만, push 보류)

티켓 `inbox/publishing/20261012T1150Z__orchestrator__MULTI_2026.2Q__capital_securities_summary_fields_for_cells.md`. 산식 `scripts/capital_securities_summary.py`(순수 함수), 쓰는 곳 `scripts/apply_disclosure_utilization.py`(소진율 산출과 같은 경로, 재실행해도 소진율 변경 0건), 입력 `data/bonds/capital_securities_fy2026h1.json`(소진율 분자는 경영공시 항목이지만 발행금리·콜일은 증권 단위 자료에만 있다. 채권원장 `kics_capital_securities.json` 에는 쿠폰이 없다).
- **필드 명세**(`kics_tier1_utilization.json`·`kics_tier2_utilization.json` 47사 행 모두에 같은 값, 기존 필드 변경 없음):
  `securities_summary: { as_of, hybrid, subordinated }` — `as_of` = 분기말(2026-06-30, 콜 도래 판정 기준일). `hybrid`(신종자본증권)·`subordinated`(후순위채)는 **잔액이 남은 증권이 없으면 객체 전체가 null**, 있으면 아래 키:
  - `latest_coupon_pct`: 잔액이 남은 증권 중 발행일이 가장 늦은 증권의 쿠폰(%). 같은 날 여러 건이면 잔액이 큰 쪽. 그 증권의 쿠폰이 원천에 없으면 **null**(이전 증권 값으로 대신하지 않는다). `latest_issue_date`: 그 증권 발행일(툴팁용).
  - `issued_since_2023_eok`: 발행일 >= 2023-01-01 인 증권의 잔액(`outstanding_mn`) 합 / 100, 정수 반올림. 해당 없으면 0.
  - `next_call_date`·`next_call_eok`: `past_call_outstanding`=false 이고 콜일 >= as_of 인 증권 중 가장 이른 콜일과 그날 잔액 합(같은 날 여러 건이면 합). 해당 증권이 없으면 둘 다 null.
  - 추가 필드 2개(명세 밖, 화면이 정직하게 쓰도록): `next_call_estimated`(콜일이 원문 공시가 아니라 발행일+5년 등 추정이면 true, 콜일 없으면 null) · `balance_as_of`(그 tier 잔액 중 가장 오래된 기준일 - 22사는 잔액이 2025-12-31 기준이라 2026-06-30 과 다르다).
- 판정: 47사 x 2 tier = 94칸 중 신종 null 30·후순위 null 23. 발행일 미상 증권(악사손해 후순위 1건)은 최근 발행·2023 이후 합계에서 빠진다(추측 안 함). 흥국화재 후순위의 가장 최근 발행(2026-03-31)은 쿠폰이 원천에 없어 `latest_coupon_pct` null, 콜일도 없어 그 증권은 콜 후보에서 빠진다. 푸본현대 후순위처럼 같은 날 콜이 여러 건이면 합산(3,995억). 증빙 `data/_derived/capital_securities_summary_20261012/s1_judgment_table.{csv,txt}`(채권원장 2023 이후 합계와 94칸 전부 일치 · 배포본 대조 차이 0).
- 한화생명(KR0068) 사람 검산 일치: 신종 최근 = 2025-06-24 외화 6.30%, 2023 이후 합계 30,819억(5,000+6,000+6,000+13,819), 가장 가까운 콜 2029-07-17 5,000억. 후순위 최근 4.45%(2024-12-12), 2023 이후 12,968억(4,988.23+7,979.32), 가장 가까운 콜 2027-02-04 10,720억(발행일+5년 추정이라 `next_call_estimated`=true).
- xlsx: `기본자본소진율`·`보완자본소진율` 시트는 `build_master_xlsx.py` 의 고정 항목 목록(`_TIER1_ITEMS`·`_TIER2_ITEMS`)만 행으로 만들어 이 필드는 **시트·공개본에 실리지 않는다**(항목행 추가는 스키마 변경이라 하지 않았다, 필요하면 owner 결정).
- 시험 `tests/unit/test_capital_securities_summary.py` 20 passed(경계 2022-12-31/2023-01-01 · 콜 경과 · 콜일 동일 다건 · tier 없음 · 쿠폰 없음 · 변이 5종 모두 검출).

## 2026-10-12 — 자본성증권 인정한도 소진율 규정 근거 재정의 반영 (커밋만, push·배포 보류)

티켓 `inbox/publishing/20261012T0800Z__orchestrator__MULTI_2026.2Q__capital_utilization_redefinition_apply.md`(Opus 실행). 정본 `data/_derived/capital_utilization_definition_20261012/definition_memo.md`(owner 결정 ①~⑦ 권고안 채택).
- 산식 `scripts/capital_utilization_rules.py`(신설, 순수 함수): 보완자본 = 항목 47 적용후 열 + 발행사 인쇄 관행 R0~R5(메모 s5 와 같은 계산, 항목 47 스코프는 `kics_json_rules._tier2_i47_scope_map` import) ÷ 항목 14(적용 전) × 50%. 기본자본 = max(기발행 신종 항목 53 ÷ SCR×15%, 기본자본형 신규 ÷ SCR×10%). `apply_disclosure_utilization.py` 가 47사 전부를 이 산식으로 쓴다(교보라이프플래닛의 옛 `no_bonds` 0.0 경로 → null + "경과조치 표 미공시", 스위스리 `numerator_undisclosed` → 0.0).
- 등재부 `data/bonds/capital_tier_registry.json`(신설, 18사 증권별 legacy_tfi/tier1/tier2 + 근거). 미정 4사: 흥국생명 = 기본자본형 확정(2022-12 전환우선주 2,300억 = 티시스 2,000·티캐스트 300 보도, X 실현가능성 검정 7개 분기, 경과조치 표는 496.5 만 이동 → 원칙 10%, 81.4%). 코리안리·농협생명·푸본 = 미확정(공개 자료에 스텝업 조건 없음, 시계열 검정으로 못 가름 `a5`·`a5b`) → 보수적 상한 205.1·72.7·42.1 + `type_unconfirmed`(보완자본형이면 94.0·48.5·17.3).
- 47사 메모 대조 차이 0(`a7_memo_diff.txt`). 전후 `b1_before_after_47.csv`: tier2 23사(한화생명 222.4→70.5, 메리츠 55.4→0.2, 미래에셋 112.4→24.5, 푸본 130.1→86.6, IBK 120.4→76.0, 농협손해 117.7→103.9 등, 교보라이프플래닛 0.0→null, 스위스리 미공시→0.0), tier1 14사(한화생명 136.3→0.0, 하나손해 284.9→0.0, 농협손해 223.2→0.0, KDB 103.2→0.0, 하나생명 158.8→238.2, DB손해 101.1→151.6, 코리안리 230.7→205.1 등).
- 파생물: `kics_forward_capital.json` 은 confidence 가 tier 값을 읽어 같은 인자로 재실행(`20261012T015750Z`) — confidence 109칸만 바뀌고 전망값은 같다, 신뢰도 low→high 5사(신한이지·한화생명·미래에셋·푸본·IBK). `data/bonds/capital_securities_forward_outlook.json`·`capital_securities_utilization_20261Q.json` 은 archive/ 스크립트 산출이라 아무도 읽지 않아 그대로 둠. `kics_capital_securities.json` 은 tier1 의 `scr_eok` 만 읽어 값 의존 없음(그 인정표의 "신종 15% 공유" 정책과 forward 모형의 신종 15% 일괄 가정은 새 정의와 다르다 - 보고만).
- xlsx(`sync_master_xlsx_sheet.py`, 백업 후): 기본자본소진율 값 54칸·비고 188칸, 보완자본소진율 값 47칸·비고 141칸, 자본비율전망 비고 275칸·_diagnostics 605칸(행 수 불변, `c4_xlsx_change_list.csv`). 손해율은 `268002b` 재보사 세그먼트 표준화가 미동기화돼 있던 기존 드리프트 1,520행(값 변경 0)을 같이 맞췄다. 시트 이름·열 불변. 기본자본소진율은 항목명을 그대로 두고 읽는 필드만 바꿨다("기본자본 인정한도(SCR x 15%)" ← `tier1_legacy_limit_eok`, "신종자본증권 인정액" ← `tier1_basic_new_eok`) - 항목명을 규정 표기로 바꾸는 것은 owner 승인 사항.
- 공개본: 3시트 + manifest(`build_id` c3ebcc3), 나머지 13시트 바이트 동일.
- 게이트: data-contract RED 0(YELLOW `T2_UTIL_OVER_100_DISCLOSED` 2 = 농협손해 103.9·동양 105.0, 종전 6), live_artifacts RED 0(공개본 재생성 후), xlsx 드리프트 0, K-ICS 룰 게이트 exit 0(입력 불변). 새 RED 0. tier1 100% 초과(DB손해 151.6·하나생명 238.2·아이엠라이프 221.7·코리안리 205.1 상한)는 tier1 도메인 룰이 없어 RED 가 나지 않는다 - 정당 초과 허용 규칙을 둘지는 validation 판단.
- 시험: `tests/unit/test_capital_utilization_rules.py` 25 passed(훅의 tests/unit 묶음에 들어간다), 코드 변이 3종 모두 검출(`e1_mutation_run.txt`), `test_deploy_assets`+`test_push_gate_wiring` 77 passed·1 skipped.
- **designer 용 새 필드**(기존 필드 이름·구조 유지, 추가만):
  - tier1 행: `utilization_pct`(새 값) · `tier1_hybrid_recognized_eok`/`tier1_hybrid_limit_eok`(결속 쪽 분자/한도 = 숫자 줄 "기본자본 자본증권 X억원 / 인정한도 Y억원") · `binding_leg`(`legacy_15` 기발행 SCR×15% · `basic_10` 기본자본형 신규 SCR×10% · null 자본증권 0) · `tier1_legacy_eok`/`tier1_legacy_limit_eok`/`tier1_legacy_pct` · `tier1_basic_new_eok`/`tier1_basic_new_limit_eok`/`tier1_basic_new_pct` · `tier1_excluded_tier2_type_eok`(보완자본형이라 뺀 금액) · `type_unconfirmed`(bool) · `tier1_pct_if_unconfirmed_tier2`(미확정일 때 범위 아래 끝, 아니면 null) · `type_note`(근거 문장) · `no_capital_securities`(true 면 "발행 없음"). `tier1_hybrid_issued_eok` 는 종전대로 항목 6 전체 - 화면 분자로 쓰지 않는다.
  - tier2 행: `utilization_pct`·`numerator_eok`(새 값, `rule`="NA" 이면 둘 다 null) · `tier2_limit_eok` · `rule`(R0·R1·R2·R3·R4·R5·R-none·NA) · `rule_basis` · `numerator_source` · `reason`(NA 일 때만 "경과조치 표 미공시") · `numerator_tfi_off_eok`/`utilization_pct_tfi_off`(경과조치 종료 시 관점) · `item47_scope` · `rule_flags` · `supplementary_capital_eok`(항목 3) · `lapse_excess_item49_eok`(항목 49) · `no_capital_securities`.
  - 표시(결정 ④): 분자 0 → "0%", `no_capital_securities` 면 "발행 없음" 덧붙임 · `rule`="NA" → 가운데 "—", 캡션 "산출 불가", 툴팁 `reason` · 스위스리는 항목 49 인쇄가 0 이라 보완자본 4,274억 설명은 `reinsurer_basis.note` 참고.
- owner 보고(메모 밖 새 발견): 메리츠·흥국생명은 「(기발행 후순위채무)」 행(항목 54)에 2023년 이후 신규 후순위채가 섞여 있다(메리츠 2024.3Q +6,581 = 2024-08 6,500억 발행, 흥국생명 2025.1Q +2,132·2025.4Q +901 = 2025 발행분, `a2`·`a3`). 메모 R2 대로면 메리츠 0.2%·흥국생명 10.6%, 원장 기발행분만 빼면 30.8%·37.0%(`a11`). 결정 ② 를 두 회사로 넓힐지 owner 결정 대상이라 이번에는 메모 값을 실었다.
- 커밋 `c3ebcc3`(산식·등재부·마스터·xlsx·forward·시험·증거), `00bab2a`(공개본), `bd69673`(문서), `3fe9a53`(배포본 대조 시험이 배포본의 분기를 따라가게). 증거 `data/_derived/capital_utilization_apply_20261012/`.

## 2026-10-12 — 미니 재동기화 2차 (재보사 PL·BS·CSM 재스윕 반영, 커밋만, push·배포 보류)

티켓 `inbox/publishing/20261012T0500Z__orchestrator__MULTI_2023.1Q-2026.2Q__mini_resync_2_reinsurer_resweep.md`. 마스터 JSON 은 읽기만 했다(3727438·57b7d78).
- xlsx 7시트를 시트별로 동기화(`sync_master_xlsx_sheet.py`, 기존 행 삭제 0): 손익분해PL 13,491→13,794(+303행, 값 변경 25칸 = 15행·KR1102/1103/1105 전부 값→값) · 17BS +49 · CSM워터폴 +18 · CSM상각 +15 · 가정민감도 +6 · 보험계약부채 +110 · 신계약CSM배수 +3. 마스터 diff 와 칸 단위로 일치, 다른 10시트 SHA 동일, 요약 시트는 행수 칸만 변경. 드리프트 RED 7→0.
- `NB_CSM_multiple.json` 390→393(재보사 KR1104 2025.4Q·KR1105 2025.4Q·KR1107 2023.4Q, 배수 null). 기존 390행 변경 0.
- 패널: ifrs17 viz 4패널·csm_waterfall 바이트 동일(재보사 상각·민감도는 최신 분기만 싣는데 신규 행이 모두 2023.4Q). csm_combo 52노드·compare 137리프 변경, 전부 재보사(다른 회사 0). compare 의 손해율 항목은 직전 라운드 재보사 행을 처음 반영한 것.
- `public_exports/` 7시트+manifest 재생성(build_id b4b6a71). 게이트: data-contract RED 102(전부 CONCEPT_MIXED_DISCLOSURE_INTO_DART, MASTER_XLSX_* 0), live_artifacts RED 0·YELLOW 25(baseline), 테스트 142 passed/1 skipped, viz 골든 2종 통과.
- 커밋 `b4b6a71`(xlsx·NB·패널·증거), `5079688`(public_exports). 상세 `data/_derived/mini_resync_20261012/runlog.md`.


## 2026-10-12 — 재보사 손해율 패널 확장 + 예실차 블록 + xlsx `손해율` 동기화 (커밋만, push·배포 보류)

- `scripts/viz_build_persistency_lossratio_panels.py`: `build_ae()` 추가(읽기 `data/loss_ratio/claims_ae_ratio.json`). 패널 최상위에 `ae` 블록: `ae[회사코드]={n, q:{공시분기:[[기준연도, 사업구분, 예상손해율%, 실제손해율%, 예실차비율%p, [플래그]]]}}` — 값은 마스터 그대로, 공시값 '-'는 null, 플래그는 마스터 `플래그` + `identity_break`/`dash`. `companies` 처리 코드는 바꾸지 않았다(재보사는 마스터에 행이 들어와 자동 편입).
- 패널 전후: 37사→44사(+KR1101~1107), 크기 180,325→206,065 바이트, `meta.quarters` 불변. 기존 37사 `companies` 항목 37/37 바이트 동일, `panel_persistency.json` 바이트 동일, `ae` 162행이 마스터와 불일치 0. `--check` OK.
- xlsx `손해율` 시트: 36,344→38,248행(+1,904, 변경 셀 0, 삭제 0), 나머지 시트 값 동일(sync 사후검증 OK). 백업 `insurequant_master_tables.xlsx.bak_20261012_lossratio`. 예실차·긴 형식 표용 시트는 `MASTERS` 에 없다(신설은 owner 승인 사항, 이번엔 안 만듦).
- 검증: `test_push_gate_wiring` 65 passed·`test_deploy_assets` 12 passed. `check_master_xlsx_drift`/`validate_data_contract` 의 RED 는 전부 다른 레인이 쓰는 중인 마스터(PL_breakdown 3종 112건·MASTER_XLSX_ROW_MISSING 6시트=17BS·가정민감도·CSM워터폴·CSM상각·손익분해PL·보험계약부채)이고 손해율·유지율은 0. `public_exports/` 는 이번에 재생성하지 않았다.
- 원자료·스크립트: `data/_derived/lr_panel_20261012/`.

---

## 2026-10-11 — 미니 재동기화: 라이나 CSM·PL 항목 4·상각 정정 반영 (커밋만, push·배포 보류)

- **xlsx**(`5d320c9`): 손익분해PL +33행·2칸 · CSM워터폴 +54행·15칸 · CSM상각 +50행·172칸 · 신계약CSM배수 +9행·6칸, 삭제 0. 마스터 diff 와 맞고 나머지 13시트는 값 SHA 동일. 드리프트 189 -> 0.
- **NB 마스터**: `build_nb_csm_multiple.py` 재빌드 381 -> 390행. 라이나 +9행·빈칸 3개 채움만 바뀜, 다른 회사 0 변경. `NB_CENSUS_MISSING` 0.
- **패널**: IFRS17 viz 4개·csm_waterfall 바이트 동일(라이나는 DART 행이라 마스터 상각이 패널에 안 간다), csm_combo 라이나 nb_csm 11칸, compare 53칸(라이나 + 재보사 신계약 CSM 18칸).
- **공개 스냅샷**(`812b007`): 4시트 + manifest(`build_id` 5d320c9). 게이트 data-contract RED 0 · live_artifacts RED 8(`INSPL_CENSUS_MISSING` 뿐). 골든 `csm_amort_schedule` 해시만 어긋남(validation `--update` 대기). 상세 `data/disclosure/_meta/mini_resync_runlog_20261011.md`.

## 2026-10-11 — 마감 라운드: xlsx 12시트 동기화 · 공개 스냅샷 · IFRS17 viz 재보사 · 패널 재빌드 · 자본성증권 정리 (커밋만, push·배포 보류)

- **xlsx**(`8848cb8`): 시트 12개를 `sync_master_xlsx_sheet.py` 시트 단위로 동기화(드리프트 434 -> 0, `MASTER_XLSX_*` RED 0). 추가 행 17BS 1,937 · 손익분해PL 517 · 가정민감도 116 · CSM워터폴 108 · CSM상각 180 · K-ICS공시 103 · 금리듀레이션갭 1 · 보험계약부채 114 · 기본자본소진율 80 · 보완자본소진율 112 · 자본비율전망 440, 바뀐 칸 17BS 93 · 손익분해PL 121 · K-ICS공시 107 · 금리민감도 62 · 금리듀레이션갭 39 · 보험계약부채 12. 유지율·손해율·신계약CSM배수·배당·자본성증권발행현황은 행수·값 SHA 동일. 경영지표는 xlsx 시트가 아니다(신설 안 함).
- **공개 스냅샷**(`61babb6`): `export_public_sheets.py` 전체 재실행, 13파일 갱신(3개 무변), manifest `build_id` 6f92fb0 · 15시트. 공개 게이트 발견 0. `android_push_and_deploy.sh` NEW_FILES 는 main 에 없는 새 공개 시트(`보험계약부채.json`)만 필요 — 나머지 둘(금리듀레이션갭·자본성증권발행현황)은 이미 main 에 있어 추가 불필요.
- **IFRS17 viz**(`17dca81`): `viz_build_ifrs17_panels.py` 가 마스터(CSM_amortization·CSM_sensitivity)의 재보사 7곳(마이브라운은 PAA 전용이라 해당 없음)을 DART 산출 뒤에 덧붙인다. 상각 39 -> 46, 민감도 32 -> 39, 기존 행은 JSON 동일(접두 동일), 보험손익·BS 패널은 바이트 동일. 상각은 마스터가 경과차년 1~10만 가져 total·y5_plus·y10plus 를 비운다. 민감도 provenance 사이드카에 DISCLOSURE 셀 7개(`emit_sensitivity_provenance.py`). 로컬 서버에서 8곳 전부 확인: 7곳 상각·민감도 정상, 마이브라운은 「상각 버킷 없음」·「민감도 데이터 미수록」 안내.
- **골든**: `test_viz_ifrs17_panels_golden` 은 상각 +7·민감도 +7 행만큼 달라져 실패(`--update` 안 함, validation 몫 — 그 뒤 `validate_golden_input_fingerprints.py --update`). `test_viz_csm_waterfall_golden` 통과.
- **패널**(`89ecf9a`): csm_combo 40 -> 48사 · 분기 8 -> 14 · `--check` OK, compare 패널 `--check` OK.
- **자본성증권**(`8848cb8`): `compute_tier{1,2}_utilization.py` 회사명을 마스터 원수사명으로(파일명이 K-ICS.html 매칭 규칙에 안 맞을 때만 -> KB라이프 1건 외 46건 동일 증명). `kics_forward_capital.json` 서울보증보험 제외 행(`status: excluded` + `exclusion_reason`), 생성기 `EXCLUDE_PAA` 도 같은 행을 낸다. designer 가 HTML 에서 `exclusion_reason` 을 읽기 전에는 서울보증 문구가 일반 문구가 된다(티켓 `inbox/designer/20261011T1600Z…`).
- **게이트**: `validate_data_contract` RED 22 = 알려진 것뿐. `validate_live_artifacts` RED 26 = 새 두 부류(`NB_CENSUS_MISSING` 18 · `INSPL_CENSUS_MISSING` 8) — 재보사에 NB 배수 행/보험손익 원표가 없어서(원인 구조적, 아래 TODO).
- **NB 재보사 18행**(orchestrator 승인, `1412aaf`·`04ea6c6`): `build_nb_csm_multiple.py` 실행 -> `NB_CSM_multiple.json` 363 -> 381행(git diff 234 추가·0 삭제, 배수 null), 신계약CSM배수 시트 +18행(기존 363 불변)·`public_exports/신계약CSM배수.json` 381행. `NB_CENSUS_MISSING` 18 -> 0, `validate_live_artifacts` RED 26 -> 8(INSPL 8만 남음).
- 상세 `data/disclosure/_meta/final_resync_runlog_20261011.md`.

## 2026-10-11 — 보험계약부채 마스터 시트 · 공개 스냅샷 신설 + KB라이프 소진율 도넛 이름 수정

- **xlsx**: 시트 `보험계약부채` 6,111행 x 13열(마스터 10열 + 단위·기준표시·비고). `sync_master_xlsx_sheet.py` 시트 단위만 — 기존 16시트의 행 수·값 SHA-256 전후 동일, 요약 시트 행 1개 추가. 백업 `insurequant_master_tables.xlsx.bak_20261011_ilp`.
- **공개 스냅샷**: `export_public_sheets.py` MASTERS 15개로, `--only <시트>` 옵션 신설(그 시트 파일 + manifest 항목만). `public_exports/보험계약부채.json` 6,111행, 게이트 발견 0.
- **선언**: `build_master_xlsx.MASTERS`·TEXT_COLS(`기준표시`)·FLATTEN, `MASTER_XLSX_SHEETS` 17, `PUBLIC_EXPORT_SHEETS` 15, `MASTER_SHEET_PENDING` 비움, `android_push_and_deploy.sh` NEW_FILES.
- **KB라이프**: tier1/tier2 배포본·빌더 20262Q 산출물의 `company` 1칸 `케이비라이프생명보험` -> `KB라이프생명`(K-ICS.html 매칭 이름). 컴퓨트 스크립트 재실행 시 옛 이름 부활 위험은 남음.
- 상세 `data/disclosure/_meta/ilp_master_sheet_runlog.md`. designer 필요 변경: `download-survey.js` SHEETS 1줄.

## 2026-10-11 — 재보사 8곳(KR1101~KR1108) 자본비율 Forward Outlook · 자본성증권 소진율 추가

- **원인 = 데이터 부재.** 재보사는 2026-10-09 에 `kics_disclosure.json` 에 들어왔고 `kics_forward_capital.json`(9/23)·`kics_tier{1,2}_utilization.json`(9/1)은 그 전 산출이라 8곳 행이 없었다. 화면은 「forward simulation 데이터 없음」·도넛 「데이터 없음」. 이름 매칭은 문제 아님(드롭다운 value = 원수사명 전체, 약칭은 라벨만).
- 추가만(기존 38/39행 `==` 동일 증명): `capital_securities_fy2026h1.json` 빈 레코드 8개(「스캔 후 무발행」 명시, 안 하면 게이트 `CAPSEC_COVERAGE_REGRESSION` RED) · tier1/tier2 산출+배포본 8행 · forward 빌더를 라이브와 같은 인자(`--baseline-quarter 2026.2Q --tier-quarter 2026.2Q --bonds-source …fy2026h1.json`)로 재실행해 38→46행. 도구 `scripts/add_reinsurers_to_capsec_panels.py`(멱등; `build_capital_securities_fy2026h1.py` 를 다시 돌리면 이것도 다시 돌린다).
- 스코리(요구자본 경과조치 적용사) 190.13%→187.80→185.53→183.31→181.15%(2030), 시작=K-ICS 적용후 공시, 2032 적용전 종점 176.97%(공시 176.99). 나머지 7곳 flat.
- 소진율: 7곳 0%. **스위스리 보완자본만 빈 칸** — 보완자본 4,274억(순자산 재분류분)인데 한도 적용 전·한도 '-' 라 확정 불가("틀린 값을 싣느니 빈 칸"). RGA 는 발행사 표의 한도 적용 전 5,499(=지급여력금액)가 보완자본 0 과 모순이라 0 + 원값 보존.
- 남은 것: xlsx 3시트(기본자본소진율 80행·보완자본소진율 112행·자본비율전망 440행) 동기 + public_exports 재생성(안 하면 `MASTER_XLSX_ROW_MISSING`), KB라이프 tier 행 이름 불일치(기존 행이라 이번엔 안 건드림). runlog `data/disclosure/_meta/reinsurer_forward_capsec_runlog.md`.

---

## 2026-09-23 — main 배포 7차 `22e2471`: K-ICS 금리 민감도 패널 교체 + 금리듀레이션갭 마스터 신설 (owner GO)

- 배포 4파일: `K-ICS.html` · `kics_duration_gap.json`(신규 270행) · `PL_breakdown.json`(라이나생명 2023.4Q 20칸) · `public_exports/manifest.json`(build_id `fa21ec9`). main `a5118f3..22e2471`.
- **새 마스터가 같이 올라가야 하는 배포다.** `K-ICS.html` 이 `kics_duration_gap.json` 을 fetch 하므로 HTML 만 올리면 fail-soft 로 카드가 통째 숨겨진다(에러는 안 나고 조용히 사라진다). keep-list 는 기억이 아니라 각 HTML 의 `fetch(` grep 으로 재파생해 확정했다.
- 게이트 `prepush_check` FULL **gate-clear** (RED=0 · 605 passed · 1,739초).
- **1차 BLOCKED 와 그 처리 (기록 가치 있음).** 골든 입력지문이 `pl_breakdown` 에 CODE_MOVED + OUTPUT_DRIFT 를 냈다 — `build_pl_breakdown.py` 의 `_GOLD_CELL_OVERRIDE` 에 라이나생명 2023.4Q 20칸을 추가했으니 정확한 발화다. 지문이 시킨 대로 **빌더를 실제로 재실행**(`RUN_PL_GOLDEN=1`, 372초)했고 `non_null_values` 10,257 → 10,277 = **정확히 +20** 이 나왔다. 손으로 넣은 칸 수와 일치한다. 이어서 `--update` 로 재생성한 산출을 커밋본과 셀 단위 대조해 **값 다른 셀 0 · 키 추가/삭제 0** 을 확인했다 — 즉 손으로 넣은 20칸을 빌더가 그대로 재현하고, 산출 바이트는 재작성 후에도 안 움직였다. 해시를 손으로 고치지 않고 `--update` 로 재생성(CLAUDE.md 불변식 3), 커밋 `a0f0607`.
- **2차 `offline tests=FAIL` 은 가짜였다.** 내가 게이트에 건 `timeout 900` 이 오프라인 묶음 도중에 잘라서 나온 것이고(EXIT=124), 묶음만 1,739초다. 묶음의 모든 테스트를 개별로 돌려 전부 pass 를 확인한 뒤 제한을 2,700초로 늘려 재실행해 `gate-clear` 를 받았다. **게이트 verdict 를 읽을 때 종료코드 124 를 같이 봐야 한다** — "FAIL" 과 "안 끝났다" 가 같은 문구로 나온다.
- 배포 후 검증: 라이브 4파일을 받아 `git hash-object` 로 커밋 블롭과 대조 **4/4 바이트 일치**. 회사망이 TLS 폐기검사(CRYPT_E_NO_REVOCATION_CHECK)로 막아 `curl -k` 가 필요했다(연결 자체가 막힌 게 아니다 — `http=000` 을 도달불가로 오독하지 말 것). 라이브 렌더 삼성생명 2026.2Q `5.94 / 6.60 / △0.26`.
- 작업 브랜치 `fix/csm-product-segmented-columns` 도 `37e4cd2..a0f0607` push 완료. 이 PC 에서 직접 push 가 됐다(폰 Termux 번들 불필요).
- 남은 것: `금리듀레이션갭.json` public_exports 스냅샷은 안 올렸다 — main 은 원래 `17BS.json`+`manifest.json` 만 싣고 있어 기존 관행을 그대로 뒀다. 다운로드 기능에 새 시트를 노출할지는 별건.

---

## 2026-09-21 — main 배포 6차 `a5118f3`: IFRS17·기타공시 헤더셀렉트+토글 이식 + K-ICS item14 적용후 30칸 원문 정정 (owner GO)

- IFRS17·기타공시 헤더셀렉트+토글 4파일 + K-ICS item14 후 30칸. main 커밋 `a5118f3`(`6741dea..a5118f3`), owner GO 후 push.
1차 시도(같은 날 앞 세션)는 `validate_kics_rate_sensitivity.py` RS2_BASE_ANCHOR RED=2(흥국생명 2025.2Q/4Q
item14 후 역산치)로 BLOCKED. parser-kics 에이전트가 `inbox/parser/20260921T1400Z` §B 를 처리하다 중단됐고
오케스트레이터가 마무리(`32ebfb0`, 상세는 `TODO_parser_kics.md` 18회차): item14 후 30칸 원문 정수 교체(30/30
MD 대조) + 흥국생명 item23 후 5분기 R5 재폐쇄 + 등재부 pin 갱신 + xlsx sync. `deb21e6` public_exports 재생성
(build_id `32ebfb0`). `21594e6` 골든 입력지문 갱신(kics_disclosure.json 을 입력으로 쓰는 4빌더 — 골든 4종 전부
pass, 산출 불변 확인 후 `--update`).
- 작업 트리 `prepush_check.py --full` 2회: 1차 `골든 입력지문=FAIL → BLOCKED`(예상, 위 갱신으로 해소) → 2차
  **gate-clear**(gate RED=0 · K-ICS 룰게이트 clear · 도메인게이트 pass · 골든 입력지문 pass · 배포 JS 런타임 RED=0 ·
  inbox 위반 0 · 605 passed).
- 격리 워크트리 cherry-push 7파일: `common.css` · `K-ICS.html` · `IFRS17.html` · `공시보고서.html` ·
  `kics_disclosure.json` · `public_exports/K-ICS공시.json` · `public_exports/manifest.json`.
- **라이브 확인**: `manifest.json` build_id `32ebfb0` · 라이브 바이트 ↔ HEAD 블롭 **5/5 일치**(한글 파일명은 curl 에
  URL-encoded 경로로 — 안 그러면 GitHub Pages 404 페이지를 받아 오탐) · `kics_disclosure.json` 흥국생명 2025.2Q
  item14 후 18,412 확인.
- 화면 숫자 변경: K-ICS 세부항목 표 적용후 컬럼 item14 30칸(8사, 대부분 ±1억) · 흥국생명 item23 후 5칸(±3~6억).
  item27 후(비율)는 헤드라인 소스라 불변.
- 워크트리 제거, 로컬 `main` = origin/main `a5118f3`. 남은 티켓: `inbox/parser/20260921T1400Z` §A(RS6 31칸) open.

## 2026-09-21 — 6차 배포 시도: IFRS17·기타공시 헤더셀렉트+토글 이식 (BLOCKED, 미배포)

- owner 승인("고치고 나면 main에 배포까지 진행") + designer 커밋 `6a51b7a`(orchestrator 사전검증
  완료: headless Playwright 1400/375px, deploy_assets 11 passed, validate_deployed_js --no-live RED=0)
  4파일(`common.css`·`K-ICS.html`·`IFRS17.html`·`공시보고서.html`)을 격리 워크트리
  `../insurequant-main-deploy`(main 기준)에 cherry-push 준비 — 로컬 커밋(`9ff5093`, push 안 함)까지만
  진행하고 **push 는 하지 않았다**.
- 사유: `scripts/prepush_check.py`(scope=FULL — diff 에 루트 HTML 포함돼 축소 불가) 가
  `validate_kics_rate_sensitivity.py` RS2_BASE_ANCHOR RED=2 로 BLOCKED. 흥국생명보험(KR0071)
  2025.2Q·2025.4Q item14 지급여력기준금액 `값_적용후`(비율역산 18415.27/19354.44)가 원문 헤드라인
  총괄표 인쇄값(18,412/19,350 억원)과 어긋남 — **이번 배포 payload 와 무관한 기존 K-ICS 데이터
  이슈**, 오늘 validation 이 신설한 RS2 적용후 앵커 룰이 처음 잡은 것이고 이미
  `inbox/parser/20260921T1400Z__validation__MULTI_2024.4Q-2025.4Q__ratesens_phase_level_holes.md`
  §B 로 parser 발주돼 있다(open). K-ICS 룰게이트 자체·offline tests 605 passed·골든 입력지문 6종·
  배포JS런타임게이트는 전부 clear/RED=0 — 막은 건 이 도메인게이트 하나.
- CLAUDE.md "RED 1건이라도 있으면 push 안 함, exception 우회 불가" + 이번 발주문의
  "RED 블록되면 --no-verify 쓰지 말고 멈추고 보고" 원칙 그대로 적용.
- 정리: 워크트리 제거, 로컬 `main` ref가 실수로 그 커밋(9ff5093)만큼 origin 보다 앞서 남았던 것을
  `git branch -f main origin/main` 으로 재동기화(6741dea) — stale-local-main 재발 방지.
  세션 도중 별개로 local `main` 이 origin 보다 32 커밋 뒤처져 있던 것도 발견해
  `git fetch origin main:main` 으로 정정(이 stale 참조가 원래 있던 것 — 이번 배포 시도가 만든 게 아님).
- 재현: `TODO_publishing.md` 최상단 항목에 커밋 diff·커밋 메시지 전문 기록 — RED=0 확인 후 워크트리
  재생성부터 push 승인까지 바로 재개 가능.

## 2026-09-21 — 자본비율전망 비고 내부 게이트 진단 문구 분리 (`44ae5fb`/`a61c8b2`/`c130062`, 배포 안 함)

- owner 티켓 `inbox/publishing/20260921T0320Z`: `public_exports/자본비율전망.json` 비고
  660행(추정 610행)에 `compute_confidence()`(`forward_capital_simulation.py`) 내부 게이트
  진단 문자열(필드명 `subordinated_eok`·`tier1_hybrid_issued_eok`·`numerator_eok_fallback`,
  게이트 용어 `advisory, not in overall`)이 그대로 노출.
- **원천 정정**: 실제 조립 지점은 `forward_capital_simulation.py`가 아니라
  `build_master_xlsx.py::_flatten_forward_capital()`이었다 — `kics_forward_capital.json`
  루트 마스터에는 `비고` 필드가 없다(flatten 시점 파생값). `forward_capital_simulation.py`·
  루트 마스터·provenance는 무변경.
- 수정: `비고`에는 `"신뢰도 낮음(발행잔액 vs BS 괴리)"`만 남기고, `reasons` 원문은 신설
  `_diagnostics` 컬럼으로 이동(`44ae5fb`). `export_public_sheets.py`의 `_DROP_COLS`에
  `_diagnostics` 추가 — 공개 다운로드만 제외, 내부 xlsx에는 남음.
- `sync_master_xlsx_sheet.py`에 "기존 시트에 신설 컬럼 추가"(순수 추가일 때만) 케이스를
  새로 지원(`a61c8b2`) — 자본비율전망 시트 sync. `public_exports` 재생성(`c130062`).
- 검증: 총 2090행 불변, jargon 660→0행, `_diagnostics` 제외 키로 재매칭한 '값' 컬럼
  불일치 0, `check_master_xlsx_drift.py` 드리프트 셀 0, `validate_live_artifacts.py`/
  `validate_data_contract.py` RED=0(YELLOW 전부 기존 baseline).
- validation에 재발방지 정규식 검사 제안(구현 안 함): `inbox/validation/20260921T0335Z`.
- 브랜치 `fix/csm-product-segmented-columns`에만 커밋, push 안 함(오케스트레이터/owner 판단 대기).

---

## 2026-09-21 — main 배포 5차 `92159dd`: K-ICS IQP ReferenceError 복구 + 금리민감도 9칸 + 가정민감도 caption (owner 지시 "고치고 나면 main 에 배포까지")

- 사고: 2차 배포 `2dbc4ca` 가 `K-ICS.html` 의 `function IQP()` 정의만 지우고 호출 2곳을 남김. 라이브 금리민감도
  패널 36/39사 ReferenceError, 같은 예외가 부팅 `.then` 을 죽여 `.catch` 가 세부항목 표를 오류 문구로 덮음.
  owner 가 라이나생명 2026.2Q 로 발견. 데이터 수정 0건(parser 원문 대조).
- 배포 5파일: `K-ICS.html` · `kics_rate_sensitivity.json`(789→798) · `data/dart/viz/sensitivity_heatmap.json` ·
  `public_exports/금리민감도.json` · `manifest.json`. 격리 워크트리 `deploy-20260921` cherry-push 후 제거.
- 게이트: 1차 FULL 은 뒷정리 3겹(xlsx 금리민감도 시트·viz_ifrs17_panels 지문·public_exports)으로 BLOCKED →
  `3633b21`·`273a4d8` 로 닫고 2차 FULL gate-clear(593 passed). 신설 §1f 배포 JS 런타임 게이트 RED=0.
- 라이브 검증: 블롭 5/5 일치 · 헤드리스 4사 렌더(세부항목 41행·민감도 7행·pageerror 0) · manifest build_id `3633b21`.
- 4차 배포(`3e9af35`·`8ba15d9`, 09-21 새벽) 기록을 TODO 에 소급 작성. Status 6개 이상 항목은
  `docs/todo_archive_publishing.md` 신설로 바이트 무수정 이동(재조립 cmp 3/3).
- 세션: Opus 5 오케스트레이터 직접(기계적 cherry-copy), 배포 소요 ~5분 + 게이트 2회 ~27분.


## 2026-09-17 — KR0073 2026.1Q 경과조치 후 지급여력비율 정정, main 배포 (owner 발주+승인)

FSS 보도자료(`R26090720.pdf`, 2026.9.17)와 `kics_disclosure.json` 대조(38개사×2분기×전/후 152칸,
항목27)에서 KR0073(교보생명) 2026.1Q 경과조치 후만 진짜 오류(214.23 vs 정답 211.39) 발견 — 26.1Q
원본 공시의 미정정 값이 26.2Q 공시의 정정 비교컬럼에 반영되지 않았다("적용후 컬럼 파싱 불안정"
사각의 구체 사례).

`scripts/fix_20260917_kr0073_2026q1_headline_afterapply.py`로 3칸 정정(item1/14/27_적용후).
부수효과로 R5_기준금액 적용후 항등식이 깨져(하위 세부항목은 재공시 안 됨) `validate_kics_disclosure.py`·
`validate_data_contract.py`에 `AFTER_IDENT_ISSUER_INCONSISTENT` documented-exception 등재부 신설
(잔차 938.25 박제, owner 승인 — 이 배터리는 R1/R2/R5/R6/R7/R8 중 R5만 해당, 나머지 축은 등재 없음).
`sync_master_xlsx_sheet.py "K-ICS공시"` xlsx 동기화. 게이트 `RED=0`(양쪽) 확인 후
`scripts/export_public_sheets.py` 재실행(`K-ICS공시.json`·`manifest.json`만 변경).

격리 워크트리(`../insurequant-main-deploy`, `origin/main` 기준) cherry-push — kics_disclosure.json
+ public_exports 2개 파일만, 커밋 `a84520c`. 라이브 검증: `kics_disclosure.json` 200, KR0073
2026.1Q item27_적용후="211.39" 확인. HTML 무수정, keep-list 밖 파일 섞임 없음.

## 2026-09-14 (2차) — 손보 2사 추가(24→26사) + `value_verified` UH-25 화면축 배선 (owner 승인)

두 가지 독립 변경, 둘 다 jp 범위.

**① 共栄火災海上保険·ヤマップネイチャランス損害保険 적재**: `J-ESR/nonlife_ratio_retry.json`(오케스트레이터가 원문 PDF로
독립 확인, 항등식 2/2)을 `J-ESR/merge_nonlife_ratio_census.py`에 override 소스로 배선(`load_retry()` 신설,
company_jp 매칭 시 A/B/C 그룹 원본 행을 통째로 대체, 고아 override는 `SystemExit`). `nonlife_ratio_census.json`
found 24→26·unreachable 3→1(大同火災만 잔존), 항등식 재검산 71건 중 불일치 0. `build_jesr_detail_json.py`
`RATIO_ONLY_ID_BY_JP`에 `kyoei_fire_marine`·`yamap_naturance` 2개 id 추가(caveat 없음) — `build_ratio_only_companies()`가
census를 그대로 읽어 26사를 자동 생성. census CSV(`fy2025_esr_census_20260912.csv`) 2행의 `disclosure_url`·
`doc_type`·`checked_at`·`notes` 갱신(`fy2025_esr_status`는 무변경 — 共栄火災=not_yet, ヤマップ=not_found 유지),
notes에 재현 가능한 방법 기록(共栄火災=TLS 중간인증서 보강, ヤマップ=Playwright route-intercept 우회). 행-인덱스
csv.reader/writer + utf-8-sig/LF 보존, git diff 2줄만 확인.

**② `value_verified` 계약**: `jp/jesr_esr.json`/`jp/jesr_detail.json`의 posted record마다
`{"state":"verified"|"unverified"|"exempt","reason":null|str}` 부착 — 판정은 재타이핑하지 않고 게이트 정본
`unverified_value_reasons()`·`load_source_exceptions()`을 그대로 재사용(`build_jesr_page_json.py`에
`compute_value_verified()`/`_exception_reason_by_key()`/`check_value_verified()` 신설). `build_jesr_detail_json.py`는
`public_by_en.get(company_en,{}).get("value_verified")`로 가져오고(비posted는 자동 None), ratio_only는 명시적
None + self_check 3중 강제. 오늘 기준 **16/16 전부 verified**(발화 0, 기대치와 일치). ④→⑤→④ 고정점 확인
(`generated_at` 제외 바이트 동일), ESR 16사 5필드 전건 diff 0. `pytest tests/test_jp_source_gate.py
tests/test_jp_deploy_matches_census.py` 127 passed, `scripts/prepush_check.py` REDUCED(jp-scope) gate-clear
(258 passed 2 skipped). commit/push 없음. 상세: `TODO_publishing.md` 2026-09-14 (2차) 항목.

---

## 2026-09-14 — 손보 손해율 24사 `jp/jesr_detail.json` ratio_only 레이어 + SOMPOダイレクト source_url 교체 (owner 승인)

배경: `J-ESR/nonlife_ratio_census.json`(손보 29사 전수조사, verdict `found` 24 / `not_applicable_holding` 2 /
`unreachable` 3, 오케스트레이터가 合算率 항등식 69/69 전건 검산 완료)을 `jp/jesr_detail.json`에 싣는 owner 승인
작업. HTML/CSS/`jesr_app.js`는 designer가 같은 라운드에 병행 — publishing은 JSON만.

**1) 24사 추가 (`J-ESR/build_jesr_detail_json.py` 확장)**: `EXTRACTED_PATH`(schema-item 추출) 파이프라인과는
완전히 분리된 새 함수 `build_ratio_only_companies()`를 신설해 `J-ESR/nonlife_ratio_census.json`을 직접 읽고
`build()`의 `companies_out`에 append(life_core_only 브랜치 뒤). 신규 계약 필드 2개(designer 합의):
- `data_scope: "ratio_only"` — 패널 스킵 신호. 기존 10사는 이 키 자체가 없음(="full" 취급).
- `ratio_caveat: {code, text} | null` — 4사만. `text`는 census의 `caveat` 필드를 **런타임에 그대로 복사**
  (하드코딩 재입력 금지, 전사 오류 방지). 코드 매핑만 하드코딩: トーア再保険→`lae_excluded`, ソニー損害保険→
  `ei_basis`, レスキュー損害保険→`ocr_read`, MS&ADインシュアランスグループHD→`simple_sum`.

shape는 sompo_japan(not_yet) 선례보다 한 단계 더 얕음: `profit.ratios`(pl_loss/expense/combined_ratio_pct,
cur=FY2025/prev=FY2024, FY2024 없으면 null)만 채우고 `profit.items`/`core`={}, 최상위 `capital`/`items`={},
`capital_tree`/`risk_tree`/`sensitivity`=[], `risk`/`market_sub`=스키마 키(`RISK_KEYS`/`MARKET_SUB_KEYS`)
전부 null, `aggregation`/`by_line`/`core_history`/`profit_flow`=null(life_core_only 선례 재사용), `bs`는
`build_bs_block(None)`을 그대로 호출(={"status":"not_obtained",...} — 기존 함수의 "비어있음" 표현을 재사용,
새 shape 발명 안 함), `headline`은 ESR 4필드 전부 null. `history`는 fiscal_years를 loss/expense/combined
3개 dict의 연도 합집합으로 구성(회사마다 2~5년, index 정렬 보장) + `hist_loss/expense/combined_ratio_pct`
3종만. `esr_status`는 `jp/jesr_esr.json`의 posted 레코드 멤버십으로 파생(census CSV 재파싱 안 함 — 24사
전원이 posted 아니면 not_yet뿐이라 이걸로 충분): MS&AD만 `posted`(랭킹엔 이미 실제 ESR 수치로 존재하지만
이 detail 레이어는 ratio만이라 headline은 여전히 null — 이 불일치는 후속 검토 대상으로 명시적으로 남김, 이번
티켓 범위 밖), 나머지 23사 `not_yet`.

`self_check`에 ratio_only 전용 블록 추가: 24건 카운트 + id 유일성 + `RATIO_ONLY_ID_BY_JP` 매핑 일치, esr-layer
블록(`capital`/`items`/`capital_tree`/`risk_tree`/`sensitivity`) 전부 빈값, `risk`/`market_sub` 전부 null,
headline ESR 3필드 null, `profit.items`/`core` 빈값, 合算率 항등식(loss+expense≈combined) **cur/prev 및
history series 전부 ±0.15 tol로 재검산**(census 검산과 동일 tolerance), caveat는 지정된 4사에만 붙었는지 확인.
기존 `n_posted != 2 or n_not_yet != 5` 구조 단언은 `data_scope != "ratio_only"`로 필터링해 그대로 유지 —
`_meta.coverage`의 `esr_posted`/`esr_not_yet`/`life_core_only`도 동일하게 분리하고 `ratio_only` /
`ratio_only_posted` / `ratio_only_not_yet` / `ratio_only_caveat` 4필드 신설.

**2) SOMPOダイレクト source_url 교체 (owner 승인)**: `J-ESR/fy2025_esr_census_20260912.csv`에서 분책
(`insgenjo2026_05.pdf`, 재산상황편 21p, 손해율 표 없음) → 전체책(`insgenjo2026.pdf`, 100p, 全冊)으로 교체.
행-인덱스 `csv.reader`/`csv.writer`로 편집(BOM·LF 라인엔딩 원본 그대로 보존, `diff` 1행만 확인). **교체 전
검증**: `J-ESR/jesr_http.get`으로 200 · `content-type: application/pdf` · 2,486,089 bytes 확인 → PyMuPDF로
본문 추출해 p9·p68에서 「正味損害率72.8%／正味事業費率24.3%」 직접 대조(`nonlife_ratio_census.json` B조 수치와
일치) → p64 5개년표 주석에서 esr not_yet 플레이스홀더("2025年度の単体ベースのソルベンシー・マージン比率の開示は
2026年10月末の予定です。")를 전체책에서도 재확인(`esr_status`는 `not_yet` 그대로, URL만 교체). `doc_type`에
"全冊" 표기 추가, `checked_at` 2026-09-14, `notes`에 교체 근거 기록.

**3) 파이프라인 순서 + 재실행 함정**: census 수정 → `check_source_urls.py --all`(dead=0) →
`check_esr_in_source.py --all`(found=16/not_found=0) → `build_jesr_page_json.py` 1차 →
`build_jesr_detail_json.py`(24사 추가) → **`build_jesr_page_json.py` 2차 재실행이 필수임을 이번에 발견**:
`_meta.group_children`이 `jp/jesr_detail.json`을 읽어 지주(연결)↔자회사(単体) 상세페이지를 잇는데, 1차 실행
시점엔 아직 24사가 jesr_detail에 없어 stale — `test_jp_deploy_matches_census.py`가 `_meta.group_children`
불일치로 이 순서 문제를 실제로 잡아냈다(재실행 후 Nisshin/Tokio Marine Direct/Aioi Nissay Dowa/Mitsui
Direct/Sompo Direct가 각 지주 아래 신규 연결됨). 고정점 확인(④⑤를 한 번씩 더 돌려 `generated_at` 제외 바이트
동일 재확인) → `pytest tests/test_jp_source_gate.py tests/test_jp_deploy_matches_census.py` **111 passed** →
`scripts/prepush_check.py` **REDUCED(jp-scope) gate-clear**(비교대상 13개 파일 전부 jp 범위, 242 passed
2 skipped). **ESR 16사 값 불변 확인**: `esr_pct`/`eligible_capital`/`required_capital`/`as_of`/`scope` 5필드
전건 실행 전/후 byte diff 0.

공유 워킹트리 메모: `jp/*.html`·`jesr_app.js`·`jp.css` 6개 파일이 이번 세션 내내 `git status`에 M으로 잡혔으나
이 세션은 그 파일들을 Read/Edit/Write한 적이 없음(designer 병렬 세션의 미커밋 변경) — 커밋 시 반드시 이 티켓의
7개 파일만 명시 add: `J-ESR/build_jesr_detail_json.py` · `J-ESR/esr_in_source_health.json` ·
`J-ESR/fy2025_esr_census_20260912.csv` · `J-ESR/jesr_master.json` · `J-ESR/source_url_health.json` ·
`jp/jesr_detail.json` · `jp/jesr_esr.json`. git commit/push는 오케스트레이터 소관, 이번 세션은 미실행.

모델: Sonnet 5. 소요: 약 45분(케이스 조사 15분 + 빌더 확장 20분 + 파이프라인 검증 10분).

## 2026-09-12 — J-ESR `/jp/` 페이지 데이터 JSON 신설 (`inbox/publishing/20260912T0446Z`)

배경: owner가 `/jp/` 일본어 ESR 현황 페이지 초안 킥오프(designer 병행 티켓 `inbox/designer/20260912T0446Z`). 화면 규칙
"그래프 데이터는 HTML 인라인 금지, JSON fetch"에 따라 페이지가 읽을 JSON을 publishing이 먼저 조립.

신규 `J-ESR/build_jesr_page_json.py` — stdlib만(csv/json/re/datetime/pathlib), self-check 내장(실패 시 exit 1).
입력은 `J-ESR/fy2025_esr_census_20260912.csv`(downloader 산출, 79사 census, utf-8-sig)의
`fy2025_esr_status == "posted"` 15행과, `J-ESR/jesr_sources_2026Q1.csv`(6월 수집 11사)의 보조 열(`ticker` ·
`total_assets_bn_jpy` · `target_pct` · `basis`)을 `company_jp`로 조인. 조인 규칙은 필드별로 다르게 뒀다: `ticker`는
상장코드라 시간불변이므로 무조건 조인, 나머지 세 필드는 sources 행의 `as_of`가 census 행의 `as_of`(2026-03-31)와
**일치할 때만** 조인했다 — 상호회사 4사(日本生命保険·住友生命保険·明治安田生命保険·富国生命保険)는 sources csv에
2025-03-31~2025-09-30 구분기 값만 있어서, as_of를 안 걸고 그대로 조인하면 새로 posted된 2026-03-31 수치에 옛 분기의
총자산/목표비율/basis 라벨이 잘못 붙는 사고가 난다("틀린 값을 싣느니 빈칸" 원칙 적용, CLAUDE.md). `preliminary`는
census `notes`+`doc_type` 문자열에 속보/잠정/速報 중 하나라도 있으면 true로 판정하고, 어느 키워드로 잡았는지를
`notes` 끝에 괄호로 남겼다(티켓 지시 "어느 표현을 잡았는지 notes에 남김" 반영). `doc_date`는 `doc_type` 문자열에서
정규식 3단(YYYY-MM-DD → YYYY年M月D日 → YYYY年M月) 파싱으로 추출 — 15건 전부 육안 대조 확인.

출력은 두 곳에 동일 바이트: `J-ESR/jesr_master.json`(2026-06 스키마를 전량 교체 — 이 스크립트가 유일한 생산자라
"마스터 통째 read-modify-write 금지" 원칙 예외 적용, 프롬프트·티켓 양쪽 명시)과 `jp/jesr_esr.json`(신규 `jp/` 폴더,
배포용 사본). 스키마는 designer와 합의된 고정 계약이라 키 이름은 손대지 않았고, 티켓이 derivation을 명시하지 않은
두 필드(`basis`는 조인 실패 시 상수 `"J-ICS"` 기본값, SOMPO만 sources 원본 `"J-ICS_VaR99.5"`를 그대로 반영)는
판단 근거를 답변 티켓에 남겼다.

실측 검증: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_page_json.py`
→ exit 0, `15 records`, `census: {total:79, posted:15, not_yet:62, not_found:2}`, `preliminary=5`
(LifeNet·朝日生命保険·富国生命保険·かんぽ生命保険·住友生命保険). `cmp J-ESR/jesr_master.json jp/jesr_esr.json` 바이트
동일. `head -c3 | xxd -p` 양쪽 `7b0d0a`(BOM 아님), 스크립트 자체도 `23202d`. `ast.parse` 통과. `git status --short
J-ESR/ jp/` = 정확히 3건(`M jesr_master.json` · `?? build_jesr_page_json.py` · `?? jp/`) — 루트 마스터·HTML·xlsx·
public_exports·keep-list 무변경 확인(티켓 4번 제약 준수).

**라이브 미반영(이번 범위 밖)** — 필요 항목 3가지를 조사해 답변 티켓에 기록:
1. keep-list(§1/§9) 신규 페이지 경로 추가 필요. **실측**: 4-페이지 하드코딩(`["index.html","K-ICS.html","IFRS17.html",
   "공시보고서.html"]`)이 `claude-agent-publishing.md` §1 grep 스니펫 · `tests/test_deploy_assets.py:27` `PAGES` ·
   `tests/test_push_gate_wiring.py:378` `_HTML` 세 곳에 그대로 박혀 있어, `/jp/` 페이지를 여기 추가하지 않으면 그
   fetch가 세 게이트 어디서도 "통과"가 아니라 아예 안 보이게 된다(불변식 1번: 게이트가 보는 파일=사용자가 보는 파일).
2. master xlsx 신규 시트는 불요 — `scripts/build_master_xlsx.py`의 `MASTERS`, `scripts/sync_master_xlsx_sheet.py`
   둘 다 "jesr" grep 매치 0(J-ESR은 K-ICS/IFRS17 xlsx 체계 밖 독립 트랙). 시트를 만들지는 owner 결정 사항으로 남김.
3. `scripts/status_report.py` §4("화면 fetch ↔ 마스터 시트")는 1번의 `_HTML`을 갱신하기 전까지 `jp/jesr_esr.json`
   fetch 자체를 못 보므로 지금은 무검사 상태 — 갱신하는 순간 `MASTERS`에 대응 시트가 없어 GAP으로 잡힐 것(2번과 연결).

티켓 `status: answered`로 전환(`_resolved/` 이동은 owner 확인 후). 서브에이전트 생성 없이 직접 처리.

---

## 2026-09-11 — 지식재산 보호 0원 조치, 저장소 쪽 (LICENSE · robots.txt · manifest 지문 · 투자기록 · IR xlsx 추적해제 · 상시유지 파일 배선)

배경: `artifacts/legal/ip_protection_report_20260911.md`(등록권리 없는 개인 운영 사이트가 지금
자동으로 가진 권리 = 저작권 + 데이터베이스제작자권 + 도메인, 그 중 0원으로 강화되는 것들).
owner 지시 3개: 약관 페이지 따로 만들지 말 것(privacy.html 에 추가, designer), 실명 조상욱 OK,
**진입장벽 낮게**(동의 절차·팝업 추가 금지, 금지 항목은 자동수집·대량재배포 둘만). 화면·JS 는
designer 가 같은 시간에 작업했고 이 항목은 publishing 소관 파일만 다룬다. commit/push 없음.

**① `LICENSE`(루트, 신설).** 19줄, 한국어 본문 + 영어 요약. All rights reserved 이되 허용 범위를
먼저 적었다(열람·캡처, 출처 표기 인용, 사내 분석). 금지는 둘 — 자동화 수단으로 통째 수집, 대량
재배포·재판매·유사 서비스 구축. 저작권법 제4장의2 데이터베이스제작자권 고지("개별 수치가 공개
사실이라는 점은 DB 전체·상당부분 권리에 영향 없음"), 원천 권리는 각 공시 주체, 전문 링크
`privacy.html#terms`, 운영자 조상욱 2026. 조문식 "제N조" 안 씀.

**② `robots.txt`.** 기존 상단 주석(keep-list 는 HTML grep 도출이라 이 파일은 상시 유지) 살림.
`User-agent: *` 는 `Allow: /` 유지 + `Disallow: /public_exports/`(다운로드 방명록 스냅샷 —
렌더링에 안 쓰여 색인 불필요; 루트 `*.json` 은 렌더링 리소스라 **일부러 안 막음**). AI **학습용**
크롤러 8종(GPTBot·CCBot·ClaudeBot·anthropic-ai·Google-Extended·Bytespider·meta-externalagent·
Applebot-Extended)만 `Disallow: /`. 보고서 초안에 있던 ChatGPT-User·PerplexityBot 은 **뺐다** —
사용자가 질문할 때 대신 읽어 오는 fetcher 라 막으면 AI 검색 유입이 끊긴다(owner 편의 원칙).

**③ `public_exports/manifest.json` 지문.** 생성 스크립트는 `scripts/export_public_sheets.py`
(`grep manifest.json scripts/` 로 확인). designer 가 먼저 `license`(URL)·`build_id`(HEAD short
sha) 를 넣어 두어 그 위에 얹었다: `license` 는 조건 문장으로, `terms_url`·`copyright` 추가.
안전 근거 두 개를 코드 주석으로 남김 — download-survey.js 는 `sheets`·`generated_at_utc`
(+`build_id` 있을 때만) 만 읽고, `validate_live_artifacts.py` CHECK 6(L636-663) 은
`man["sheets"]` 만 대조하므로 top-level 키 추가는 둘 다 안 깨진다. 재실행 결과: 13개 시트
스냅샷 **바이트 동일**(HEAD 대비 드리프트 0), `manifest.json` 만 +5줄. xlsx 표지 "이용 조건"
행은 **클라이언트**(`download-survey.js buildCoverSheet`) 가 만들고 designer 가 이미 넣었으므로
publishing 은 손대지 않았다. 이 경로엔 마스터 xlsx 가 없어 수식 캐시 위험 0.

**④ `docs/ip/investment_record.md` + `scripts/measure_investment_record.py`.** "상당한 투자"
증거 1장. 추정치 없이 전부 잰다(git log/rev-list, os.walk 줄 수, 골든 fixture `by_rule`,
`rule="…"` 리터럴, 마스터는 `git show HEAD:` 로 읽어 동시 세션 반쯤 쓴 파일 배제, 원천 파일은
디스크 census). 첫 실행에서 회사 수가 전부 0 으로 나왔다 — 회사 키가 `회사명` 이 아니라 13개
공통 `원보험사코드` 였다(export 단계에서 드롭되는 키라 눈에 안 띔). 고쳐서 39사 확인. 실측 요약:
첫 커밋 2025-09-15 · 561 커밋 · 57 작업일 · scripts 278파일 84,175줄(+probes 1,295파일) ·
src 33/8,822 · tests 41/10,392 · K-ICS 룰 id 30, findings 16,140 · validator rule id 123 ·
골든 8 · 테스트 함수 266 · 마스터 13개 53,530행 · 39사 · 16분기 · 공시 PDF 550 · DART raw 1,297 ·
KIDI 548 · gold xlsx 44 · `_gold` 22 · resolved 티켓 386 · 포스트모템 10. 갱신 명령을 문서 맨 위에
박아 분기마다 같은 축으로 다시 잰다.

**⑤ IR xlsx 추적 해제.** `git ls-files 'data/ir/**/*.xlsx'` = 11(전부 FY2026_Q2 팩트시트, 각
보험사 저작물). 읽는 코드 전수 grep: `crawl_ir_db.py`·`_build_lob_cross_check.py`·
`check_data_file_integrity.py`·`download_ir_*.py` 전부 **디스크 경로**, `git show` 로 data/ir 를
읽는 곳 0 → `git rm --cached` 11건(디스크 잔존 확인 11), `.gitignore` 에 `data/ir/**/*.xlsx` +
사유 주석. 이력 purge 는 하지 않음(owner 결정, 현 PC push 불가 사정도). main 에는 원래 없음.

**⑥ "HTML 무참조 상시 유지 파일" 배선 — LICENSE 의 keep-list 등록 근거.** §1 keep-list 는
HTML grep 으로 도출되는데 `LICENSE` 는 아무 HTML 도 참조하지 않는다. 그러나 공개 `main` 이 곧
GitHub 공개 저장소이고 `https://www.insurequant.com/LICENSE` 로도 열리므로 거기 없으면 의미가
없다 → robots.txt·`.nojekyll`·CNAME 과 같은 부류. designer changelog 2026-09-11 "미배선 잔여"
(robots.txt 상시 유지를 문서·테스트에 배선, publishing 소관)가 정확히 이 작업이라 같이 처리:
`claude-agent-publishing.md` §1 에 표 신설 + §9 스냅샷에 `.nojekyll`·`LICENSE`·`robots.txt`·
`sitemap.xml` 5줄, `docs/launch_runbook.md` §2 에 소절 신설(robots.txt 주석이 가리키던 절이
실제로는 없었다), `tests/test_deploy_assets.py::test_always_keep_files_exist_and_are_documented`
— `ALWAYS_KEEP` 5개의 존재·BOM 없음·두 문서 등재를 강제. "배선했다 ≠ 강제된다" 원칙대로 테스트가
정본이고 문서는 테스트가 검사하는 대상이다. `pytest tests/test_deploy_assets.py` **11 passed**.

**다음 배포 주의.** §3 절차 2) 의 `git checkout <branch> -- …` 목록에 `LICENSE`·`robots.txt` 를
넣을 것 — 둘 다 grep 으로는 안 나온다.

## 2026-08-25 — 소진율 100% 캡을 데이터에서 걷어냈다 — owner 2026-06-14 결정 이행 (`20260825T1130Z` iter2)

validation 재확인(iter 2)에서 **캡의 근거가 뒤집힌 owner 결정**이라는 것이 확인돼 처리했다.
커밋/푸시 없음.

**owner 원문.** *"raw data 에선 144% 로 살리고 K-ICS.html 에서 보여줄 땐 100%+ 로 표시하라."*
`docs/changelog_designer.md:783-789`(2026-06-14 후속3, 직전 "구현 취소"의 **번복**) ·
`docs/agents/claude-agent-designer.md:177` LOCKED. 논거: 분자(발행액)=KOFIA/DART per-bond,
분모(인정한도)=공시 SCR 기반 → **소스가 독립이라 사전 100% cap 이 애초 불가능**하다.
자르는 것은 **도넛 원호뿐**(360° 한계, `K-ICS.html:833`)이고 숫자는 생짜로 둔다.

**무엇이 어긋나 있었나.** 데이터 쪽이 정반대로 구현돼 있었다 —
`wire_capital_securities_to_utilization.py:122` 가 `min(x["t1_util"], 100.0)`. 그래서
`K-ICS.html:841/879` 의 `pct > 100` 분기가 **영영 거짓**이 되어 `100%+` 표기와 툴팁 실제값이
죽어 있었다. 2026-07-22 `a629e34` 로 인라인 JSON 이 fetch 로 분리되며 데이터쪽 캡이 화면에
도달했고, 같은 날 앞선 배포본 동기화로 0.0% 가 걷히면서 비로소 6사가 전부 그 캡에 걸렸다.

**tier1/tier2 비대칭이 스스로 증거였다.** 같은 빌더의 L140 은 tier2 를 `x["t2_util"]` 그대로
통과시키고 L149 에서 `>100` 이면 `quality_flag="util_over_100_legit"` 를 붙인다. tier2 쪽이
owner 결정에 맞다.

**고친 곳 (6개).**

| # | 파일 | 무엇 |
|---|---|---|
| 1 | `scripts/wire_capital_securities_to_utilization.py:122` | `min(x["t1_util"], 100.0)` → `x["t1_util"]`. 근거 주석 동봉. `utilization_pct_raw` 는 하위호환 별칭으로 유지(캡 제거 후 항상 동일) |
| 2 | `scripts/validate_live_artifacts.py:465` | 항등식 `min(100, n/lim×100)` → `n/lim×100`, RED 메시지 문구도 정정. 옛 주석(캡이 owner 결정이라던 것)을 정반대 사실로 교체 |
| 3 | `scripts/compute_tier1_utilization.py` | **상류 빌더에도 같은 캡이 있었다** — L412 primary·L414 strict 둘 다 제거. `utilization_cap` 정의 문구 재작성 |
| 4 | `scripts/forward_capital_simulation.py:321` | 고치지 않고 **사유를 그 자리에** — tier2 전용 한도초과 판정이고 tier2 는 애초에 안 잘렸다. 같은 스크립트가 tier1 파일도 읽지만 `_pick_kics_t1_baseline` 은 금액 필드(`issued`/`recognized`)만 본다 |
| 5 | `docs/tier1_hybrid_utilization_definition.md` | 소진율 4필드 의미 표 + "왜 캡이 없나" 절 신설 |
| 6 | 배포본 2개 | `sync_tier_utilization_to_deploy.py --apply` |

> **3번을 발주 범위 밖인데 왜 같이 고쳤나.** 발주는 `compute_tier1_utilization.py:484` 의 **문구**만
> 고치라고 했다. 그런데 그 빌더는 `utilization_pct` 만 자르고 `tier1_hybrid_recognized_eok` 는
> 안 자른다 — 2번으로 새로 세운 항등식이 **다음 분기에 그 빌더를 돌리는 날 바로 RED** 로 뜬다.
> 문구와 코드가 다시 어긋나므로 같이 고쳤다. 현재 배포본은 `wire_` 가 덮어쓰므로 이 변경이
> 지금 값에 주는 영향은 0(빌더 산출물 diff 로 확인).

**6사 before → after.** 분자(발행액)·분모(한도)는 **불변**, 잘려 있던 비율 하나만 바뀐다.

| 회사 | 데이터 before → after | 화면 before → after | 툴팁 after |
|---|---|---|---|
| NH농협손해보험 | 100.0 → **192.9** | `100%` → `100%+` | `사용: 100%+ (실제 192.9% · 발행액이 인정한도 초과)` |
| 하나생명보험 | 100.0 → **187.0** | `100%` → `100%+` | 〃 187.0% |
| 하나손해보험 | 100.0 → **144.1** | `100%` → `100%+` | 〃 144.1% |
| 코리안리재보험 | 100.0 → **139.8** | `100%` → `100%+` | 〃 139.8% |
| 한화생명 | 100.0 → **138.5** | `100%` → `100%+` | 〃 138.5% |
| 케이디비생명보험 | 100.0 → **113.4** | `100%` → `100%+` | 〃 113.4% |

`git diff kics_tier1_utilization.json` = **6줄**(값만). tier2 배포본은 `차이 없음 (in sync)`,
tier2 빌더 산출물은 **바이트 동일**.

**`utilization_pct` 소비처 전수 grep — ≤100 가정 잔존 0.** `K-ICS.html:906/907`(이제 `pct > 100`
분기가 살아남) · `validate_live_artifacts.py:457/501` · `validate_data_contract.py:1535`(R-T2-UTIL,
**tier2 전용**이라 의미 불변) · `forward_capital_simulation.py:321`(tier2 전용, 사유 기록) ·
`compute_tier2_utilization.py:504-505`(tier2 진단 리포트) · `sync_tier_utilization_to_deploy.py`
(값 미참조) · `_data_contract_selftest.py`(tier2 픽스처).

**필드 의미 (문서화).** `utilization_pct` = 표시 정본(캡 없음) · `utilization_pct_raw` = 캡 시절
잔재인 하위호환 별칭(이제 항상 동일) · `utilization_pct_strict` = 분모만 SCR×10% 인 참고치(정의상
1.5배) · `tier1_hybrid_overflow_eok` = 발행액−한도 **금액**(규정 다.(1) 재분류분, tier2 분자로 감).
비율 3개와 금액 1개라 의미 충돌 없음.

**화면 확인 — 직접 띄웠다.** `python -m http.server 8889` + Playwright headless Chromium 으로
`K-ICS.html` 로드, **회사 선택은 실제 `<select id="company">` 조작**(`select_option`). **HTML 무수정.**

- 도넛 가운데 텍스트: 6사 전부 `100%+` (캔버스 렌더 스크린샷으로 눈으로 확인).
- 툴팁: Chart.js 콜백 반환 문자열을 6사 전부 추출 — `사용: 100%+ (실제 144.1% · 발행액이
  인정한도 초과)` 형태로 **실제값 병기**.
- 원호: `datasets[0].data == [100, 0]` — 360° 한계로 원호만 캡되는 것도 의도대로.
- 하단 노트: `기본자본: 발행 1,000억원 / 한도 694억원 (SCR×15%)` — 분자·분모 원값.
- 대조군 삼성화재해상보험(발행 0): `0%` · `사용: 0.00%` 정상.

**게이트로 고정했다 (변이시험).** 문서가 아니라 게이트로 막히는지 확인했다(바이트 백업 → 변이 →
게이트 → 복원, sha256 일치·`git status` 청결).

| 변이 | 게이트 | 결과 |
|---|---|---|
| 배포본 tier1 의 >100 인 6사를 100.0 으로 되돌림(캡 재도입 재현) | `validate_live_artifacts` **exit 2** | `TIER_UTILIZATION_IDENTITY` 6 + `TIER_DEPLOYED_VALUE_DIFFERS` 6 |
| 복원 후 | **exit 0** | `RED=0 STALE_BASELINE=0` |

캡을 다시 넣으면 push 가 막힌다. 덤으로 항등식이 `min` 을 벗으면서 **조여졌다** — 이전에는 분자가
한도보다 크기만 하면 어떤 값이든 100 과 맞아떨어져 통과했다.

**owner 승인 대상**: 도넛 6칸이 `100%` → `100%+` 로 바뀐다(툴팁에 실제값 병기). 값을 바꾸는 것이
아니라 2026-06-14 결정을 이행하는 것이다.

**게이트 최종.** `scripts/prepush_check.py` **exit 0** —
`gate RED=0 · K-ICS rule gate=clear · domain gates=pass · DART raw 유실=0 · inbox 기계적위반=0 ·
offline tests 230 passed / 1 skipped → gate-clear`. 문서·티켓 편집까지 끝낸 **최종 트리에서 재실행**한
값이다(편집 전 1회, 편집 후 확인용 1회 — 두 번 다 exit 0). `emit_capsec_provenance.py --check` =
0 out of sync. `git status` 에 **HTML 4개 전부 없음**(무수정).

> **공유 트리 단서(숨기지 않는다).** `scripts/validate_live_artifacts.py` 한 파일에 두 세션의 변경이
> 섞여 있다 — 내 것은 `check_tier_utilization` 의 소진율 항등식 훅뿐이고, `RULE_REASON` 의
> `INSPL_CSM_AMORT_BAND` 사유 문구 확장은 **다른 세션의 미커밋 변경**이다(HEAD 에 없음). 커밋 시
> 파일 통째가 아니라 훅 단위로 골라 담아야 한다. `PL_breakdown.json` · `data/_gold/user_pl_cells.json` ·
> `data/dart/viz/*` · `scripts/viz_build_ifrs17_panels.py` 도 다른 세션 것이라 건드리지 않았다.

---

## 2026-08-25 — 자본증권 소진율 도넛이 4사를 "발행 없음 0%"로 그리고 있었다 — 조립 단계 부재 (`20260825T1130Z`)

validation 티켓 처리. **라이브 화면 오표시 수정.** 커밋/푸시 없음(owner 승인은 오케스트레이터 몫).

**원인 — 한 문장.** 빌더 산출물 `output/tier{1,2}_utilization/*_20261Q.json` 에서 배포본 루트
`kics_tier{1,2}_utilization.json` 을 갱신하는 **조립 스크립트가 이 저장소에 존재한 적이 없었다.**
루트 파일은 2026-07-22 `a629e34`(K-ICS.html 인라인 JSON 147KB 분리) 때 손으로 한 번 복사된
스냅샷이고, 2026-08-03 `cb084e7` 로 DART per-bond 소스가 24사→39사로 늘어나
`wire_capital_securities_to_utilization.py` 가 빌더 산출물을 갱신하는 동안 배포본은 옛 0 을 유지했다.

**추측하지 않고 확정한 방법.** 티켓은 "조립 경로에 분자 필드를 떨어뜨리는 자리가 있는 것으로 보인다"
고 했고, 발주에는 `issued_source: "bs_transposed"` 폴백 가설이 붙어 있었다. **둘 다 틀렸다** —
떨어뜨리는 자리가 있었던 게 아니라 **경로 자체가 없었고**, `issued_source` 는 `wire_` 이전 레거시
잔재라 소진율 계산에 쓰이지 않는다(분자는 `data/bonds/` per-bond 에서만 온다). 확정 근거 4개:
① 배포본을 **쓰는** 코드 전수 grep = 0곳(`emit_capsec_provenance.py` 는 사이드카 발행용으로 읽기만),
② `git diff a629e34 -- <두 파일>` 이 비어 있음(2026-07-22 이후 한 번도 안 바뀜),
③ `wire_capital_securities_to_utilization.py` **재실행 → 빌더 산출물 바이트 동일**(diff 0) = 빌더
쪽이 현재 소스로 재현되는 최신값이고 배포본이 낡은 쪽,
④ `data/bonds/capital_securities_fy2025.json` 에 해당 채권 실물 확인(하나손해 신종 1,000억
2024-05-14 발행 = post-K-ICS 신규 / IBK연금 후순위 4건 중 3건 pre-2023 면제 1,597.3억 + 1건
2023-03-30 신규 / 아이엠라이프 신종 948.8억 2022-03-30 = 전액 면제).
그리고 이 채권들이 들어온 시점이 바로 `inbox/_resolved/20260803T0310Z`(owner, KR0050·KR0076 을
`absent_in_source` 로 특정한 커버리지 census 건)다 — 상류는 그때 고쳤는데 **배포본만 안 따라갔다.**

**전수 확인(39사 × 2파일 = 78행, 필드 단위).** 회사 결측·초과 0. 어긋난 곳 **5사 / 25필드**,
전부 `배포본 0 → 빌더 값 있음` **한 방향**이다 — 반대 방향 0건이라 배포본에만 있던 값은 없고
통째 교체로 잃는 것이 없음을 먼저 증명한 뒤에 썼다.

| 회사 | tier1 | tier2 | 화면 |
|---|---|---|---|
| KR0050 하나손해보험 | 6필드 | 3필드 | ✅ 양쪽 |
| KR0076 아이엠라이프생명보험 | 1필드(면제분) | 8필드 | ✅ tier2 만 |
| KR1011 IBK연금보험 | — | 6필드 | ✅ tier2 만 |
| KR0049 악사손해보험 | — | 1필드(gross) | ❌ |

**티켓·발주의 "3사 tier1 소진율 0" 은 tier1/tier2 혼동이다.** tier1 에서 실제로 화면이 바뀌는
회사는 **하나손해보험 1사뿐**이고, 나머지의 0.0% 는 정답이다 — 아이엠라이프는 신종이 전액
pre-2023 경과조치 면제(신규 분자 0 이 맞다), IBK연금은 신종 발행 자체가 없고, 악사는 유일한
후순위의 call 이 2025-12-31 로 as-of(2026-03-31) 이전이라 잔존만기 직선상각 인정액이 0 이다.
**0 이 전부 버그인 것은 아니다** — 회사별 실데이터로 갈랐다(`feedback_no_category_assumptions`).

**화면 before/after** (K-ICS.html `updateDonutPanel` L906-917 이 읽는 필드만):

| 회사 | 패널 | before | after |
|---|---|---|---|
| 하나손해보험 | tier1 소진율 / 발행액 | 0.0% / 0억 | **100.0%** / 1,000억 (한도 693.9억) |
| 하나손해보험 | tier2 소진율 / 인정액 | 0.0% / 0억 | **13.2%** / 306.1억 (한도 2,313억) |
| 아이엠라이프생명보험 | tier2 소진율 / 인정액 | 0.0% / 0억 | **40.6%** / 1,324.3억 (한도 3,262.5억) |
| IBK연금보험 | tier2 소진율 / 인정액 | 0.0% / 0억 | **22.2%** / 797.8억 (한도 3,598억) |

한도(분모)는 before/after 전부 동일 — 바뀐 것은 분자뿐이다. 하나손해 tier1 은 raw 144.1% 를 owner
결정대로 100 에서 자른 값이다(`reference_kics_capital_tiering`).

**조치 — 빠진 단계를 만들었다.** `scripts/sync_tier_utilization_to_deploy.py` 신설. 기본 dry-run
(필드 단위 전건 열거 + 화면 필드에 `*SCREEN*` 표시), `--apply` 로 반영. 배포본 포맷
(indent=1 · CRLF · BOM 없음)을 보존해 **git diff 가 값 25줄만** 나온다(포맷 churn 0 — 값 변경과
재직렬화 노이즈가 섞이면 리뷰가 불가능해진다). `docs/agents/claude-agent-publishing.md` §2.1 에
`compute_tier{1,2}_utilization.py` → `wire_capital_securities_to_utilization.py` → **이 sync** 3단
체인으로 명문화했다. **표에 없던 것이 실행되지 않은 것이 이 사고의 전부**라, 고친 값보다 이 줄이
본체다.

**등재 해제.** `data/_gold/live_artifact_baseline.json` 에서 `TIER_DEPLOYED_VALUE_DIFFERS` 4건 +
`_counts` 2키 삭제, `_promote` 라우팅 문장에서 tier 절 제거. 등재부 `_promote` (1) 절차 그대로 —
고친 뒤 게이트가 `BASELINE STALE 4건` 으로 알려준 것을 확인하고 지웠다(안 지우면 등재부가
거짓말을 시작한다). `RED=0 YELLOW 1086 → 1082`, `STALE_BASELINE 0 → 4 → 0`.

**티켓 §2 (`NB_CSM_multiple.json` 2026.2Q) 는 못 고친다 — 원천 부재.** `build_nb_csm_multiple.py`
의 분모 `data/kidi/premium_summary.json` 이 디스크에 없고(gitignore 대상이라 git 복구도 불가),
`data/kidi/FY2026_Q2/` 도 없다(있는 것은 FY2023_Q1~FY2026_Q1). 빌더는 `load_wolnap()` 의
`KIDI.read_text` 에서 즉사한다. 강행 가정을 따져 봐도 안 된다 — 분모 없이 돌리면 2026.2Q 행은
생기되 배수가 전부 null 이라 버블맵 Y축이 안 그려지고(결측 31건이 "배수 null 31건"으로 모양만
바뀐다), 이 빌더는 파일을 통째로 새로 쓰므로 **기존 2023~2026.1Q 의 월납·배수까지 날아간다**
(마스터 통째 read-modify-write 유실형 — `project_master_json_lost_update`). 막힌 지점 = KIDI
재수집이고 그건 owner 보류 사안이라(`reference_kidi_premium_summary_gap`: 재요청 전 먼저 물을 것)
owner 판단으로 올렸다. `NB_CENSUS_MISSING` 31건은 등재 유지.

**검증**: sync 재실행 `차이 없음(in sync)` · `validate_live_artifacts` RED=0 STALE=0 ·
`emit_capsec_provenance.py --check` 0 out of sync · `pytest test_deploy_assets.py
test_push_gate_wiring.py` 55 passed · 편집 파일 전부 UTF-8 BOM 없음 ·
**HTML 무수정**(designer 소관 경계 준수).

**게이트 — 통과했다, 그리고 지금 트리는 남의 작업으로 막혀 있다(둘 다 사실이라 둘 다 쓴다).**
내 변경(배포본 2 + baseline)만 워킹트리에 있던 상태의 전체 `prepush_check.py` 는 **exit 0**
(`RED=0 · K-ICS clear · domain pass · inbox 위반 0 · offline tests 198 passed`). 문서·스크립트
편집을 마친 뒤 확인용으로 다시 돌린 실행은 **exit 2** 인데, 그 사이 **다른 세션이
`PL_breakdown.json` · `data/_gold/user_pl_cells.json` 을 수정**했다(KR0070 에이비엘생명 item7
재계산 — item4 override 가 residual item7 을 재계산하지 않아 깨져 있던 PL_BRIDGE 등식 수정,
`inbox/parser/20260825T1120Z`). 실패 테스트는 `test_master_tables_golden.py` **한 건**, 델타는
**`pl_bridge:2503P/26F → 2513P/16F`** 하나뿐 — PL_BRIDGE 실패 10건이 통과로 바뀐 것이라
**개선이 골든에 아직 반영되지 않은 상태**다. 나머지 카운트(coverage_hole · closing · crosscheck ·
zero_legs · qoq · sens)는 전부 골든과 일치한다. 내 변경집합은 tier 배포본·baseline·문서·신설
스크립트라 **PL 축에 입력을 주지 않는다.** 골든 `--update` 는 그 수정의 소유자(parser/ifrs17)
몫이라 손대지 않았다 — 남의 레인 골든을 대신 재생성하면 진행 중인 작업을 반쯤 박제한다.

공유 트리 주의: 위 두 파일 외에 `scripts/validate_data_contract.py` · `scripts/prepush_check.py`
(신설 단계 `DART raw 유실` 이 두 실행 사이에 들어왔다)도 다른 세션이 수정 중이라 손대지 않았다.
커밋 시 내 파일만 골라 담을 것: `kics_tier{1,2}_utilization.json` ·
`data/_gold/live_artifact_baseline.json` · `scripts/sync_tier_utilization_to_deploy.py` ·
`docs/agents/claude-agent-publishing.md` · `TODO_publishing.md` · 이 changelog · 티켓 md.

---

## 2026-08-25 — 이상치 발견이 게이트에서 분리된 뒤의 프롬프트 정합 + 실행 주기 확정 (`20260825T0130Z`)

validation 티켓 처리. 코드 미수정, 문서·프로세스 작업. 커밋/푸시 없음(오케스트레이터 몫).

**배경.** owner 지시("씰데없는 룰들은 좀 쳐내")로 커밋 `22697c2`에서 일반 이상치 발견/트리아지가 push 게이트에서 빠졌다. **삭제가 아니라 이전** — `scripts/scan_generic_anomalies.py`로 내려갔고 산출 경로(`data/_derived/anomaly_{triage,skeptic_input}.json`)는 그대로다. 근거는 실측: 이 층이 데이터계약 게이트 YELLOW 297건 중 224건(75.4%)과 리뷰 큐 83건을 매 실행 재생산하면서 **RED을 한 건도 낸 적이 없다**(YELLOW 전용이라 `blocked = n_red or n_hyg or n_test or n_kics or n_dom`에 애초에 항이 없다).

**티켓 주장 전건 코드 대조.** 액면으로 받지 않고 확인했고 전부 맞았다 — `validate_data_contract.py:2378`이 주석 처리된 `# check_generic_anomalies(res, env)`, `prepush_check.py:151`의 `blocked` 식에 이상치 항 부재, `test_push_gate_wiring.py:178`에 되살리기용 선언 존재.

**정정한 stale 문장 4개** (§3): ① `"Runs: ① data-contract hard gate ... + ② generic-anomaly triage chain"` — ②가 없을 뿐 아니라 **①만 적힌 것도 이미 stale이었다**(2026-08-21에 들어간 ①b K-ICS 룰게이트·①c 도메인게이트 4종·③ inbox 위생·④ 오프라인 테스트가 통째로 누락). ② `"Outputs: ... anomaly_triage.json + anomaly_skeptic_input.json"` — 파일은 맞지만 주어(`prepush_check.py`가 만든다)가 틀림. ③ `"LLM-skeptic step (mandatory — ... before recommending push)"` + `"Push recommendation forbidden without completing skeptic step."` — 가장 위험했다. 입력을 만들어 주던 단계가 사라진 채 금지 문장만 남아, 다음 세션이 없는 산출물을 기다리다 배포를 못 하거나 그 문장을 통째로 무시하는 두 결말밖에 없었다(실제로 skeptic 입력 83건은 2026-06 이후 미분류 방치 상태 — 그 문장대로면 이후 배포 10여 건이 전부 계약 위반이 된다). ④ 라이브 수치(REAL=73/입력 79) — 실측 REAL=77 UNCERTAIN=6 NOISE=134 OWNER_CONFIRMED=8, 입력 83. 아울러 §3.0에 박혀 있던 **캐시된 "Current live: RED=0" 줄을 아예 없앴다** — 이번에 `prepush_check.py`를 돌리지 않았고(~5분, 병렬 세션이 게이트 코드 작업 중), 무엇보다 **날짜 박힌 통과 기록이 다음 세션에 배포 허가로 읽힌다**. 대신 "돌리지 않은 게이트 판정을 인용하지 말라"를 명문화했다.

**결정 — 분기 라운드 1회 (§3.0b 신설).** 세 선택지(주기 배치 / owner 요청 시에만 / 폐지) 중 **주기 배치**. 근거: 이 층이 데이터 수정을 낳은 것은 2026-06-19/20 **한 라운드뿐**이고(교보생명 원수예실차 4분기·BNP파리바카디프 단위오류 1.77조·코리안리 중복 43·교보라이프플래닛 보험금융손익) 이후 증분 push 두 달간 0건 — 가치가 대량 적재 시점에 몰려 있으니 그 시점에만 비용을 낸다. **폐지 기각**: 산술 게이트는 내부적으로 닫히는 단위오류(BNP 1.77조가 정확히 그 종류 — 항등식은 성립하는데 자릿수가 틀림)를 못 잡고, 코호트 스캔이 그 층의 유일한 룰이다. **"owner 요청 시에만" 기각**: 문서에만 있고 아무도 안 부르는 단계가 이 저장소의 반복 실패형태다(`prepush_check.py` 호출처 0곳 사건). 명문화한 것 = 주체(publishing) · 4개 트리거(분기 라운드 첫 push 전 / 새 마스터 온보딩 직후 — 신규 마스터는 자기 이력이 없어 코호트 스캔이 유일한 검사다 / 빌더 대개편·±100행 뒤채움 / owner 요청) · 증분 push 제외 · **기록이 단계의 일부**(라운드 리포트에 anomaly 줄이 없으면 건너뛴 것이고 그 자체가 지적 대상) · skeptic 판정은 그 자체로 push를 막지 않고 inbox 티켓을 만든다(그래야 §3.0의 "RED=0 아니면 BLOCKED"와 모순되지 않는다).

**스캐너 실측.** `--no-write`로 실행(산출 JSON 2개가 git 추적 대상이라 그냥 돌리면 워킹트리가 더러워지고 병렬 세션이 있었다): 후보 224건(ANOMALY_PEER_OUTLIER 147 · ANOMALY_COHORT_ZERO 77, RED=0) → 트리아지 REAL=77 UNCERTAIN=6 NOISE 134 OWNER_CONFIRMED 8. 티켓 재현 수치와 일치. **판독성 평가**: 룰별 집계 → 예시 8건(회사·분기·사유 한 줄) → 트리아지 4버킷 → 다음 단계 안내까지 단독 실행물로 읽을 만하다. **다만 화면에 나오는 건 224건 중 앞 8건뿐이고 정작 조치 대상 83건은 JSON에만 있다** — 게이트 안에 있을 땐 파이프라인이 파일을 읽었지만 손으로 돌리는 스크립트는 터미널이 곧 UI다. 하드닝 룰상 skeptic 스코프인 UNCERTAIN 6건은 전건 인쇄돼야 한다(6줄). 코드 미수정, 스크립트 소유자(validation)에 권고만.

**부수 발견 — 같은 병에 걸린 다른 사본.** grep 범위를 `.py`/`.claude/skills`까지 넓히다 **무관한 stale 사실**을 4곳에서 찾았다: `"prepush_check.py는 validate_kics_disclosure.py를 호출하지 않는다"`. 2026-08-21에 단계 1b로 배선돼(`prepush_check.py:46-57`, `n_kics`가 `blocked`에 들어간다) 거짓이 됐는데 CLAUDE.md만 정정돼 있고 나머지는 옛 문장 그대로 — 즉 **"K-ICS 룰은 push를 못 막는다"는 정반대 사실**을 퍼뜨리고 있었다. 정정: `docs/launch_runbook.md:37-38,49` · `.claude/skills/launch-runbook/SKILL.md` 함정절 · `.claude/skills/incident-postmortem/SKILL.md`(frontmatter description + 본문 함정표 — frontmatter는 매 세션 스킬 목록으로 로드되는 자리라 가장 널리 퍼지는 사본이었다; 함정표를 1b/1c 배선 + 이상치 분리까지 4행으로 갱신하되 핵심 교훈 "배선했다 ≠ push를 막는다"는 살렸다. 이 스킬은 validation/postmortem 소유라 사실 정정만 하고 절차는 미수정). `docs/postmortems/PM-2026-06-16_two_month_glitch.md` §3 배선표는 이력이라 보존하고 후속 정정 각주만 추가(폐지가 아니라 주기 변경임 명시). **SKILL 2건은 `.gitignore:86`이 `.claude/`를 통째로 무시해 커밋에 안 실린다** — 이 머신에만 반영됐고 다른 클론에는 stale 문장이 남는다(스킬 = 머신-로컬 운영정본이라는 기존 계약대로. "고쳤다"를 "전파됐다"로 읽지 말 것). 고치지 않은 것: `changelog_validation.md`·`TODO_validation.md`(validation의 정확한 기록) · `changelog_parser_ifrs17.md:1832`·`TODO_parser_ifrs17.md:2047`(당시 실행 결과를 적은 과거형 사실) · 이 changelog L46(당시엔 참이었던 이력 — 이 항목으로 supersede).

부수로 이 프롬프트 헤더의 `"Status: SKELETON"` 표시도 걷어냈다 — CLAUDE.md "Stage prompt 작성 진행도"가 2026-08-06에 5개 프롬프트 전부 authoritative라고 재확인했는데 헤더만 옛 표시가 남아 있었다(같은 종류의 stale 표시가 완성된 프롬프트 3개를 몇 달간 skeleton으로 오인시킨 전례가 있다).

검증: 편집 5파일 UTF-8 BOM 없음(`od -An -tx1` 확인), `pytest tests/test_deploy_assets.py` **10 passed**(골든표 동기화·keep-list 기계검사 포함), `check_inbox_hygiene.py --mechanical-only` 위반 0. 티켓 `status: resolved` + `inbox/_resolved/` 이동 — publishing inbox 드레인 완료.

---

## 2026-08-15 (배포 2차) — IFRS17 재무상태표 패널 T자 재구성 main push

`4f1d344..6e5634f`, 격리 워크트리 cherry-push. `IFRS17.html`(Panel 7 타일형 → Panel 1 최상단 T자, 좌 자산/우상 부채/우하 자본을 실값 비율로 배치 + 2단계 `+` 드릴다운, 세부 미공시 회사는 버튼 disabled) + `IFRS17_BS.json`(`섹션`·`레벨` 컬럼 신규, 항목 1-7→1-31, 1,637→5,008행 — 파서가 예고보다 빨리 세부계정 랜딩, owner가 원 발주 60여개 항목을 13개로 축소). 원 발주 `inbox/_resolved/20260814T1250Z`(owner→designer) — designer가 섹션/레벨 그룹핑 계약(항목번호 무하드코딩)으로 짜둬서 파서 스키마 랜딩 후 HTML 무수정으로 호환 확인.

부수 발견: `scripts/build_ifrs17_bs.py`가 이 시점까지 한 번도 git에 커밋된 적이 없었다(`git log --all` 이력 0건) — 이번 배포 커밋에 같이 포함해 추적 시작(단 main의 site-assets-only keep-list에는 안 들어감, 작업 브랜치에만).

Pre-flight `validate_data_contract.py` RED=0 YELLOW=236, `pytest test_deploy_assets.py` 10 passed. owner에게 파일목록 제시 후 GO 받고 push. **배포 확인 함정**: legacy `pages/builds/latest` API가 새 push 후 한동안 직전 커밋을 계속 "built"로 보여줘 폴링이 안 됨 — 이 저장소는 실제로 `pages-build-deployment` GitHub Actions 워크플로우로 배포되므로 `gh run list`/`gh run view --json headSha,conclusion`으로 해당 커밋의 run을 직접 확인하는 게 맞다(다음부터 이쪽 우선). 라이브 검증: `IFRS17_BS.json`에서 `섹션`/`레벨` 필드 WebFetch로 확인, `IFRS17.html`은 브라우저에서 삼성화재해상보험 선택 후 T자 패널 DOM 텍스트 직접 조회로 확인(자산 112조4,436억 = 부채 77조981억 + 자본 35조3,455억, 항등식 성립) — 세부 드릴다운 행(현금및현금성자산·보험계약부채·이익잉여금 등)도 실값으로 렌더.

---

## 2026-08-15 (배포) — 배당현황 오픈 + PL_breakdown 유실 셀 복구 main push

`de0aef9..4f1d344`, 격리 워크트리 cherry-push. 3파일: `dividend.json`(신규, DART alotMatter 배당에 관한 사항, 24개사, 1,924행) · `공시보고서.html`("준비 중" placeholder → 배당현황 대시보드, KPI 4종 + 항목1-7 분기표 + 종류주별 드릴다운, designer 작업물) · `PL_breakdown.json`(작업트리에서 유실됐던 61셀/1,475행 복구, 7,799→8,111행).

**dividend keep-list 등록** (`inbox/publishing/20260814T2230Z`): `dividend.json`+`scripts/build_dividend.py` 커밋(기존 미추적), `claude-agent-publishing.md` §1 fetch표에 `공시보고서.html`→`dividend.json` 등록해 `test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` FAIL→PASS 복구. xlsx는 이미 `배당` 시트가 있어 재생성 불필요(파서 확인).

**PL_breakdown 유실 복구**: 원 사고는 `inbox/parser/20260814T1637Z`(validation 발견, MASTER_HOLE RED=13) — `validate_master_tables.py`를 `--no-build` 없이 돌리면 첫 동작으로 `build_root_masters.py`를 재실행하는데, 그 산출물이 결정론적으로 61셀(1,475행)을 떨어뜨림(2026-07-30 근접사고와 동일 계열, `project_git_purge`). validation이 owner 지시로 HEAD∪작업트리 union-merge(키=원보험사코드+공시분기+항목번호, null-vs-실값까지 셀 단위 판정)로 8,111행 복구, `validate_master_tables.py --no-build` 골든 일치 확인. publishing은 그 복구본을 `PL_breakdown.json`만 단독 스코프로 커밋(`79b1f7d`, 공유 워킹트리 다른 세션 변경분 섞이지 않게 `git commit -- <path>`로 범위 고정)한 뒤 위 3파일과 함께 배포. **근본원인(빌더가 순가산이 아님 / rebuild 기본값)은 미수정 — `inbox/parser/20260814T1637Z`에 열어둠**, parser 몫.

Pre-flight `validate_data_contract.py` RED=0 YELLOW=220, `pytest test_deploy_assets.py` 10 passed. owner에게 정확한 파일목록+이유+게이트결과 제시 후 GO 받고 push. 배포 후 GitHub Pages 빌드 완료(`gh api .../pages/builds/latest` status=built로 폴링) 확인 후 라이브 검증: `dividend.json`/`PL_breakdown.json` WebFetch로 스키마 확인, `공시보고서.html`은 브라우저에서 실제로 삼성화재해상보험을 선택해 배당 Panel이 렌더되는지 DOM에서 직접 확인(현금배당금총액 8,289억원·주당배당금 19,500원·배당성향 41.1%, 2025.4Q 기준) — 콘솔 에러 0. 워크트리 정리 완료.

---

## 2026-08-14 (배포) — IFRS17_BS.json + IFRS17.html Panel 7 main push

`255e445..de0aef9`. 격리 워크트리(`../insurequant-main-deploy`)로 `IFRS17_BS.json`(신규 마스터, 1,637행) + `IFRS17.html`(Panel 7 "재무상태표·자본의 질") 2개 파일만 cherry-push — `common.css`는 main과 diff 0이라 미포함. Pre-flight `validate_data_contract.py` RED=0 YELLOW=220 확인, 정확한 파일목록+이유+게이트결과 제시 후 owner GO 받고 `git push origin main` 실행. 배포 후 검증: `IFRS17_BS.json`을 WebFetch로 스키마 확인(원보험사코드/원수사명/티커/생손보여부/항목번호/항목명/공시분기/값), `IFRS17.html`은 브라우저에서 실제로 삼성생명(KR0069)을 선택해 Panel 7이 렌더되는지 DOM에서 직접 확인(자산총계 309조 9,483억원 표시, 2025.4Q) — 콘솔 에러 0. 로컬 static server(8896 config) 사전 확인은 Browser pane 컴포지팅 문제로 무산됐으나 curl 200 확인 후 진행, 라이브 브라우저 검증으로 최종 확인 완료. 워크트리 정리 완료.

## 2026-08-14 — equity_composition → IFRS17_BS keep-list swap (HIGH, `20260814T0232Z`) + inbox backlog triage

**1. keep-list + xlsx source swap.** Owner archived `equity_composition.json`(항목1-49) in favor of the single `IFRS17_BS.json`(항목1-7) master — `docs/agents/claude-agent-publishing.md` §1 fetch table, §9 keep-list snapshot, and §0 live-gate line updated to match; `scripts/build_master_xlsx.py:18` MASTERS entry repointed `equity_composition.json`→`IFRS17_BS.json` (sheet name `17BS` unchanged, columns 9→8 since the schema is stock-only, no `값_당분기`). Regenerated via the official `xlsx` skill after confirming with owner that the pre-existing `17BS_PIVOT` manual sheet (owner's 해약환급금준비금 hand-review) would be lost on rewrite — its correction logic was already ported into `build_ifrs17_bs.py`, so proceeded with a `.bak_20260814_prepivotloss` backup. Result: 8 cols × 1,637 rows, xlsx mtime newer than `IFRS17_BS.json`. `pytest tests/test_deploy_assets.py` 10 passed.
**Not pushed yet.** `IFRS17_BS.json` is not yet on `main`. At the time of the original report, `validate_data_contract.py` was RED=42, all `[IFRS17_BS] BS_CENSUS_MISSING_ITEM` (6 companies with partial Tier-2 face-table extraction). **Correction (re-checked same day):** a concurrent validation-lane session closed this out before this note was finalized — owner confirmed via live DART API probe (status 013/014) that those 6 companies are non-listed and file only audit reports with no XBRL attachment at all, so the extraction gap is unrecoverable; owner directed a census exemption (`IFRS17_BS_NO_SOURCE`, `BS_IDENTITY` still checked) added to `validate_data_contract.py` (`inbox/_resolved/20260814T0620Z`). **Gate is now RED=0** (YELLOW 220, one new `BS_CENSUS_NO_SOURCE_COMPANY` for visibility). §9 keep-list comment and §0 live-gate line corrected to match. Technical gate is clear; actual `main` push still needs an explicit owner GO (publishing recommends only, never executes `git push`).

**2. Inbox hygiene.** Several publishing-inbox tickets going back to 2026-06-16 had already been substantively completed (their `## 답변` sections said so, some literally writing "status: answered" in the body) but the YAML frontmatter `status` field was still `open`, or the ticket had been overtaken by later architecture changes. Reconciled against current repo state and closed out:
- Archived to `_resolved/` as genuinely done/superseded: `20260803T0743Z`(xlsx regen, prior answer verified) · `20260814T0135Z`(equity keep-list gap, confirmed superseded by this session's 0232Z) · `20260620T0859Z_skeptic_hardening_grounding`(all 4 hardening rules verified present in `claude-agent-publishing.md` §3) · `20260616T0700Z`(K-ICS inline `FORWARD_DATA` reembed — moot, superseded by the later no-inline-data-in-HTML refactor; grep confirms 0 occurrences of `FORWARD_DATA` in `K-ICS.html` now) · `20260813T0422Z`(equity_composition deploy-prep — file itself archived, superseded).
- Frontmatter synced `open`→`answered` (content already resolved, left in place per protocol since these are informational owner-instruction tickets, not archived unilaterally): `20260619T0412Z`(prepush_check chain + LLM-skeptic wiring, confirmed live in §0) · `20260620T0834Z`(코리안리/삼성화재/신한이지 5-cell owner-confirmed registry, confirmed `data/_gold/user_pl_confirmed_cells.json` exists).
- **Left genuinely open, not started**: `20260620T0859Z__gold_overlay_durable_ownerfix` — owner's request to unify all masters (not just K-ICS) onto a durable gold-overlay-as-last-build-step pattern. `## 답변` is blank; this is real unstarted architecture work, out of scope for this session without owner check-in.

---

## 2026-08-03 (2차) — inbox 처리: master xlsx 재생성 + forward baseline 키 오기 수정 (UH-7)

**1. `insurequant_master_tables.xlsx` 재생성** (`inbox/publishing/20260803T0743Z`, owner escalate → resolved). 위 배포로 마스터 JSON 4종이 갱신됐는데 xlsx가 7/30 stale이었음. 재생성 전 `data_only=False`로 전체 시트 스캔해 수식 셀 0건(=owner 수기 리뷰 formula 없음) 확인 → `.bak` 백업 → 공식 `xlsx` skill 워크플로우로 `scripts/build_master_xlsx.py` 실행(`build_csm_waterfall_master.py`는 미실행). 결과: CSM워터폴 1,962행·신계약CSM배수 327행·손익분해PL 7,799행(행수 유지, 값만 갱신). KR0004 3개년(2023/2024/2025.4Q) + KR0051 투자이익/보험금융손익 분리값을 xlsx에서 직접 read-back해 확인. xlsx는 git 미추적/keep-list 밖 — push 대상 아님.

**2. `kics_forward_capital.json` `baseline_2025_4Q` 키 오기** (`inbox/publishing/20260803T0210Z`, validation UH-7 → answered). `scripts/forward_capital_simulation.py:482`의 키가 `BASELINE_QUARTER`("2026.1Q")와 무관하게 하드코딩된 `"baseline_2025_4Q"`였음(2026-06-16 rebaseline 때 안 따라간 잔존 이름) — 데이터는 맞고 키 이름만 거짓이라 게이트는 통과하지만 다음 분기 as-of 판단 때 같은 오독을 재생산할 위험. 조치: quarter-agnostic `"baseline"` 필드 + 형제 `"baseline_quarter"`로 교체(하드코딩 연도 재발 방지), 이번 릴리스만 `"baseline_2025_4Q"` alias를 같은 payload로 병기해 하위호환 유지. 재생성 후 `validate_data_contract.py` RED=0 YELLOW=219(불변) 확인, `pytest tests/test_deploy_assets.py` 9 passed. `K-ICS.html:1090`이 이 키를 읽는 유일한 소비처(publishing은 HTML을 못 건드림) → designer inbox(`20260803T0900Z`)로 스왑 요청, alias는 designer 확인 후 다음 실행에서 제거.

## 2026-08-03 — main 배포: 마스터 JSON 4종 동기화 (`a4e8a7c..255e445`)

**배경**: 2026-08-03 capsec 체인(`184286c`·`64043fa`·`cb084e7`·`08321db`·`eea9da3`)이 작업 브랜치에만 커밋돼 있었고 라이브(main)에는 미반영. owner 지시로 배포.

**올린 것 (4개, 전부 루트 마스터 JSON — HTML/CSS는 손대지 않음)**:

| 파일 | 델타 |
|---|---|
| `CSM_waterfall.json` | KR0075 비엔피파리바카디프 CSM 단위 재정정 + KR0004 예별손해 3개년(2023/2024/2025.4Q) 18셀 신규 온보딩 (1944→1962행) |
| `NB_CSM_multiple.json` | 위 반영 재산출 (321→327행) |
| `PL_breakdown.json` | **KR0051 신한이지손해보험** 2025.4Q 투자이익 -3890.709458→-1603.902737 / 보험금융손익 0.0→-2286.806721 (부모 투자손익 -3890.709458 불변, 7799행 유지) |
| `kics_forward_capital.json` | 자본증권 소스 FSC bonds → DART 개별사채 리베이스 (38사 유지, 값 전면 갱신) |

**올리지 않은 것**: `index.html`/`K-ICS.html`/`IFRS17.html`/`공시보고서.html`/`common.css` — main과 이미 byte-identical(HTML은 designer 소관이기도 함). provenance sidecar 4종은 HTML이 참조하지 않아 keep-list 밖 → main slim 유지 위해 제외.

**절차(runbook 준수)**: ① pre-flight `validate_data_contract.py` **SUMMARY RED=0** YELLOW=219 provisional=False ② K-ICS 게이트 별도 실행 — RED=12는 전부 `TODO.md` 등재 exception(KR0087 2023.2Q ×7 · KR0097 2024.2Q ×4 · KR0079 8_life ×1, image-only)이고 `kics_disclosure.json`은 main과 diff 0이라 이번 변경과 무관 ③ keep-list를 4개 HTML의 `fetch(`/`src=`/`href=`에서 재파생 ④ **행 손실 가드** — main 버전과 신버전을 (원보험사코드,항목번호,공시분기) 키로 대조해 dropped cells 0 확인 ⑤ 격리 워크트리 `git worktree add ../insurequant-main-deploy main`, staged가 정확히 4개인지 확인 ⑥ owner 사전 GO로 push ⑦ 워크트리 제거, 작업 브랜치 복귀 확인.

**배포 후 검증(라이브 브라우저 fetch, cache-bust)**: CSM 1962행·KR0004 3분기 present·KR0075 2025.4Q 기말 299.584 / PL 7799행·KR0051 3항목 분리 확인 / NB 327행 / forward 38사. 회사망에서 `curl`은 TLS 차단으로 빈 응답 — 브라우저 경유로 검증했다.

⚠️ **정정**: 배포 커밋 `255e445`의 메시지가 PL 델타 회사를 KR0075로 잘못 적었다(실제 KR0051). main은 공개 배포 브랜치라 force-push로 고치지 않고 여기에만 정정 기록.

**후속**: `insurequant_master_tables.xlsx`가 stale(7/30 17:16 < 마스터 4종 8/3) → `inbox/publishing/20260803T0743Z__owner__MULTI__master_xlsx_regen_after_json_deploy.md`로 재생성 발주(공식 `xlsx` skill 경유, openpyxl 재저장 금지). xlsx는 keep-list 밖이라 배포 대상 아님.

---

## 2026-07-22 — main 배포: K-ICS 패널 데이터 인라인 → 외부 JSON (`a5d0ffa..8372b53`)

**올린 것 (4개)**: `K-ICS.html`(208,957→62,081자) + 신규 keep-list 3개 `kics_tier1_utilization.json`(39행)·`kics_tier2_utilization.json`(39행)·`kics_forward_capital.json`(38행). 배경·근거는 cross-stage changelog 2026-07-21 리팩토링 2차 B 항목.

**절차(runbook 준수)**: ① pre-flight `validate_data_contract.py` **SUMMARY RED=0** ② keep-list를 HTML의 `fetch(`/`src=`/`href=`에서 재파생(기억 아님) ③ **main과 내 브랜치의 K-ICS.html 차이가 내 변경뿐임을 확인** — designer a5d0ffa a11y 작업을 되돌리지 않음을 push 전에 검증 ④ 격리 워크트리(`git worktree add --detach origin/main`), 같은 폴더 checkout 바꿔치기 안 함 ⑤ 워크트리 staged가 정확히 4개 파일인지 확인 ⑥ **배포될 그 워크트리를 직접 서빙해서** 헤드리스 검증(ALL PASS) ⑦ owner GO 후 push.

**배포 후 검증**: 3개 JSON 200(26,265 / 25,080 / 131,747 bytes), 라이브 `K-ICS.html` 69,045 bytes·인라인 블롭 0, 라이브 브라우저에서 패널 39/39/38 적재·자본도넛 실수치·forward 렌더·**콘솔 에러 0**.

⚠️ **이후 K-ICS.html을 배포할 때 이 3개 JSON은 항상 동반**해야 한다. HTML만 올리면 자본도넛·forward가 **에러 없이 빈칸**이 된다. `tests/test_deploy_assets.py`가 4개 페이지의 로컬 fetch/link 참조 존재를 강제하므로, 배포 전 `pytest tests/test_deploy_assets.py`를 keep-list 파생의 기계적 확인으로 쓸 것.

---

## 2026-07-22 -- designer A11y color fixes + treemap revert, deployed to main via launch runbook

Feature branch (`fix/csm-product-segmented-columns`) had two uncommitted-then-committed designer
changes sitting ahead of `main`: the A11y owner-review-queue color/contrast fixes
(`docs/changelog_designer.md` 2026-07-21d, commit `2e4f114`) and a same-day-plus-one revert of the
treemap red→blue swap after owner flagged it broke an intentional finviz.com-style market-map
identity (commit `6fc34c1`). Ran the newly-adopted `docs/launch_runbook.md` procedure end to end for
the first time on designer-only output (no master JSON changes involved).

- **Pre-flight**: `python scripts/validate_data_contract.py` → `SUMMARY RED=0` (YELLOW=200, existing
  triage queue, non-blocking).
- **Shared-tree check**: `git branch --show-current` + `git status` before touching anything — found
  an unrelated concurrent session's staged changes (`schemas/kics_data.schema.json` deletion,
  `src/solvency/legacy/*` removal, `scripts/run_harness.py`/`src/solvency/config.py` edits). Did
  **not** stage or commit any of it — `git reset` (index-only, no working-tree impact) to unstage,
  then re-staged only the designer files. That session went on to commit its own work cleanly
  (`0543414` etc.) with no interference either direction.
- **Isolated worktree cherry-push**: `git worktree add ../insurequant-main-deploy main` (after
  fast-forwarding local `main` to `origin/main`, which already had an earlier a11y sync `8e8c01d` —
  the keyboard-access/aria-label batch, not the color batch) → `git checkout
  fix/csm-product-segmented-columns -- index.html K-ICS.html IFRS17.html common.css` → verified
  `git status`/`git diff --cached` showed exactly those 4 files and nothing else → committed
  (`a5d0ffa`).
- **Owner GO**: presented the 4-file list + 1-line reason each + gate result in chat; owner confirmed
  ("push 고고") before `git push origin main`.
- **Live verification**: polled `common.css` for the active-tab underline (propagated ~15-30s after
  push, GitHub Pages), then confirmed all 4 files' specific changed values live via curl —
  `K-ICS.html` placeholder gray, `IFRS17.html` `NB_LINE_COLORS`, `index.html` bubble-legend green,
  and confirmed `index.html`'s treemap `hue` is `0` (red) in both branches, not `215` — the revert
  is correctly live, not just on the feature branch.
- **Cleanup**: `git worktree remove ../insurequant-main-deploy`, confirmed clean return to the
  feature branch (`git status` clean of tracked changes).
- **Not deployed** (intentionally out of scope): the concurrent session's `src/solvency/legacy`
  removal / `schemas/` change — backend-only, not a site asset, not touched by this deploy.

## 2026-07-21 -- provenance sidecar 3종 발행 + 게이트 로더 버그 수정 + launch runbook 신설

Inbox 드레인 (`inbox/publishing/`): validation의 UH-3 후속(`20260721T0530Z`) + owner의 런북 발주
(`20260721T0233Z`), 둘 다 `status: answered`/`resolved`. 겸사겸사 오래 미커밋 상태였던 IBK(KR1011)
스레드(`20260704T0600Z`, 실제 배포는 `7bf0d60`으로 이미 완료돼 있었음)도 xlsx 재생성 확인 후 종결.

### Provenance sidecar 발행 (forward_capital · tier1/tier2_utilization)

`templates/{forward_capital_latest,tier1_utilization_latest,tier2_utilization_latest}_provenance.json`
3종 신설 — `--print-provenance-contract` 스키마 그대로: `source_id=FSC_BONDS`, `effective_filtered=true`,
`as_of_date=2026-03-31`(=2026.1Q). source_file은 각 마스터가 **실제로** 읽는 파일로 정확히 매핑:
- forward_capital → `data/bonds/normalized/20260616T060817Z/bonds_by_insurer.json` (forward manifest의
  `bonds_source`와 동일 스냅샷).
- tier1/tier2_utilization → `data/bonds/capital_securities_fy2025.json` (DART per-bond 발행현황;
  `wire_capital_securities_to_utilization.py`가 이 파일의 `call_date`/`legal_maturity` 기준
  `is_grandfathered`/`amort` 효력필터를 실제로 적용함을 코드 리딩으로 확인한 뒤 `effective_filtered=true`
  기재 — 상위 `compute_tier{1,2}_utilization.py`는 이 필터를 안 하는 구버전이라 혼동 주의, 2026.1Q
  산출물은 `wire_*` 스크립트가 in-place 갱신한 버전).

**버그 발견 + 수정 (발행만으론 안 잡혔을 뻔)**: `Env.MASTER_FILES`(`validate_data_contract.py`)에
`forward_capital`이 `forward_capital_latest`라는 다른 키로 등록돼 있어 `check_as_of`의
`sidecars.get("forward_capital")`과 영원히 매칭이 안 됐고, `tier1_utilization`/`tier2_utilization`은
그 dict에 항목 자체가 없어 사이드카 로드 경로가 없었음 — 3종 다 발행해도 게이트가 못 찾는 상태.
`MASTER_FILES` 3개 키를 lookup 이름과 맞춰 수정/추가.

**검증**: `--selftest` 14/14 유지(회귀 0). 게이트 `MISSING_PROVENANCE_SIDECAR` YELLOW 4→**1**
(잔여 sensitivity_heatmap = parser ifrs17 별도 소관, 원 티켓 스코프 밖). RED=0 불변.

### Launch runbook 신설 (owner 발주 `20260721T0233Z`)

`docs/launch_runbook.md`(정본 절차서) + `.claude/skills/launch-runbook/SKILL.md`(로컬 skill) 신설.
Pre-flight 게이트 → keep-list 재파생 → 격리 워크트리 cherry-push → owner 승인 지점 → 배포 후 검증 →
**§6 rollback(신규 — 이전 TBD)**: HTML/JSON은 격리 워크트리에서 `git revert`(force-push 금지), 마스터
xlsx 손상은 `.bak` 복원 → Excel 재오픈 → `build_master_xlsx.py` 최후수단 순. `claude-agent-publishing.md`
§8 TBD 3건(branch policy·site-deploy hook·rollback contract) 체크 완료 + 링크. **로컬 skill 채택**
(외부 미도입) — 이 저장소에 이미 로컬 skill 패턴(a11y-audit·incident-postmortem) 존재 + 절차가 이
저장소의 공유 워킹트리·slim keep-list·K-ICS 별도게이트 함정에 강결합돼 범용 외부 스킬로는 못 담음.
**이번 발주로 실제 배포는 실행 안 함**(지시대로 문서화만).

### 2026.1Q 적용후 요구자본 fill — 배포 확인 결과 이미 라이브 (중복 push 없음)

`inbox/publishing/20260716T0330Z`(validation) — 2026.1Q 5개사(한화생명·교보·하나·롯데손해·농협)
적용후 요구자본 fill을 main에 반영할지 owner에게 질의 → **"지금 배포 진행"** 승인. 착수 전
`git fetch origin main` + `kics_disclosure.json` 정규화 전체 대조(18,878 레코드) → **diff 0** —
다른 세션이 이 사이(`25d8e98` 2026-07-16 · `1c9ebdc`/`8e8c01d` 2026-07-21) 이미 라이브에 올려둠.
**push 실행 안 함**(중복 배포 스킵), 스레드 resolved.

### 미착수 (다음 세션 트리아지 필요)

`inbox/publishing/`에 `status: open`으로 남아 있는 2026-06-16~20 backlog 5건 — 이번 세션에서 손대지
않음(스코프 밖, 오래된 항목이라 이미 다른 경로로 해소됐을 가능성도 있어 트리아지 우선): reembed-done
트리거·prepush 체인 문서화·owner-confirmed registry 분쟁 3건·gold-overlay 통일·skeptic 하드닝.

---

## 2026-06-17 -- push BLOCKED (data-contract RED=52) + 게이트 #0 와이어링

### 게이트 #0 data-contract 신설 (owner 정책 2026-06-16 12:44)

owner 정책 확정: **"RED 1건이라도 있으면 push 안 한다."** — documented-exception 우회 불가, fixable RED은 고쳐서 0으로.

- `claude-agent-publishing.md` §3 #0 gate 명문화: `validate_data_contract.py` exit 2 = BLOCKED, exception 없음.
- 현재 라이브 RED=52 (CHECK2 sensitivity_heatmap FY2024 stale = V12 parser refill 대기 + CHECK1 census 30).
- owner inbox `1242Z` + validation inbox `1254Z` 모두 resolved.

### push 대기 중인 변경 (main에 미반영)

designer 트리거(`1300Z`) 수신. 다음 배포 후보 변경이 feature branch에 파킹됨:
- K-ICS.html: FORWARD_DATA 2026.1Q 재임베드 + Baseline 라벨 (designer)
- IFRS17.html: common.css 채택 + WF_Q_WINDOW=5 + PL 워터폴 zero-crossing fix (designer)
- CSM_waterfall.json: continuity RED 8→0 교정
- PL_breakdown.json: 기타사업비용 item16 0처리 (KB손해 13Q, 흥국화재 6Q, KDB 1Q)

**push 재개 조건**: `validate_data_contract.py` exit 0 (sensitivity_heatmap V12 parser refill 완료 후).

### 자본성증권 소스 조사 완료 (downloader 1300Z + parser 1305Z)

- KDB생명(KR0072) 신종 DART 2,410억 ≈ BS 2,403억 ✓ 확인.
- 현대해상(KR0009) 후순위 FSC 26,000억이 정확, BS 3,766억 = 파서 오파싱 → parser(kics) 재파싱 발주(`1530Z`).
- 농협생명(KR0104) 신종 DART/FSC 5,000억, BS=0 = 파서 누락 → parser(kics) 재파싱 발주(`1530Z`).
- 흥국화재(KR0005) per-bond: 신종 4,120억(≈BS), 후순위 3,200억(Face=gross, BS=경과조치 인정분).
- 사모채 7사(삼성생명·악사·하나손해·AIA·삼성화재·KDB후순위·교보): 공개 소스 없음, forward-sim BS 총계 단순가정 유지.
- forward_capital_simulation 재실행: parser KR0009/KR0104 재파싱 + data-contract gate clear 후 예정.

---

## 2026-06-16 -- 배포 `99fb923..dbbb096`: common.css 디자인시스템 + 2026.1Q site refresh

owner 승인 push("오늘까지 작업본 + designer common.css 같이"). origin/main 배포(7파일, worktree on main → fast-forward, rebase 불요·origin==local 99fb923).

- **common.css** (신규 배포에셋): 디자인시스템 단일소스(토큰+chrome+A11y), index/K-ICS/IFRS17.html 3개가 `<link>` 참조 → **HTML과 반드시 동반 배포**(누락 시 스타일 붕괴). designer frontend-design skill 산출물.
- index.html(92)/K-ICS.html(31)/IFRS17.html(156): common.css 추출 + 렌더수정. kics_disclosure.json(4700, 예별 13Q 백필). kics_rate_sensitivity.json(294)·sensitivity_heatmap.json(144) refresh.
- **게이트**: K-ICS `validate_kics_disclosure.py` RED=24 **전부 documented**(TODO.md 36-96: 36_irr 12·19_market 7·예별 KR0004 rule1·AIA·micro 등) + census MISSING=6 documented(image-PDF OCR). 충족.
- **continuity break**(전기말 CSM≠당기 기시): owner가 **내일(6/17) 수정 deferred**. 이 배포의 CSM waterfall 데이터(CSM_waterfall.json + data/dart/viz/csm_waterfall*.json)는 **live와 동일=델타 밖** → 배포가 악화 안 시킴. 이미 parser 작업중(validation `csm_2026q1_opening_misparse` + downloader `csm_continuity_raw_ready`).
- **미반영(후속)**: K-ICS.html `window.FORWARD_DATA`는 아직 구 베이스라인 — 2026.1Q forward 재임베드는 designer 대기건(`inbox/designer/20260616T0605Z`, JSON 준비완료). 다음 push에 반영.
- ls-remote 확인 origin/main=dbbb096. worktree 제거, feature 무손상.

## 2026-06-16 -- Forward-capital 2026.1Q 재베이스라인 + (a) T2-디커플 신뢰도 산식

parser-kics 발주(`inbox/publishing/20260616T0600Z`, owner QA 후속). owner가 신뢰도 산식 **(a) T2 디커플** 선택. `forward_capital_simulation.py` 두 파트:

- **재베이스라인**: `BASELINE_QUARTER` 2025.4Q→2026.1Q, `TIER{1,2}_JSON`→_20261Q(parser 산출분), `BASELINE_YEAR` 2025→2026(as-of 2026-03-31 — 경과조치 phase-out 램프 앵커링, 2026.1Q post값의 ~1년 run-off 이중계상 방지). Face=`_latest_bonds_dir()` 자동 픽 clean 스냅샷 `20260616T060817Z`(카카오페이 Face=0·KB라이프 1,200억 반영).
- **(a) T2 디커플**: `_overall_bucket(t1_bucket, t1_real_error, t2_hard_error)` 재작성 — overall=T1 reconciliation 기준, T2 Face(FSC outstanding)-vs-BS(grandfathered issued) 개념차는 advisory(overall 안 깎음). 진짜 오류만 hard-low: T1/T2 한쪽결측 + t2_util>100%. 불변식 검증 통과(low 21건 전부 진짜 사유, T2 개념차 단독 low=0; 분해 fsc_missing_t2 10·T1gap 4·kics_missing_t1 4·util>100 3). **T2 개념차 false-low 8개사 구제**. dist high=15/med=2/low=21(구 22/37).
- **경계**: 스크립트에 `--no-html` 플래그 신설 → publishing은 JSON만(`templates/forward_capital_latest.json` + `output/.../20260616T063704Z/forward_simulation_v3.json`), K-ICS.html `window.FORWARD_DATA` 재임베드는 **designer**(handoff `inbox/designer/20260616T0605Z` blocked→open 전환). 스키마 불변(level/t1_gap_pct/t2_gap_pct). forward JSON은 slim keep-list 비대상 → **push 없음**(사이트엔 designer inline 임베드로만 반영). parser 스레드 resolved→`_resolved/`.

## 2026-06-16 -- publishing 프롬프트 내부모순 정리 (MD 감사 후속)

owner 발주(`inbox/publishing/20260616T0514Z`). `docs/agents/claude-agent-publishing.md` 3건 surgical 수정:
1. **헤더↔§5 모순 해소**: 옛 문장 "Subagent prints these... does **not** execute them" 삭제 → 헤더(L5)·§1 hard-rule(L36)·§9(L201)와 일치하는 "agent runs local git itself; only outward `git push` is gated"로 교체.
2. **§3 "gathering scripts" → "assembly/build scripts"** (죽은 stage명 정정, 문서 내 잔존 0 확인).
3. **(선택) §1 경로 주석**: 표 아래 §9 "Pending path migration" cross-ref 한 줄 추가(`data/dart/viz/*` post-migration canonical vs 라이브 `main` `data/ifrs17/viz/*`). 경로 자체 미변경.

검증: UTF-8 no BOM·깨진 한글 없음·grep 정합. 배포 없음(docs/agents = IP, slim keep-list 비대상). inbox answered.

## 2026-06-16 -- V7(NB_CSM_DART_VS_IR) gate enforcement 조사: publishing 차단 미배선 확인

owner backlog 🟠-6(`inbox/publishing/20260612T0900Z`) 위임. **결론: NB_CSM_DART_VS_IR RED는 publishing 어셈블을 차단하지 않음 — 전용 차단 로직 미배선. 단 publishing 코드 갭 아니라 validation 측 배선 갭.**

3층 전수 확인:
1. **어셈블 `build_root_masters.py` = 검증게이트 전무** — diag 소스→루트 마스터 무조건 transform(owner override + unit-cap만). validation 결과 미참조 → RED여도 빌드. (설계상 정상: V7 severity="RED→DART parser loopback", 교정은 parser 소스에서.)
2. **V7 미집계** — 도구 `check_nb_csm_widespread.py`·`check_nb_csm_history.py` **소스 둘 다 부재(.pyc만 잔존)**, 파이프라인 미호출, `validate_master_tables.py` 미포함, `validation_report*.json` 0건.
3. **publishing 게이트는 generic·절차적** — §3.1/Hard-rule/exit-table = "validation subagent report `summary.red==0` per domain → else BLOCKED". V7가 그 리포트에 surface되면 **이미 차단됨**. 결손은 V7 자동집계뿐.

판정·조치: 전용 V7 publishing 게이트 **신설 비권장**(parser-loopback 설계 + V1으로 retire 예정). enforcement 지점은 generic 게이트로 충분 — V7를 validation 리포트에 올릴지/도구 소스 복원/retire는 **validation 소관**이라 inbox 발주(`inbox/validation/20260616T0100Z__publishing__MULTI__v7_gate_enforcement_findings`). publishing은 무코드(pre-push 체크리스트 1줄: IFRS17 RED 시 V7 7사 cohort 포함 확인). 현재 V7는 parser 교정 중(롯데 FY2025 P1 / off-by-one history P2).



owner 발주(`inbox/publishing/20260616T0043Z`): Anthropic 공식 `xlsx` skill을 publishing master xlsx 작업의 **상시 디폴트 도구로 즉시 채택**(별도 평가 없이). 발주 시점에 마침 재생성 룰 발동 → #1 대상으로 첫 적용.

- **트리거**: 오늘 배포한 master JSON 2건(`kics_disclosure.json`·`kics_rate_sensitivity.json`, 둘 다 6/16)이 기존 xlsx(6/15)보다 최신 → `feedback_rebuild_master_xlsx` stale 룰 발동.
- **조치**: `xlsx` skill 워크플로우 하에 `scripts/build_master_xlsx.py` 실행. skill 원칙 "Existing template conventions ALWAYS override" → 기존 컨벤션(맑은 고딕·헤더 305496·`#,##0.##;(#,##0.##);-`) 유지, 표준화 강제 안 함.
- **결과**(7시트): 요약 + K-ICS공시 17,197 · 금리민감도 516 · CSM워터폴 **1,926** · CSM상각 290 · 신계약CSM배수 321 · 손익분해PL 7,727. read-back 한글 무결, 정적값(수식 0)이라 recalc N/A·formula 에러 불가.
- **금지선**: `build_csm_waterfall_master.py` 미실행(CSM워터폴 1,926행 유지로 입증 — raw purge 브랜치 붕괴 회피, 메모리 `project_git_purge`). 멀티라인 인라인 `python -c` 미사용.
- **배포 없음**: xlsx는 untracked 빌드물(리뷰어용), slim keep-list 비대상 → push 불요. backlog `🔴-3` 종결. inbox `xlsx_skill_adoption` answered.
- 적용대상 #2(리뷰루프 I열 재계산)·#3(gold xlsx 게이트)는 발생 시 skill 적용 예약. 분담 불변(diag→parser inbox, 데이터 도메인 오류→parser 바운스).

## 2026-06-15 -- Forward sim: 신종자본증권 tier-priority deduction (T2→T1)

owner 발주(`inbox/publishing/20260615T0435Z`). `forward_capital_simulation.py` 채권 차감부를 tier 우선(보완자본 먼저→기본자본) 으로 교체. 별도 순서분기 없이 매 시점 재계산:
- `HYBRID_LIMIT_RATIO=0.15` (신종/조건부=SCR×15%, 규정 다.(1)). `limit_y=scr_y×0.15`, `H_y=total_hybrid−누계신종call`.
- `basic_y = basic_baseline + (min(H_y,L_y) − min(H_0,L_0))` → 신종 call이 H를 줄여도 H≥L인 동안 기본자본 불변(초과분=T2에서만 차감), H<L부터 기본자본 감소. 후순위채는 총자본만 차감(기본자본 불변, 유지).
- 출력 진단필드 추가: hybrid_remaining/tier1/tier2_overflow/limit_eok.

검증(KR1000): 2027 신종 3,300억 call → 기본자본 35,582 불변(T2만), 2028 초과분 소진 후 기본자본 34,550으로 하락 = **T2-first 확인**. 빌드 37사 ok → `forward_simulation_v3.json`(20260615T050803Z) + `templates/forward_capital_latest.json` + K-ICS.html `window.FORWARD_DATA` 동기화. **K-ICS.html 배포는 owner GO 대기.**

## 2026-06-14 -- Slim-publish deploy: IFRS17/K-ICS designer fixes + sensitivity heatmap (option B)

origin/main 배포 (`25a329d..d45ebd5`, 3파일). **kics_disclosure.json 보류**(K-ICS 게이트 RED>0: 36_irr×11 등 미문서화 — validation/parser 트리아지 대기). master JSON + HTML만.

- IFRS17.html (현대해상 #FFB81C, ΔCSM 억원 헤더, 모바일 패딩), K-ICS.html (드롭다운 누락사 fillMissingCompanies), data/dart/viz/sensitivity_heatmap.json (흥국/푸본현대 정정+단위정규화).
- 절차: main이 이미 slim(17 site assets, data/dart/viz 경로 이전 완료) 확인 → §9 대량삭제 dance 불필요. **git worktree**로 main 체크아웃(피처 워킹트리 동시쓰기 충돌 회피, §8b 권장). origin/main이 앞서있어(미purge 이력) **force-push 대신 rebase**로 fast-forward. local main(purge본)은 force-push 안 함.
- tier1 100% 캡 수정은 K-ICS.html이 `window.TIER1_DATA` inline+JS캡이라 사이트 미영향(내부 정합성용), keep-list 아님 → 미배포.
- 라이브 검증(raw curl): K-ICS.html fillMissingCompanies✓, IFRS17.html FFB81C+ΔCSM(억원)✓, sensitivity_heatmap.json 200/48KB✓.

## 2026-06-14 -- Tier-1 hybrid utilization 100% cap (glitch G2 resolution)

9개사 2025.4Q tier1(기본자본 신종자본증권) 소진율 >100% (코리안리 242.5%, NH농협손해 187%, 교보 171% 등). 진단: 규정(K-ICS 해설서 [별표22] Ⅲ.2.다.(1)) 상 신종 한도(SCR×10%, 조건부자본증권 15%) 초과분은 보완자본 자동 재분류 → 소진율 정의상 ≤100%. >100%는 Ⅴ.1 재분류액(excess) 파싱누락 artifact. parser-kics 회신: standalone Ⅴ.1 행 9사 전부 부재(번들 "…초과한 금액 **등**" 행으로만 공시). 번들값 검산상 신종 한도초과분과 40배 차이(번들="등" 기타항목; 신종초과분은 공시 보완자본에 직접 반영, 라.(1)).

owner 결정: **소진율 100% 캡(옵션 2/3)** — tier2 cascade는 공시 보완자본 이중계상이라 미채택.

> **정정 각주 (2026-08-25 추가, 이력은 위에 그대로 보존).** 이 "소진율 100% 캡" 결정은
> **같은 날 늦게 owner 가 번복했다** — `docs/changelog_designer.md` 2026-06-14 (후속3)
> "기본자본 소진율 '100%+' 표기 (owner 결정 복원)". 논거: 분자(발행액)=KOFIA, 분모(인정한도)=공시로
> **소스가 독립이라 사전 100% cap 이 애초 불가능**하고, >100% 면 그냥 `100%+` 로 표기하는 것이
> 정당하다. `docs/agents/claude-agent-designer.md:177` 에 LOCKED 로 박혀 있다. 자르는 것은
> **도넛 원호뿐**이다. 그런데 데이터 쪽 캡은 2026-08-25 까지 코드에 남아 있었고, 2026-07-22
> `a629e34`(인라인 JSON → fetch 분리) 이후 그 캡이 화면에 도달해 6사가 평평한 `100%` 로 그려졌다.
> 캡 제거 경위는 이 파일 맨 위 2026-08-25 항목 참조. **이 문단을 근거로 캡을 다시 넣지 말 것.**

- `compute_tier1_utilization.py`: `utilization_pct=min(recognized/limit,1.0)*100` 캡(util_strict 동일) + 신설 필드 `tier1_hybrid_overflow_eok=max(recognized−한도,0)`(보완자본 재분류분 명시, 예: 코리안리 4,749억). definition에 `utilization_cap` 주석.
- 9사 util15 → 전부 100.0, util>100=0건. `templates/tier1_utilization_latest.json`(K-ICS.html 리더) 갱신.
- **무변경**: compute_tier2/forward_capital_simulation(cascade 미채택), K-ICS.html(line 816 Math.min 캡 그대로=안전망, designer 도메인). designer XXX%+ 도넛 구현 보류 확정.
- inbox 종결: parser `tier1_hybrid_excess_unparsed`(blind_spot, resolved), owner `tier1_overflow_cascade`(resolved) → `_resolved/`. designer 스레드 재통지(예외 없음).

## 2026-05-31 -- Publishing stage created (merge of gathering + pushing)

User decision: parser+validation are the "real" pipeline; gathering+pushing are mechanical follow-up to those. Merged into one **publishing** stage with two responsibilities: (1) assemble validated per-source JSON into HTML-ready masters, (2) report changes + recommend commit/push commands (human still runs `git push`).

- Combined prompt: `docs/agents/claude-agent-publishing.md` (replaces `claude-agent-gathering.md` + `claude-agent-pushing.md`, both deleted).
- New TODO/changelog created from root TODO items: F4 v2 / F13 / INDEX-IFRS17-BUBBLE / INDEX-BUBBLE-V2 / MISC-IR-NB-DENOM (publishing side) / MISC-IR-PROTOTYPE / IFRS17-CSM-BUBBLE.
- Done archive imported: KICS-TIER1/2-UTIL / KICS-FORWARD-CAPITAL / IFRS17-HTML-DASH / F17 Panel 3 data / F5 / F6 data side / F1 cross-nav data hook.
- Hard rule retained from pushing: this stage **reports + recommends only**, never runs `git push`.
- Hard split with designer: publishing owns master JSONs; designer owns HTML. If a new master field needs HTML rendering, publishing reports `manual_html_edit` warn and stops — designer takes over.

---

## 2026-05-30 -- Forward sim v3 deployed + bond tier `(신종)` fix data refresh

**Forward sim v3 (`20260525T061947Z`):** confidence high **5** (+1). KR0032: `fsc_missing_t1` cleared, T1 gap 0%; still **low** on T2 face vs BS (over_deduct). KR0104: **high**. KR0072: **`fsc_missing_t1` remains** — FSC has only **called** tier1 (700억); BS still shows 2403억 outstanding 신종 (not in FSC outstanding cohort).

**Weak capital (document only, no "fix"):** KR0003 Lotte basic_cap **-3875**억 / basic ratio **-23.7%**; KR0072 KDB basic_cap **-3311**억. User-confirmed real stress, not parser error.

(Bond normalize itself = downloader; this entry is the publishing-side refresh that consumed it.)

---

## 2026-05-30 -- F17 Panel 3 clean 4-bar swap (data side)

`scripts/build_net_income_breakdown.py` → `data/dart/viz/net_income_breakdown.json`. Tier1 10/10 손보 OK. Panel 3 (IFRS17.html) swapped from raw-table-last-column 12-row horizontal bar dump to clean 4-bar 당기순이익 decomposition (보험손익 / 투자손익 / 영업외 → 당기순이익). 보험금융 + 보종별 caption.

Designer swapped HTML; publishing owned the JSON shape.

---

## 2026-05-28 -- IFRS17 yearly CSM amort F6 (data side)

`viz_build_ifrs17_panels.py`: `extract_amort_schedule` now emits `yearly` (y1..y10 + y10plus + total) and `granularity` alongside the existing 4-bucket `buckets` (kept — `viz_build_ifrs17_kpis.py` + bubble still read buckets). New helpers `_year_bucket_cell` / `_year_bucket_indices` / `_yearly_from_aligned` / `_extract_transposed_yearly`. `granularity='yearly'` only when >=7 of y1..y10 present.

Split: **16 yearly / 6 coarse / 2 no-data** (of 24); 22/24 ok unchanged.

(HTML panel 2 swap = designer 2026-05-28.)

---

## 2026-05-25 -- IFRS17 CSM 시계열 panel 6 data buildout (assembly side)

Stage 3 of the IFRS-HIST pipeline (stages 1+2 = downloader/parser):

- `viz_build_csm_waterfall_history.py`: reuses `pick_main_block` + `extract_stages` + `detect_unit_scale` from FY-only viz builder. Aggregates per-(insurer, period) snapshots into time-series payload.
- Coverage 20 → **257 ok + 2 partial** out of 299 reachable after measurement promote.
- Output: `data/dart/viz/csm_waterfall_history.json` (319KB, 23 companies × 13 periods).
- IFRS17.html Panel 6 data wiring: dual-axis line, 기말 CSM solid + 신계약 CSM dashed, 22 background lines (회색 spaghetti).
- nulls for `no_csm_block` periods (spanGaps: false) — visible as gaps in HTML.

Push #2 deployed: commit e846e5a (6 files, 9271 insertions). data file 200 OK at 319KB at https://solvencyk.github.io/insurequant/data/dart/viz/csm_waterfall_history.json (now path; previously templates/).

---

## Older entries

Pre-2026-05-25 publishing/gathering/viz entries are in the compressed historical archive of root `docs/claude-changelog.md` ("## Historical archive (compressed)"):

- IFRS17 CSM Waterfall picker (5 no_csm 손보사 → 0, MVP filter off, ceded penalty)
- K-ICS.html Phase 4 (자본성증권 도넛 + Forward Outlook 라인)
- Forward sim v2 (confidence per-row, capacity_exhausted cap)
- KICS-FORWARD-CAPITAL Phase 3 v1 (yearly × 5y, 19사 cohort)
- Bond calendar v3 (5y Call rule for ALL bonds, 3-status outstanding/called/matured)
- FSC schedule API per-insurer full pull (publishing-side normalize)
- HTML single-source refactor P1+P4 (cross-cutting refactor; designer side too)
