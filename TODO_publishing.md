# Insurequant Publishing TODO (Stage 4)

> 갱신 2026-10-22 · 프롬프트 `docs/agents/claude-agent-publishing.md` · 이력 `docs/changelog_publishing.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_publishing.md` 맨 위에 있다. publishing 은 마스터 JSON 만 쓰고 HTML 은 designer 몫이다.

## Status (최신 3개)

- **2026-10-22 교보생명(KR0073) 마스터 재교정 2건(parser `e01f1395` 기타포괄손익 13셀 · `59e6e459` 17BS 6셀 · 보험계약부채 3셀) 파생 산출물 재생성(커밋 전)** — xlsx 시트 3개만 cherry-pick(`손익분해PL` 31셀 · `17BS` 6셀 · `보험계약부채` 4행 교체=값 3셀+기준표시/비고), 전부 KR0073, 나머지 16시트 값 동일.
  `panel_csm_combo.json` 3값 + `meta.restated` 1(2023.4Q 소급재작성 표지) · `panel_compare.json` 7값(ROE 4 · 자본 1 · 자산 2), 전부 KR0073. 공개본 3시트(교보 28행) + manifest build_id `9dfd28f9`. `check_master_xlsx_drift` RED 4 -> 0, `validate_data_contract` RED=0 · YELLOW 169 불변,
  `validate_master_tables --no-build` 불변 · 골든 3종 · `test_rule_coverage_manifest` 104 통과. 남은 것: 재커밋 뒤 `export_public_sheets.py` 로 build_id 재생성(HEAD 가 바뀌므로). 증빙 `data/_derived/remaining_20261022/p2_resync/`.

- **2026-10-22 교보생명(KR0073) 마스터 교정(parser `3e53aef8`) 파생 산출물 재생성 · 배포 완료(push `aefad044`, main `1a73d4c2`, 라이브 9파일 바이트 일치 · build_id `5f818b59` 확인)** — xlsx 시트 3개만 cherry-pick(`CSM워터폴` 91셀 · `손익분해PL` 274셀 · `신계약CSM배수` 27셀, 전부 KR0073, 나머지 16시트 값 동일), `NB_CSM_multiple.json` 27셀 · `panel_compare.json` 31값 · `panel_csm_combo.json` 19값(전부 KR0073). `check_master_xlsx_drift` RED 2 -> 0, `validate_data_contract` RED=0.
  2라운드(parser `5f818b59`, 교보 2023.3Q `값_당분기` 19셀): xlsx `손익분해PL` 19셀 재동기화 · 공개본 재생성(교보 19행 + manifest build_id `5f818b59`), 게이트 RED 0. 남은 것: 재커밋 뒤 배포 시 origin/main 과 다른 파일은 `CSM_waterfall.json` · `PL_breakdown.json` · `NB_CSM_multiple.json` · 패널 2종 · 공개본 3시트 · manifest 뿐(HTML·viz 패널은 main 과 동일). 증빙 `data/_derived/kyobo_publishing_20261022/`.

- **2026-10-19 밤 손해율 비교 단위 데이터 + 위험보험료 단위환산 정정 + 반올림 통일(push `a8d9f193` · main 배포 `5221a1b4` 완료)** — `viz_build_compare_panel.py` 가 `loss_curve` 에 `units`(12) · `default_unit` · `u` · `up` · `med_u` · `unit_note` · `unit_rule` · `alt_co`, `loss_pv` 에 `vu` · `medu` 를 더함, `panel_loss_ratio.json` 잎 행 5번째 원소 = 위험보험료(억원). **마스터 위험보험료는 이미 억원인데 두 빌더가 백만원 공시사를 또 ÷100 해 100배 작게 싣던 것 정정.** 반올림을 이진값 기준 half-up 으로 통일(**compare 값 93칸 +0.1**, IFRS17 표시와 일치).
  검증: 마스터 독립 재계산 불일치 0(5,328칸 · 중앙값 · 위험보험료 13,127칸 · alt_co), 신규 `tests/test_loss_unit_panels_vs_master.py`(옛 ×0.01 변이로 실제 실패 확인, `prepush_check.py` 배선). 남은 것: 빌더 `--check` 는 재현성만 보므로 마스터 대조는 위 테스트가 맡음.

## 열린 일

- [ ] **자본성증권 후속 3건** — `inbox/publishing/20260923T1130Z` §1 `step_up` 플래그(원문 근거 있는 건만 true) · §2 후순위 `잔액기준일` 이
  2025-12-31 로 두 분기 낡음(공시 주기 문제면 시트 설명에만 적는다) · §3 한화생명 item54 17,932억 vs 인벤토리 14,712억(원문 TFI 표 정의부터 확인).
  §3 참고(2026-10-12): 항목 54 분기 시계열·원장 대조 `data/_derived/capital_utilization_apply_20261012/a2·a3` — 2023.3Q 에 +5,628(신규 후순위 발행 분기) 뒤 2023.4Q -8,439.
- [ ] **공개 다운로드 잔여 내부 문구 4건**(2026-10-06 snake_case 스캔, jargon 룰 4패턴 밖이라 게이트는 통과) — 가정민감도 `비고` 1행 ·
  기본자본소진율 22행(2026-10-12 재정의 후 문서 경로가 남은 100% 초과 행 7행) · 자본성증권발행현황 `비고` 123행·`콜근거` 59행. 고칠지 owner 판단.
- [ ] **듀레이션갭 3개 분기 화면 도달 불가** — 분기 셀렉트가 `kics_rate_sensitivity`(4분기)에서 나와 2023.2Q·2023.4Q·2024.2Q 를 못 고른다.
  셀렉트 소스 확장은 owner 판단(designer 와 같이).

## 휴면 / 보류

F4 v2 forward confidence(Cat C/D 리서치·외국계 분류 helper) · F13 재보험 영업 지표(downloader F8 선행) · F17 Tier2 LOB viz(parser 결정 대기) ·
F18 IR 통합·MISC-IR-NB-DENOM·MISC-IR-PROTOTYPE(IR 파싱 보류) · CAPSEC-SAMO-GAP 사모채 5사 처리 방식 결정(`TODO_downloader.md`).
