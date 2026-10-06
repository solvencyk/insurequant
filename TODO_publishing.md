# Insurequant Publishing TODO (Stage 4)

> 갱신 2026-10-07 · 프롬프트 `docs/agents/claude-agent-publishing.md` · 이력 `docs/changelog_publishing.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_publishing.md` 맨 위에 있다. publishing 은 마스터 JSON 만 쓰고 HTML 은 designer 몫이다.

## Status (최신 3개)

- **2026-10-06 라이브 `main` `420cdc3`(owner 폰 Termux 배포)** — `kics_disclosure.json` + public_exports 5종(K-ICS공시·손익분해PL·자본비율전망·
  자본성증권발행현황·manifest). build_id `54ec835`. 그 전 배포는 2026-09-28 `0187cf4`(자본비율전망 과거콜 미상환 교정).
- **2026-09-23 자본비율전망 '콜 지났는데 미상환' 처리** — 콜 경과 미상환 채권은 법정만기 기준 계단식 체감(인정표 빌더의 `tier2_recognition_rate` 를 import).
  8개사 40칸 상승(구 모델이 과대차감). 악사손해 JPY 사모 459억은 만기 미공시라 종전 동작 유지. `60ca347`.
- **2026-09-23 자본성증권 후순위 체감 기준을 콜 → 법정만기로 교정** + `법정만기일` 열 신설. 2026.2Q 보완자본 인정액 106,084 → 208,011억. `b3fd1ff`.

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
