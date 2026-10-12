# Insurequant Publishing TODO (Stage 4)

> 갱신 2026-10-12 · 프롬프트 `docs/agents/claude-agent-publishing.md` · 이력 `docs/changelog_publishing.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_publishing.md` 맨 위에 있다. publishing 은 마스터 JSON 만 쓰고 HTML 은 designer 몫이다.

## Status (최신 3개)

- **2026-10-12 발행사 처리 기준 재분류 + 증권별 X 검정(커밋만 · push 보류)** — 티켓 `20261012T2115Z`: 하나생명 제1회·교보 2024-11 `type` tier2 -> tier1(발행사 K-ICS 표가 기본자본형으로 처리), 나머지 tier2 증권 10개사 12건은 발행 분기 X(항목13-49) 검정으로 보완자본형 확인, 판정 불가 3건(푸본 600·농협생명 제5회·코리안리 제6회)은 현 분류 유지(`issuer_check`). 소진율 tier1 은 하나생명 0.0 -> 238.2 만 변경(교보 70.1 불변), tier2·총자본 경로 불변, forward 의 `baseline_basis_flag` 류 필드는 사라짐. `tier1_overflow_into_tier2_eok`(공개 시트 1칸)가 옛 채권원장 추정(하나생명 665.7)으로 낡아 있던 것을 기본자본 소진율과 같은 출처(1,043.6)로 47사 통일 (`dbbffcb5`).
  남은 것: ① owner: 판정 불가 3건의 발행사 처리 확인 필요 시 별도 근거(원문 표 재독)가 필요 ② 증빙 `data/_derived/capsec_reinstate_20261012/x1~x6` ③ 기존 DB손보 5건(기본자본형)은 이번 범위 밖 - 같은 X 검정 미실시.

- **2026-10-12 소진율 도넛 + Forward Outlook 재공개(커밋만 · push 보류)** — 티켓 `20261012T2030Z`: 등재부 재분류(하나생명 제1회·푸본 600·농협생명 제5회·코리안리 제5/6회 -> tier2 확정, 교보 2024-11 type=tier2 + `issuer_type`=tier1) -> 소진율 tier1 만 4사 변경(하나생명 238.2->0.0 · 코리안리 205.1->94.0 · 농협생명 72.7->48.5 · 푸본 42.1->17.3), tier2 불변. forward 가 증권별 계층(기발행 15% · 기본자본형 10% · 보완자본형 기본자본 0)을 따르고 총자본 경로는 47사 불변. 비공개 목록 3종 비움 + 공개 스냅샷 3시트 재생성 (`ef62969`·`2729a53`).
  남은 것: ① designer: K-ICS.html fetch 복원과 같은 커밋에서 `LIVE_ARTIFACT_READERS` 에 루트 JSON 3개 선언(`tests/test_push_gate_wiring.py`) · `tests/test_deploy_assets.py` 의 「fetch 안 함」 단정 뒤집기 · `download-survey.js` 주석 해제 · `report-widget.js` 목록 ② owner: DB손보 2026 신종 3건·하나손해·하나생명은 census 1차가 다르게 읽음(아래 changelog), census 최종본 대조 ③ 증빙 `data/_derived/capsec_reinstate_20261012/`.

- **2026-10-12 타임라인 JSON 읽는 검사기 선언 + 죽은 선언 3개 정리(커밋만 · push 보류)** — 티켓 `20261012T1945Z`: `validate_live_artifacts.check_capsec_timeline`(구조·분류/인정액 필드 금지·회사별 권면 합·건수 == `data/bonds` 파생) 신설, `LIVE_ARTIFACT_READERS`·`PANEL_DERIVED_FROM` 선언, 변이시험 3개(`test_rule_coverage_manifest`). 나머지 1건 = 비공개 3시트(forward·tier1·tier2) 선언이 ghost 검사에 걸린 것, 선언 삭제로 해소.
  남은 것: ① 배포 전 시험으로 앞당기기(작업 브랜치 HTML fetch 목록 대 선언)는 의견만, 구현 별도 ② 타임라인은 시트와 125건 중 122건만 일치(3건 타임라인 전용·1건 시트 전용)라 시트 열 수준 대조는 안 걸었다.

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
