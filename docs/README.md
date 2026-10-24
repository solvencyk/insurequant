# docs/ 색인

> 2026-10-14 작성. 세션 시작 때 읽는 문서는 아래 「읽는 문서」 표뿐이다. 나머지는 과거 결정의 근거가 필요할 때만 연다. 문서 쓰기 규칙 정본은 `agents/doc-style.md`.

## 읽는 문서 (세션 시작)

| 문서 | 용도 |
|---|---|
| `../CLAUDE.md` → `../TODO.md` → `../TODO_<stage>.md` | 룰 → cross-stage 열린 일 → 자기 stage 열린 일 |
| `agents/claude-agent-<stage>.md` | stage 별 프롬프트(parser 는 `claude-agent-parser.md` + `domains/claude-agent-{kics,ifrs17}.md`) |
| `agents/source-catalog.yaml` | downloader 가 다루는 소스 정본 |
| `kics_gate_exceptions.md` · `agents/kics-json-validation-rules.md` | K-ICS 게이트 예외 등재부(owner 만 등재) · 룰 공식·허용오차 |

## 하위 폴더

| 폴더 | 내용 |
|---|---|
| `agents/` | stage 프롬프트, 문서 스타일, 검증 룰 |
| `domains/` | 도메인 설계 참고(K-ICS·IFRS17, 그리고 `csm-pl-basis-methodology.md`). jp 도메인 문서는 브랜치 `lane/jp` 에만 있다. 충돌 시 코드와 스킬이 우선 |
| `flows/` | 흐름도 |
| `parser/` | parser 레인 조사 메모 |
| `postmortems/` | 사고 사후 분석 |
| `design_refs/` · `ip/` | 디자인 참고, 지식재산 자료 |
| `archive/` | 끝난 문서(예: `2026-06_oneshot/` = 6월 수집 현황·시각화 제안·아침 보고, `handoff_20261007_*.md` · `handoff_20261008_*.md` = 신규 도메인 인수인계, `mockups/compare/` = 사별 비교 목업) |
| `changelog_archive/<stage>/<YYYY-MM>.md` | 월 지난 changelog (`scripts/doc_rotate.py`) |

## 이력 (읽지 않는 문서)

- `changelog_<stage>.md` — stage 별 최신 두 달. 더 오래된 것은 `changelog_archive/`. `changelog_parser.md` 는 2026-06-13 분리 전 동결본.
- `claude-changelog.md` — cross-stage 변경·배포 라운드.
- `todo_archive_<이름>.md` — TODO 에서 밀려난 Status·끝난 블록(무수정 이동, 최신이 위).
- `claude-md-history.md` — `CLAUDE.md` 2026-09-12 이전 전문.

## 루트에 남아 있는 참고 문서

| 문서 | 용도 |
|---|---|
| `roadmap.md` · `strategy-monetization.md` · `launch_runbook.md` | 방향·수익화·출시 절차 |
| `a11y_baseline.md` | 접근성 기준선(a11y-audit 스킬이 참조) |
| `tier1_hybrid_utilization_definition.md` | Tier1 소진율 정의 |
| `pl_breakdown_coverage.md` · `pl_selfcheck_matrix.md` · `csm_status_matrix.md` · `csm_coverage_goldmap.md` | 스크립트(`scripts/_pl_coverage_map.py`·`_pl_selfcheck.py`·`_csm_status_matrix.py`·`_csm_goldmap.py`)가 쓰는 현황표. 손으로 고치지 않는다 |
| `LESSONS_2026-06-07.md` · `archived_metrics.md` | 과거 교훈·폐기 지표 기록(`postmortems/` 와 `roadmap.md` 가 인용) |
| `og-image.src.html` | og:image 원본(`launch_runbook.md` 참조) |
| `business_assessment_20261018.md` · `loss_ratio_comparable_unit_20261019.md` | 기자 reach out 결과 평가(2026-10-18) · 손해율 가정 비교 최소 포트폴리오 단위 실측(2026-10-19). 일회성 분석 기록이다 |
