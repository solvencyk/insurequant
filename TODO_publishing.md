# Insurequant Publishing TODO (Stage 4)

> 갱신 2026-10-12 · 프롬프트 `docs/agents/claude-agent-publishing.md` · 이력 `docs/changelog_publishing.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_publishing.md` 맨 위에 있다. publishing 은 마스터 JSON 만 쓰고 HTML 은 designer 몫이다.

## Status (최신 3개)

- **2026-10-12 미니 재동기화 2차(재보사 재스윕 반영, 커밋만 · push 보류)** — xlsx 7시트(`손익분해PL` +303행·25칸, `17BS` +49, `CSM워터폴` +18, `CSM상각` +15, `가정민감도` +6, `보험계약부채` +110, `신계약CSM배수` +3)·NB 마스터 +3행(재보사, 배수 null)·combo/compare 재빌드(재보사만)·`public_exports`(`b4b6a71`·`5079688`). 드리프트 0, data-contract RED 102(전부 `CONCEPT_MIXED_DISCLOSURE_INTO_DART`), live_artifacts RED 0.
  남은 것: ① `CONCEPT_MIXED_DISCLOSURE_INTO_DART` 102 는 validation ② ifrs17 viz 4패널·csm_waterfall 은 바이트 동일(신규 재보사 행이 전부 최신 분기 아님) ③ compare 패널 손해율 항목은 직전 라운드(`66e6156`) 재보사 행을 이번에 처음 반영. 상세 `data/_derived/mini_resync_20261012/runlog.md`.

- **2026-10-12 재보사 손해율 패널·xlsx 동기화(커밋만 · push 보류)** — `panel_loss_ratio.json` 37→44사(재보사 7곳 추가·기존 37사 바이트 동일)+최상위 `ae` 블록(예실차 162행·44사), xlsx `손해율` +1,904행(변경 셀 0).
  남은 것: ① designer 가 `ae` 를 화면에 표시(`meta.note` 참조) ② 예실차(`claims_ae_ratio.json`)·긴 형식 표(`risk_premium_vs_expected_claims.json`)는 xlsx 시트가 없다 → 신설은 owner 승인(`build_master_xlsx.py` 스키마) ③ `public_exports/` 는 다른 마스터가 끝난 뒤 마감 라운드에서.

- **2026-10-11 미니 재동기화(라이나 CSM·PL 항목 4·상각 정정, 커밋만 · push 보류)** — xlsx 4시트(`5d320c9`)·NB 마스터 재빌드·combo/compare 재빌드·`public_exports`(`812b007`). 드리프트 0, data-contract RED 0, live_artifacts RED 8(`INSPL_CENSUS_MISSING` 뿐, `NB_CENSUS_MISSING` 0).
  남은 것: ① 골든 `test_viz_ifrs17_panels_golden`(`csm_amort_schedule` 해시만)·지문 `--update` 는 validation ② 라이나 상각 스케줄은 패널에 안 간다(패널 행이 DART 원천) — 화면에 싸지 owner 판단. 상세 `data/disclosure/_meta/mini_resync_runlog_20261011.md`.

## 열린 일

- [ ] **자본성증권 후속 3건** — `inbox/publishing/20260923T1130Z` §1 `step_up` 플래그(원문 근거 있는 건만 true) · §2 후순위 `잔액기준일` 이
  2025-12-31 로 두 분기 낡음(공시 주기 문제면 시트 설명에만 적는다) · §3 한화생명 item54 17,932억 vs 인벤토리 14,712억(원문 TFI 표 정의부터 확인).
- [ ] **공개 다운로드 잔여 내부 문구 4건**(2026-10-06 snake_case 스캔, jargon 룰 4패턴 밖이라 게이트는 통과) — 가정민감도 `비고` 1행 ·
  기본자본소진율 22행 · 자본성증권발행현황 `비고` 123행·`콜근거` 59행. 고칠지 owner 판단.
- [ ] **듀레이션갭 3개 분기 화면 도달 불가** — 분기 셀렉트가 `kics_rate_sensitivity`(4분기)에서 나와 2023.2Q·2023.4Q·2024.2Q 를 못 고른다.
  셀렉트 소스 확장은 owner 판단(designer 와 같이).

## 휴면 / 보류

F4 v2 forward confidence(Cat C/D 리서치·외국계 분류 helper) · F13 재보험 영업 지표(downloader F8 선행) · F17 Tier2 LOB viz(parser 결정 대기) ·
F18 IR 통합·MISC-IR-NB-DENOM·MISC-IR-PROTOTYPE(IR 파싱 보류) · CAPSEC-SAMO-GAP 사모채 5사 처리 방식 결정(`TODO_downloader.md`).
