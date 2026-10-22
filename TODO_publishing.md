# Insurequant Publishing TODO (Stage 4)

> 갱신 2026-10-23 · 프롬프트 `docs/agents/claude-agent-publishing.md` · 이력 `docs/changelog_publishing.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_publishing.md` 맨 위에 있다. publishing 은 마스터 JSON 만 쓰고 HTML 은 designer 몫이다.

## Status (최신 3개)

- **2026-10-23 parser `afea4342`(READY-25 최신 비교열 · 9사 KR0001 KR0003 KR0010 KR0068 KR0070 KR0079 KR0083 KR0099 KR0104 · PL 440 + CSM 55셀) 파생 산출물 재생성(커밋 전)** — xlsx 3시트만 cherry-pick: `CSM워터폴` 132셀 · `손익분해PL` 1,045셀 · `신계약CSM배수` 20셀(NB_CSM_multiple.json 20셀을 셀 단위로 갱신, 메리츠 KR0001·한화생명 KR0068 2023.1Q~3Q뿐), 나머지 16시트 값 동일(수식·피벗·차트 거부 없음, 백업 `insurequant_master_tables.xlsx.bak_20261023_ready25`).
  `panel_compare.json` 사별 91값 + 손보 ROE 중앙값 1(기말 CSM 11 · 보험손익 20 · 투자손익 22 · 당기순이익 22 · ROE 8 · 신계약CSM 4 · 배수 4, 큰 이동 한화생명 신계약CSM 2023.2Q 13,592 -> 11,643억, 메리츠 기말 CSM 2023.2Q 100,684 -> 97,015억), `panel_csm_combo.json` 20값(신계약 CSM 6 + 대조 메타 `csm_mismatch` 4 -> 3). 공개본 `손익분해PL` 1,045 · `CSM워터폴` 132 · manifest build_id `afea4342`.
  `check_master_xlsx_drift` RED 2 -> 0 · `validate_live_artifacts` RED 6 -> 0(NB_VS_WATERFALL 4 + PUBLIC_EXPORT_DRIFT 2) · `validate_data_contract` RED=0 · YELLOW 169 불변 · `validate_master_tables --no-build` 요약이 parser 골든과 동일 · 골든 3종 · `test_rule_coverage_manifest` 104 · deploy_assets 12 · push_gate_wiring 66.
  화면 노출: compare.html 0값 · CSM 워터폴/NB/콤보 0값 · IFRS17.html 3번 패널(PL 연도모드 4Q) 39셀만(KB손보 2023.4Q 15 · 미래에셋 2023.4Q 11 · 푸본현대 2024.4Q 10 · ABL 2024.4Q 3). 남은 것: 커밋 뒤 `export_public_sheets.py` 재실행(신계약CSM배수 20셀 + build_id). 증빙 `data/_derived/remaining_20261022/e21_ready25/p5_resync/`.

- **2026-10-23 parser `5419a817`(최신 비교열 21버킷 · 11사 KR0032 KR0068 KR0069 KR0070 KR0071 KR0072 KR0082 KR0083 KR0087 KR0094 KR0104 · 값 84 + 값_당분기 110셀) 파생 산출물 재생성(커밋 전)** — xlsx `손익분해PL` 1시트만 cherry-pick 194셀(전부 11사, 13801행 불변), 나머지 18시트 값 동일(수식·피벗·차트 거부 없음, 백업 `insurequant_master_tables.xlsx.bak_20261023_pl_e20`).
  `panel_compare.json` 9값뿐(보험손익 3 · 투자손익 4 · 당기순이익 1 · ROE 1 = NH농협손보 2023.1Q · DB생명 2023.1Q/2Q · 푸본현대 2024.3Q), 중앙값·메타 불변. `panel_csm_combo.json` 은 `--check` 만(불변). 공개본 `손익분해PL` 194셀(11사) + manifest build_id `5419a817`.
  `check_master_xlsx_drift` RED 1 -> 0 · `validate_data_contract` RED=0 · YELLOW 169 불변 · `validate_master_tables --no-build` 요약은 직전과 같고 `oci_vs_bs_aoci` 23Y -> 21Y 만 달라짐(parser 쪽 실측과 동일) · 골든 3종 · `test_rule_coverage_manifest` 104 · live_artifacts RED=0.
  2023.1Q/2Q 바뀐 값은 화면에 안 나온다(compare.html 은 최신 분기만 · IFRS17.html 표는 4Q+최신 / 최근 5분기 창). 남은 것: 재커밋 뒤 `export_public_sheets.py` 로 build_id 재생성. 증빙 `data/_derived/remaining_20261022/e20_held_and_remaining/p4_resync/`.

- **2026-10-22 parser `acdb2fe9`(최신 비교열 19버킷 · 7사 KR0005 KR0032 KR0070 KR0082 KR0083 KR0087 KR0104) 파생 산출물 재생성 · 배포 완료(push `2a05378c`, main `80ba3c1d`, 라이브 4파일 바이트 일치 · build_id `acdb2fe9` 확인, 콘솔 오류 0)** — xlsx `손익분해PL` 1시트만 cherry-pick 386셀(값 171 + 값_당분기 215), 전부 7사, 나머지 18시트 값 동일(수식·피벗·차트 거부 없음).
  `panel_compare.json` 55값(보험손익 1 · 투자손익 19 · 당기순이익 18 · ROE 17 중 사별 51 + 그룹 중앙값 4), 사별 값은 전부 7사. `panel_csm_combo.json` 은 PL_breakdown 을 읽지 않아 `--check` 만(불변). 공개본 `손익분해PL` 386셀(7사) + manifest build_id `acdb2fe9`.
  `check_master_xlsx_drift` RED 1 -> 0 · `validate_data_contract` RED 1 -> 0 · YELLOW 169 불변 · `validate_master_tables --no-build` 요약 불변 · 골든 3종 · `test_rule_coverage_manifest` 104 · live_artifacts RED=0.
  남은 것: 재커밋 뒤 `export_public_sheets.py` 로 build_id 재생성(HEAD 가 바뀌므로). 증빙 `data/_derived/remaining_20261022/p3_resync/`.

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
