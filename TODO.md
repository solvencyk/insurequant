# Insurequant TODO — cross-stage

> 갱신 2026-10-07 · 사실(게이트·inbox·커버리지)은 `scripts/status_report.py --fast` 가 정본이고, 이 파일은 의도만 적는다.
> stage 별 TODO·프롬프트·이력 위치는 `CLAUDE.md` §1. 2026-10-07 정리 전 전문은 `docs/todo_archive_root.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-07 문서·inbox 정리.** TODO 8개를 열린 일 위주로 다시 썼다(정리 전 전문은 각 `docs/todo_archive_*.md` 맨 위).
  K-ICS 예외 등재부 → `docs/kics_gate_exceptions.md`, 분기 라운드 절차 → `docs/flows/kics_quarterly_round.md`. inbox 활성 10 → 4.
  서브에이전트 모델을 `sonnet`/`opus` 별칭으로 바꿔 최신 모델을 따라가게 했다.
- **2026-10-06 AIA생명 2024.4Q 항목46 단위 정정(3607646 → 36076.46) + `PUBLIC_EXPORT_INTERNAL_JARGON` 신설.**
  라이브 `main` `420cdc3`(build_id `54ec835`, owner 폰 배포). 상세 `docs/changelog_parser_kics.md`·`docs/changelog_validation.md` 2026-10-06.
- **2026-09-22 금리 듀레이션갭 마스터 신설** — `kics_duration_gap.json`(39사 × 짝수분기 270셀, 분모 = 금리위험액 현황 자산총계)
  + 라이나생명 2023.4Q PL 20칸. 라이브 `22e2471`. 상세는 archive.

## 열린 일

- [ ] **2026.3Q 정기경영공시 라운드** — 2Q 는 8/29~31 에 게시됐으니 3Q 는 11월 말 예상. 절차 `docs/flows/kics_quarterly_round.md`
  (라벨·스크립트를 3Q 로 바꿔 쓴다). owner 가 부르기 전에는 시작하지 않는다.
- [ ] **J-ESR 10월 말 재census**(기한 2026-10-31 직후) → `TODO_jp.md`.
- [ ] **inbox 열린 4건** — parser 3(PL 부모 #2 결측 26버킷 · 메리츠 2026.2Q item2/3 적용후 stale 외 · 금리민감도 phase 31칸)
  + publishing 1(자본성증권 step_up·잔액기준일·한화 item54). 남은 일은 각 티켓 맨 아래 「현황」.
- [ ] **PL 골든 실패** — `RUN_PL_GOLDEN=1` 에서 `sha256_coverage` 만 어긋난다(라이나 KR0074 2023.4Q coverage 1행). → `TODO_parser_ifrs17.md`.
- [ ] **owner 판단: KR0004 의 2025.4Q 법인** — K-ICS 마스터는 예별손해보험(가교사), PL 마스터는 엠지손해보험 잔여법인이다. → `TODO_parser_ifrs17.md`.

## 보류 (재개 조건이 오면 연다)

- F18 IR factsheet 정형화 + DART↔IR 교차검증 — owner 2026-08-30 "꼭 필요할 때만". raw 130파일, parsed 6파일.
- F13 재보험 영업 지표 — downloader F8(손보협회 비교공시) 수집이 선행.
- 중장기 제품·수익화 트랙 — `docs/roadmap.md`.

## 정책 (cross-stage)

| # | 결정 | 날짜 |
|---|---|---|
| 3 | NB CSM ratio denominator: **월납환산 신계약보험료** | 2026-05-24 |
| 5 | API keys: repo root `.env` only (gitignored). Never commit/log key values | 2026-05-24 |
| 6 | Bond Call rule: issue + 5y for ALL bonds. Past 5y = assume `called` (갱신: 콜 지난 미상환분은 `TODO_publishing.md` 2026-09-23) | 2026-05-24 |
| 7 | Pushing: subagent **reports + recommends only**. 라이브 `main` 배포는 owner GO | 2026-05-30 |
| 8 | DART attachments (별첨/감사보고서 zip): **don't fetch**. Body XML has all IFRS17 disclosures | 2026-05-30 |

## 참조 (필요할 때만 연다)

- K-ICS 게이트 documented exceptions: `docs/kics_gate_exceptions.md`
- 분기 라운드 절차: `docs/flows/kics_quarterly_round.md`
- Status 이력·정리 전 전문: `docs/todo_archive_root.md`
