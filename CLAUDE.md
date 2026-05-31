# Insurequant Project Guidelines & Index

Automated data pipeline for Korean insurance financial metrics (K-ICS, IFRS17).
This file contains the core behavioral rules and the documentation index.

## 🗂️ 5-Stage Workflow Split (2026-05-31)

The pipeline is organized as **5 stages**, each owned by a subagent with its own master prompt, TODO, and changelog. **All history and instructions for a stage live in that stage's three files** — don't dump cross-stage content into one place.

| Stage | Prompt (instructions) | Active TODO | History |
|---|---|---|---|
| 1 — **downloader** | `docs/agents/claude-agent-downloader.md` (+ `docs/agents/source-catalog.yaml`) | `TODO_downloader.md` | `docs/changelog_downloader.md` |
| 2 — **parser** | `docs/agents/claude-agent-parser.md` (skeleton) | `TODO_parser.md` | `docs/changelog_parser.md` |
| 3 — **validation** | `docs/agents/claude-agent-validation.md` | `TODO_validation.md` | `docs/changelog_validation.md` |
| 4 — **publishing** (merged former gathering + pushing, 2026-05-31) | `docs/agents/claude-agent-publishing.md` (skeleton — reports + recommends, never executes `git push`) | `TODO_publishing.md` | `docs/changelog_publishing.md` |
| 5 — **designer** (HTML / CSS / responsive / chart layout, new 2026-05-31) | `docs/agents/claude-agent-designer.md` (skeleton) | `TODO_designer.md` | `docs/changelog_designer.md` |

**Stage 4 ↔ Stage 5 hard split:** publishing owns master JSONs (assembly + push recommendation). Designer owns HTML structure/styling. Master JSONs are read-only to designer; HTML files are off-limits to publishing (publishing reports `manual_html_edit` warn and stops). The two stages are otherwise independent (can run in parallel).

Cross-stage items (large refactors, mobile/HTML work, multi-stage features) live in the **root** `TODO.md` and `docs/claude-changelog.md`.

Domain reference docs (K-ICS / IFRS17 / Misc IR) sit under `docs/domains/` and provide source-side context (label variants, table forms, company-specific quirks) — the stage agents consult them for domain knowledge. Architecture flow docs (download-flow, gemini-flow, json-build, validation-harness, overview) sit under `docs/flows/`.

## 🔄 Session Handoff (다음 세션을 위한 안내)

이 저장소는 여러 Claude/Cursor 세션이 이어서 작업합니다.

**새 세션 시작 시 읽는 순서:**
1. 이 `CLAUDE.md` (정책 + 5-stage 인덱스)
2. 루트 `TODO.md` (cross-stage 현황) + `docs/claude-changelog.md` (cross-stage 이력)
3. 작업하려는 stage의 `TODO_<stage>.md` + `docs/changelog_<stage>.md` + `docs/agents/claude-agent-<stage>.md`

변경·실행이 있을 때마다 **해당 stage**의 TODO/changelog 맨 위를 갱신. cross-stage 변경이면 root 두 파일 갱신.

## K-ICS validation gate (mandatory)

Before proceeding to the next K-ICS pipeline stage (JSON swap, template sync, HTML deploy, push):

1. Run `python scripts/validate_kics_disclosure.py` on root `kics_disclosure.json`.
2. **RED count must be 0**, unless every remaining RED is a **documented exception** in `TODO.md` (company, quarter, rule id, reason).
3. Any unexpected RED requires **parsing-error review** (MD source, parser scope, row mapping) before continuing.
4. Rule `8_life` **SKIP** (missing items 29-35) does not block the gate; all other rules treat missing inputs as RED.

See `docs/agents/kics-json-validation-rules.md` for formulas, R4/R7 matrices, tolerance, and item-label mapping. The validation subagent ([`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md)) automates the loop (max 5 retries → parser callback → escalate to human).

## 🈲 문서·TODO 인코딩 룰 (필수)

**TODO.md, docs/*.md, README 등 모든 문서 파일은 반드시 UTF-8 (BOM 없음)으로 저장한다.**

- 한글이 깨질 환경(PowerShell `Out-File` 기본 UTF-16, Write 도구 일부 환경 등)에서는 **영어로 작성**한다.
- **절대 중국어/일본어/유사 문자로 보이는 깨진 출력을 그대로 두지 말 것.** (실제로는 UTF-16 LE BOM 누락으로 글자 사이 null byte가 들어가 한글이 중국어처럼 보이는 케이스가 빈번.)
- 신규/덮어쓰기 시 반드시: Python `Path.write_text(content, encoding='utf-8')`, PowerShell `[System.IO.File]::WriteAllText(path, content, [System.Text.UTF8Encoding]::new($false))`, 또는 `Set-Content -Encoding utf8` 사용.
- 작성 후 첫 줄을 즉시 read-back으로 확인. 깨졌으면 영어로 재작성.
- 이 룰은 사용자가 2026-05-24 세션에서 명시적으로 약속을 요구함.

## 🧵 멀티에이전트 병렬처리 규칙 (필수)

작업 영역이 서로 독립이면 **반드시 별도 서브에이전트(Agent tool)를 띄워 병렬로 처리한다.** 단일 세션에서 순차로 처리하지 말 것.

**병렬 단위 — 둘 다 유효:**

1. **Stage 단위** (5-stage workflow): downloader → parser → validation → gathering → pushing이 명확하게 분리된 작업이면 stage별로 fan out. 각 에이전트에 해당 `docs/agents/claude-agent-<stage>.md` + 해당 `TODO_<stage>.md` + `docs/changelog_<stage>.md` 경로를 컨텍스트로 명시.
2. **Domain 단위** (K-ICS / IFRS17 / Misc IR): 한 stage 안에서 여러 도메인에 걸친 작업이면 도메인별로 fan out. 각 에이전트에 해당 `docs/domains/claude-agent-<domain>.md` + 관련 `docs/flows/*.md` 경로를 컨텍스트로 명시.

**공통:**

- 한 메시지 안에서 `Agent` 호출을 작업 수만큼 병렬로 발사 (`subagent_type=general-purpose` 또는 `Explore`).
- 모든 에이전트에 본 `CLAUDE.md`도 컨텍스트로 명시.
- 메인 세션은 오케스트레이션(계획 조율, 결과 통합, changelog 갱신, 검증·푸시 게이트)만 담당. 도메인 코드/MD/JSON 직접 수정은 서브에이전트가 한다.
- 한 도메인 안에서도 명백히 병렬 가능한 단계(예: 회사별 PDF 파싱)는 서브에이전트가 자체 판단으로 병렬화.

## 🚧 Stage prompt 작성 진행도

- [x] Downloader prompt (`docs/agents/claude-agent-downloader.md`) — owner-authored, complete
- [x] Validation prompt (`docs/agents/claude-agent-validation.md`) — complete
- [ ] Parser prompt — skeleton; TBD label variation matrix, split-table rules, Docling quality-gate thresholds, per-company YAML mapping path
- [ ] Publishing prompt — skeleton; TBD idempotency contract, schema versioning, derived metrics DAG, viz JSON contract, branch policy, site-deploy hook, rollback procedure
- [ ] Designer prompt — skeleton; TBD design system, common.css extraction, A11y baseline, chart legend density, donut stack breakpoint, mobile pass scope

The 3 incomplete stages still have a usable skeleton (Contract section: input/output/exit codes) so they can be invoked even before the TBD body is filled in.

---
