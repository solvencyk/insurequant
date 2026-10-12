# Insurequant Publishing TODO (Stage 4)

> 갱신 2026-10-12 · 프롬프트 `docs/agents/claude-agent-publishing.md` · 이력 `docs/changelog_publishing.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_publishing.md` 맨 위에 있다. publishing 은 마스터 JSON 만 쓰고 HTML 은 designer 몫이다.

## Status (최신 3개)

- **2026-10-12 타임라인 JSON 읽는 검사기 선언 + 죽은 선언 3개 정리(커밋만 · push 보류)** — 티켓 `20261012T1945Z`: `validate_live_artifacts.check_capsec_timeline`(구조·분류/인정액 필드 금지·회사별 권면 합·건수 == `data/bonds` 파생) 신설, `LIVE_ARTIFACT_READERS`·`PANEL_DERIVED_FROM` 선언, 변이시험 3개(`test_rule_coverage_manifest`). 나머지 1건 = 비공개 3시트(forward·tier1·tier2) 선언이 ghost 검사에 걸린 것, 선언 삭제로 해소.
  남은 것: ① 배포 전 시험으로 앞당기기(작업 브랜치 HTML fetch 목록 대 선언)는 의견만, 구현 별도 ② 타임라인은 시트와 125건 중 122건만 일치(3건 타임라인 전용·1건 시트 전용)라 시트 열 수준 대조는 안 걸었다.

- **2026-10-12 비공개 3시트 + 자본성증권 공개 열 제한 + 뮌헨·스위스리 재동기화(커밋만 · push 보류)** — 티켓 `1420Z`·`1440Z`: 기본자본소진율·보완자본소진율·자본비율전망 공개 스냅샷 3개 삭제(manifest 에서도 제외), main 에서는 배포 스크립트 `PRIVATE_PATHS` 가 이 3개 + 루트 JSON 3개(tier1·tier2·forward)를 `git rm`. `자본성증권발행현황` 공개본은 한도·인정액 계산 열 7개 제외(123행 불변). 뮌헨 K-ICS공시 +3행·스위스리 보험계약부채 +8행(「계산값(전 행 합)」 표기) xlsx·공개본·`csm_combo` 패널 반영. 새 시험 `tests/test_private_deploy.py`.
  남은 것: ① 폰 배포는 `git checkout -B <브랜치> origin/<브랜치>` 로 새 스크립트를 먼저 받은 뒤 1회 실행(안 받고 옛 스크립트로 돌리면 2회) ② 배포 건조 실행 시험은 부하가 큰 PC 에서 시험당 5분 안팎 ③ 증빙 `data/_derived/private_sheets_20261012/`.

- **2026-10-12 최종 재동기화(push 직전 정합, 커밋만 · push 보류)** — xlsx 5시트(`17BS` 처브 6칸·`CSM상각` 18칸·`손익분해PL` +7행/1칸·`보험계약부채` 18칸·`K-ICS공시` +16행/4칸)·손해율 패널(재보사 세그먼트 표준화)·combo(처브)·compare(2칸) 재빌드·`public_exports`(`538cbe7`·`dee37c2`). 드리프트 0, data-contract RED 0, live_artifacts RED 0(baselined 25), 시험 142 passed.
  남은 것: ① `downstream_kpis.json` 은 어느 HTML 도 안 읽고 이번 변경이 아닌 옛 `cf66dce`(상각 스케줄 정정) 미반영분(213칸) 때문에 어긋나 있어 재빌드본을 커밋하지 않음(`downstream_kpis.rebuilt_NOT_COMMITTED.json`) ② `viz_build_nb_csm_ratio.py` 는 IR 원문 입력이라 이번 마스터와 무관해 생략 ③ 상세 `data/_derived/final_resync_20261012/runlog.md`.

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
