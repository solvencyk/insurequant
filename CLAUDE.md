# Insurequant Project Guidelines & Index

Automated data pipeline for Korean insurance financial metrics (K-ICS, IFRS17).
This file contains the core behavioral rules and the documentation index.

## 🗂️ 5-Stage Workflow Split (2026-05-31)

The pipeline is organized as **5 stages**, each owned by a subagent with its own master prompt, TODO, and changelog. **All history and instructions for a stage live in that stage's three files** — don't dump cross-stage content into one place.

| Stage | Prompt (instructions) | Active TODO | History |
|---|---|---|---|
| 1 — **downloader** | `docs/agents/claude-agent-downloader.md` (+ `docs/agents/source-catalog.yaml`) | `TODO_downloader.md` | `docs/changelog_downloader.md` |
| 2 — **parser** (2 lanes ∥) | `docs/agents/claude-agent-parser.md` (shared) + domain `docs/domains/claude-agent-{kics,ifrs17}.md` | `TODO_parser_kics.md` · `TODO_parser_ifrs17.md` | `docs/changelog_parser_{kics,ifrs17}.md` (pre-split frozen: `changelog_parser.md`) |
| 3 — **validation** | `docs/agents/claude-agent-validation.md` | `TODO_validation.md` | `docs/changelog_validation.md` |
| 4 — **publishing** (merged former gathering + pushing, 2026-05-31) | `docs/agents/claude-agent-publishing.md` (skeleton — reports + recommends, never executes `git push`) | `TODO_publishing.md` | `docs/changelog_publishing.md` |
| 5 — **designer** (HTML / CSS / responsive / chart layout, new 2026-05-31) | `docs/agents/claude-agent-designer.md` (skeleton) | `TODO_designer.md` | `docs/changelog_designer.md` |

**Stage 4 ↔ Stage 5 hard split:** publishing owns master JSONs (assembly + push recommendation). Designer owns HTML structure/styling. Master JSONs are read-only to designer; HTML files are off-limits to publishing (publishing reports `manual_html_edit` warn and stops). The two stages are otherwise independent (can run in parallel).

**Parser 2-lane split (2026-06-13):** parser runs as two parallel lanes — **kics** (`src/solvency/parser/`, Docling MD → `kics_disclosure.json`; market-risk subs; rate-sensitivity) and **ifrs17** (`src/ifrs17/`, DART XML → `CSM_waterfall` / `PL_breakdown` masters). Disjoint code/sources/outputs/validators → **run in separate sessions in parallel**. Each lane has its own `TODO_parser_<lane>.md` + `docs/changelog_parser_<lane>.md`, shares the stage prompt `claude-agent-parser.md` + its domain prompt `docs/domains/claude-agent-<lane>.md`. Shared inbox `inbox/parser/` with frontmatter `lane: kics|ifrs17`. **Join point:** `build_root_masters` runs once after both lanes have loaded.

Cross-stage items (large refactors, mobile/HTML work, multi-stage features) live in the **root** `TODO.md` and `docs/claude-changelog.md`.

Domain reference docs (K-ICS / IFRS17 / Misc IR) sit under `docs/domains/` and provide source-side context (label variants, table forms, company-specific quirks) — the stage agents consult them for domain knowledge. Architecture flow docs (download-flow, gemini-flow, json-build, validation-harness, overview) sit under `docs/flows/`.

## 🔄 Session Handoff (다음 세션을 위한 안내)

이 저장소는 여러 Claude/Cursor 세션이 이어서 작업합니다.

**새 세션 시작 시 읽는 순서 (2026-07-27 deferred loading — changelog는 매 세션 로드 X):**
1. 이 `CLAUDE.md` (정책 + 5-stage 인덱스)
2. 루트 `TODO.md` (cross-stage 현황)
3. 작업하려는 stage의 `TODO_<stage>.md` + `docs/agents/claude-agent-<stage>.md`
   - **parser는 레인별**: `TODO_parser_<lane>.md` + 공유 `claude-agent-parser.md` + `docs/domains/claude-agent-<lane>.md` (`<lane>` = `kics` 또는 `ifrs17`)

> **changelog는 읽는 순서에서 뺐다 (deferred, 2026-07-27).** `docs/claude-changelog.md`·`docs/changelog_<stage>.md`는 **이력 저장소** — 특정 과거 결정의 배경·근거가 필요할 때만 연다(대부분 세션은 안 열어도 됨). **현황은 TODO에**, 커밋레벨 상세는 **git log**(첫 push 2026-05-25 이후)에 있다. 이유: changelog가 매 세션 강제 로드되면 kics 세션 기준 ~1,900줄 중 868줄이 이력이라 컨텍스트 낭비(클로드 컨텍스트 엔지니어링 원칙: 필요시점 로드).

**갱신 규칙은 유지:** 변경·실행 후 **해당 stage TODO 맨 위 갱신 필수**, 그리고 완결 항목은 **해당 stage changelog에 계속 기록**(이력은 쌓되 읽기는 필요 시). cross-stage 변경이면 root `TODO.md` + `docs/claude-changelog.md` 갱신.

