# Insurequant Publishing TODO (Stage 4)

> 갱신 2026-10-19 · 프롬프트 `docs/agents/claude-agent-publishing.md` · 이력 `docs/changelog_publishing.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_publishing.md` 맨 위에 있다. publishing 은 마스터 JSON 만 쓰고 HTML 은 designer 몫이다.

## Status (최신 3개)

- **2026-10-19 밤 손해율 비교 단위 데이터 + 위험보험료 단위환산 정정 + 반올림 통일(push `a8d9f193` · main 배포 `5221a1b4` 완료)** — `viz_build_compare_panel.py` 가 `loss_curve` 에 `units`(12) · `default_unit` · `u` · `up` · `med_u` · `unit_note` · `unit_rule` · `alt_co`, `loss_pv` 에 `vu` · `medu` 를 더함, `panel_loss_ratio.json` 잎 행 5번째 원소 = 위험보험료(억원). **마스터 위험보험료는 이미 억원인데 두 빌더가 백만원 공시사를 또 ÷100 해 100배 작게 싣던 것 정정.** 반올림을 이진값 기준 half-up 으로 통일(**compare 값 93칸 +0.1**, IFRS17 표시와 일치).
  검증: 마스터 독립 재계산 불일치 0(5,328칸 · 중앙값 · 위험보험료 13,127칸 · alt_co), 신규 `tests/test_loss_unit_panels_vs_master.py`(옛 ×0.01 변이로 실제 실패 확인, `prepush_check.py` 배선). 남은 것: 빌더 `--check` 는 재현성만 보므로 마스터 대조는 위 테스트가 맡음.
- **2026-10-19 IFRS17 8절 현재가치 이중 반올림 수정(티켓 `20261018T0700Z` resolved; main 배포 `f96f06b0` 완료)** — `viz_build_persistency_lossratio_panels.py` 가 반올림 전 비율(소수 6자리)을 싣도록 고침, `panel_loss_ratio.json` 206 → 282KB. 화면 표시값과 마스터 재계산 차이 0.05pp 초과 약 800칸 → 0(독립 검증).
  남은 것: 배포 때 이 JSON 을 HTML 과 같이(기존 파일 갱신이라 NEW_FILES 불필요) · validation 티켓 `20261019T0200Z`(카카오페이손보 잎 합 85.7 대 합계 행 100.0 등)가 parser 로 route 되면 마스터 보정 후 패널 재빌드.
- **2026-10-13 parser-ifrs17 `b8c37fff`(249 셀) 파생 산출물 재생성(커밋 `99c7ead7` · push 보류)** — RED NB_VS_WATERFALL(메리츠 2023.3Q) 해소: `NB_CSM_multiple.json` 12칸(동양 2023.1Q·2Q, 메리츠 2023.3Q·4Q) · `data/compare/panel_compare.json` 69잎(63 = b8c37fff·NB, 6 = 기존 낡음) · `data/csm_combo/panel_csm_combo.json` 8잎 · xlsx `신계약CSM배수` 12칸 · 공개본 `신계약CSM배수`. `viz_build_ifrs17_panels`·`viz_build_csm_waterfall` 은 `data/dart/extracted` 를 읽어 재실행해도 HEAD 와 바이트 동일(변경 없음).
  남은 것: ① validation: viz 골든 2종·IFRS17 골든(이 커밋 뒤에 실행) ② 증빙 `data/_derived/ifrs17_regen_20261013/`.



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
