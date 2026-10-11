# Insurequant Publishing TODO (Stage 4)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-publishing.md` · 이력 `docs/changelog_publishing.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_publishing.md` 맨 위에 있다. publishing 은 마스터 JSON 만 쓰고 HTML 은 designer 몫이다.

## Status (최신 3개)

- **2026-10-11 마감 라운드(커밋만, push·배포 보류)** — xlsx 12시트 동기화(`8848cb8`, 드리프트 0)·`public_exports` 재생성(`61babb6`)·IFRS17 viz 상각/민감도에 재보사 7곳(`17dca81`)·csm_combo(48사)/compare 재빌드(`89ecf9a`)·서울보증 forward 제외 행·tier 스크립트 회사명 수정. 게이트 data-contract RED 22(알려진 것만), `MASTER_XLSX_*` 0.
  남은 것: ① 골든 `test_viz_ifrs17_panels_golden`(+7/+7 행)·지문 `--update` 는 validation ② `validate_live_artifacts` 새 RED 26 = `INSPL_CENSUS_MISSING` 8(`NB_CENSUS_MISSING` 18 은 orchestrator 승인으로 NB 마스터 +18행(`1412aaf`)·xlsx/공개본(`04ea6c6`)으로 해소)(보험손익 원표 viz 는 DART 표라 재보사 없음) — 마스터 추가 승인 또는 게이트 면제는 owner/validation ③ designer 티켓 2건(K-ICS `exclusion_reason` 읽기, IFRS17 상각 차트 y축 100배 작게 찍힘 — 라이브에도 있는 것으로 보임). 상세 `data/disclosure/_meta/final_resync_runlog_20261011.md`.

- **2026-10-11 보험계약부채 시트 신설** — `insurance_liability_portfolio.json`(6,111행) -> xlsx 시트 `보험계약부채`(17번째, 시트 sync 만, 기존 16시트 값 SHA 동일) + `public_exports/보험계약부채.json`(`--only` 로 1개 + manifest 항목 1개). 열 = 마스터 + 단위·기준표시·비고. `MASTER_SHEET_PENDING` 삭제, 시트 수 선언 17/15.
  KB라이프 tier1/tier2 `company` 1칸 `KB라이프생명` 으로 정정(도넛 '데이터 없음' 해소). 남은 것: designer `download-survey.js` SHEETS 에 1줄 추가(없으면 다운로드 목록에 안 나옴) · 컴퓨트 스크립트 재실행 시 옛 이름 부활 방지 · 다른 에이전트 완료 후 나머지 시트 sync + public_exports 전체 재생성. 상세 `data/disclosure/_meta/ilp_master_sheet_runlog.md`.

- **2026-10-11 재보사 8곳(KR1101~1108) Forward Outlook·소진율 추가** — 원인=데이터 부재(재보사가 9/23·9/1 산출 뒤에 마스터 편입; 이름 불일치 아님). `scripts/add_reinsurers_to_capsec_panels.py`(추가만)로 bond 소스·tier1/2·배포본 8행씩, forward 빌더 동일 인자 재실행(38→46행). 기존 행 변경 0.
  스코리 190.13%→181.15%(2030) 우하향, 비적용 7곳 flat. 스위스리 보완자본 소진율만 빈 칸(보완자본 4,274억인데 한도 적용 전 '-'). 남은 것: 3시트 xlsx 동기(기본자본소진율·보완자본소진율·자본비율전망)+public_exports 재생성, KB라이프 tier 행 이름(`케이비라이프생명보험`) 불일치. 상세 `data/disclosure/_meta/reinsurer_forward_capsec_runlog.md`.


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