## K-ICS validation gate (mandatory)

Before proceeding to the next K-ICS pipeline stage (JSON swap, template sync, HTML deploy, push):

1. Run `python scripts/validate_kics_disclosure.py` on root `kics_disclosure.json`.
2. **RED count must be 0**, unless every remaining RED is a **documented exception** in `TODO.md` (company, quarter, rule id, reason).
3. Any unexpected RED requires **parsing-error review** (MD source, parser scope, row mapping) before continuing.
4. Rule `8_life` **SKIP** (missing items 29-35) does not block the gate; all other rules treat missing inputs as RED.

See `docs/agents/kics-json-validation-rules.md` for formulas, R4/R7 matrices, tolerance, and item-label mapping. The validation subagent ([`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md)) automates the loop (max 5 retries → parser callback → escalate to human).

## 🔧 2026-07-22 리팩토링 — 바뀐 계약 (모든 stage 확인 필수)

세션 시작 시 **자기 stage 행을 반드시 읽을 것.** 상세는 각 프롬프트/SKILL의 해당 절, 전체 이력은 `docs/claude-changelog.md` 2026-07-21~22 항목.

| stage | 알아야 할 변경 | 상세 |
|---|---|---|
| **공통** | `run_harness.py`는 `--stage` **필수**, 선택지 `quality\|pdf\|parse`. `--stage all/data/perf` 삭제(폐기된 `kics_data.json`을 루트에 재생성하던 함정). `src/solvency/{legacy,transform}` + `validation/{rules,schema}.py` 삭제 — 룰 엔진은 `kics_json_rules.py` 하나. | `docs/agents/claude-agent-parser.md` §1.1 |
| **downloader** | 회사별 legacy 다운로더 4종 삭제(단일 엔진만). `--stage pdf`는 그대로. IR 크롤러 등 미참조 스크립트 아카이브. | `claude-agent-downloader.md` "What NOT to Do" |
| **parser / kics** | MD 품질게이트가 `--stage quality`로 독립 + 임계값 버그 수정(488중 485 review → 306). `export_red_all_cases.py`가 UTF-16이라 실행 불가였는데 복구됨. | `claude-agent-parser.md` §1.1 |
| **parser / ifrs17** | **`build_pl_breakdown.py` 4,885줄 → `scripts/pl_breakdown/` 패키지.** 회사 핸들러를 어디에 추가하고 어떻게 등록하는지, 골든 게이트(`RUN_PL_GOLDEN=1`) 사용·재생성법. | `.claude/skills/ifrs17-parser/SKILL.md` "PL breakdown is a package now" |
| **validation** | 데이터계약 게이트가 **배포본이 아닌 죽은 사본**(2025.4Q templates)을 보고 있었음 → 루트 배포 아티팩트로 재조준. 신규 RED `ARTIFACT_UNREADABLE`(깨진 파일 ≠ 없는 파일). `templates/kics_disclosure.json` 삭제 — **동기화 중단**. | `claude-agent-validation.md` §5.2 |
| **publishing** | keep-list에 **루트 JSON 3개 추가**(`kics_{tier1,tier2}_utilization.json`·`kics_forward_capital.json`) — 빠지면 패널이 조용히 빈칸. `forward_capital_simulation.py`의 `--no-html` 소멸. `pytest tests/test_deploy_assets.py`가 keep-list를 기계 검사. | `claude-agent-publishing.md` §1 |
| **designer** | **데이터를 HTML에 인라인 금지**(K-ICS.html 147KB=70% 제거). 폴백 경로는 대소문자까지 실서버 확인(라이브 404 전례). | `claude-agent-designer.md` §4 |

**불변식 3개 (새로 명문화):**
1. **게이트가 검사하는 파일 = 사용자가 보는 파일.** 다르면 산수가 맞아도 소스가 틀린 통과가 된다.
2. **모든 `.py`는 BOM 없는 UTF-8.** UTF-16은 실행 자체가 불가하고, UTF-8 BOM은 실행은 되지만 `ast.parse`를 깨뜨려 **정적 검사 도구에서 그 파일이 투명인간**이 된다. `pytest tests/test_deploy_assets.py`가 강제.
3. **거대 게이트/빌더 함수는 골든 테스트로 고정돼 있다 — 고치면 반드시 돌려라.** 2026-07-22 리팩토링으로 네 개의 큰 함수가 분해됐고 각각 골든이 산출물을 고정한다. 산출이 **의도적으로** 바뀌면 손으로 해시 고치지 말고 `--update`로 재생성 + 커밋에 이유 기록.

| 골든 테스트 | 고정 대상 | 언제 |
|---|---|---|
| `tests/test_pl_breakdown_golden.py` (`RUN_PL_GOLDEN=1`, ~95초) | `build_pl_breakdown.py` 산출 마스터 바이트 | PL 빌더/핸들러 수정 후 |
| `tests/test_post_transition_golden.py` (오프라인, ~4초) | `_extract_post_values`의 6,114 적용후 셀 | `fill_post_transition_to_disclosure.py` 수정 후 |
| `tests/test_kics_rules_golden.py` (오프라인, <1초) | 룰 엔진 6,804 findings 매트릭스 | `kics_json_rules.py` 룰 수정 후 |
| `tests/test_master_tables_golden.py` (오프라인, <1초) | `validate_master_tables` SUMMARY + exit code | 그 게이트 수정 후 |
| `tests/test_viz_ifrs17_panels_golden.py` (오프라인, ~1.5초) | `viz_build_ifrs17_panels.py`가 쓰는 4개 패널 JSON 해시 | 그 빌더 수정 후 |
| `tests/test_viz_csm_waterfall_golden.py` (오프라인, ~1.5초) | `viz_build_csm_waterfall.py` 산출 + 47사 status | 그 빌더 수정 후 |
| `tests/test_deploy_assets.py` (오프라인) | keep-list·인라인금지·BOM·삭제경로 참조 | HTML fetch/삭제/인코딩 변경 후 |

> viz 골든 2종은 산출 JSON을 **인플레이스로 덮어쓰는** 빌더라, 실행 전 백업하고 drift/예외 시 복구한다(마스터 반쯤 쓰임 방지). 산출이 의도적으로 바뀌면 `--update`로 재생성 + 커밋에 이유 기록.

## 🈲 문서·TODO 인코딩 룰 (필수)

**TODO.md, docs/*.md, README 등 모든 문서 파일은 반드시 UTF-8 (BOM 없음)으로 저장한다.**

- 한글이 깨질 환경(PowerShell `Out-File` 기본 UTF-16, Write 도구 일부 환경 등)에서는 **영어로 작성**한다.
- **절대 중국어/일본어/유사 문자로 보이는 깨진 출력을 그대로 두지 말 것.** (실제로는 UTF-16 LE BOM 누락으로 글자 사이 null byte가 들어가 한글이 중국어처럼 보이는 케이스가 빈번.)
- 신규/덮어쓰기 시 반드시: Python `Path.write_text(content, encoding='utf-8')`, PowerShell `[System.IO.File]::WriteAllText(path, content, [System.Text.UTF8Encoding]::new($false))`, 또는 `Set-Content -Encoding utf8` 사용.
- 작성 후 첫 줄을 즉시 read-back으로 확인. 깨졌으면 영어로 재작성.
- 이 룰은 사용자가 2026-05-24 세션에서 명시적으로 약속을 요구함.

## 📬 스테이지 간 handoff = inbox (사람 복붙 대체)

스테이지(다운로더↔파서↔검증)가 서로 검증·재작업을 요청할 때는 **`inbox/` 폴더에 md 메시지를 떨궈** 비동기로 주고받는다 (사람이 세션 간 복붙하지 않음). 계약 정본: [`inbox/README.md`](inbox/README.md). 각 스테이지 프롬프트 "Inbox handoff protocol" 섹션 참조.

- filesystem-mediated **evaluator-optimizer** (실시간 agent-team 아님). inbox=메시지, **dynamic Workflow=드라이버**.
- 에이전트는 inbox를 자동 감시하지 않음 — 드라이버(Workflow/사람)가 호출 시 첫 동작으로 자기 inbox를 드레인. 루프 bounded max 5회, 초과 → escalate(사람 큐).

## 🧵 멀티에이전트 병렬처리 규칙 (필수)

작업 영역이 서로 독립이면 **반드시 별도 서브에이전트(Agent tool)를 띄워 병렬로 처리한다.** 단일 세션에서 순차로 처리하지 말 것.

**병렬 축 — stage는 파이프라인, 병렬은 그 안/사이에서:**

> ⚠️ 5-stage(downloader→parser→validation→publishing→designer)는 **순차 파이프라인**이다. 같은 데이터에 stage들을 동시에 못 돌린다(파싱 전 검증 불가). **"stage별로 병렬"은 틀린 프레임** — 병렬은 아래 두 축으로만:

1. **Stage 내부 fan-out (주력)**: 한 stage 안에서 **(회사 × 분기 × 도메인/데이터소스)** 단위로 독립이면 그 단위로 서브에이전트 fan out. 예: 회사별 PDF 파싱, 회사-분기별 추출 진단(2026-06-09 continuity 11건 = 11 에이전트 병렬), 도메인(K-ICS/IFRS17/Misc)별 작업. 각 에이전트에 해당 `docs/agents/claude-agent-<stage>.md`(+ `TODO_<stage>.md`·`docs/changelog_<stage>.md`), 도메인 작업이면 `docs/domains/claude-agent-<domain>.md` + 관련 `docs/flows/*.md`를 컨텍스트로 명시.
2. **Item별 파이프라인 중첩**: 서로 다른 (회사,분기) item을 각자 download→parse→validate로 **독립적으로 흘린다** (item A가 validate 중일 때 item B는 parse 중 — barrier 없음). "stage들을 병렬화"하려면 이 방식 = dynamic Workflow의 `pipeline()` 프리미티브.

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
