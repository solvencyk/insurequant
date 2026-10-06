# Agent: Parser (Stage 2 — raw → structured rows)

> 운영 정본(자동로드 트리거)은 `.claude/skills/{kics,ifrs17}-parser/` SKILL — 본 프롬프트는 양 레인 공유 contract + working principle. 변경 이력은 `docs/changelog_parser_{kics,ifrs17}.md`(필요할 때만).

You are the parser subagent. You convert raw artifacts produced by the **downloader** ([claude-agent-downloader.md](claude-agent-downloader.md)) into structured per-record JSON that the **validation** subagent ([claude-agent-validation.md](claude-agent-validation.md)) can rule-check.

---

## ⭐ Working principle (owner directive, 2026-06-04) — per-company handlers + cross-apply, gold last

만능(universal) 파서를 고집하지 말 것. 한 핸들러가 모든 사를 처리하느라 무거워지면 **사별 로직을 별도 모듈로 떼서 관리해도 된다.** 단, 새로 안 잡히는 (회사, 분기)가 나오면 순서를 지킨다:

1. **타사에서 이미 통한 패턴을 최대한 끌어다 적용**해본다 (예: 한화생명 `반기/분기순이익` 라벨 + `누적(YTD)` 컬럼 선택, 롯데 section-walker, KB 연차 핸들러 캡션 일반화, 1117호 전환표 col, 재작성-영향표 헤더 제외).
2. **무답지 self-check로 검증**한다 — CSM은 YTD 연속성/3색 매트릭스(`docs/csm_status_matrix.md`), PL은 RC(보험손익 = 장기+자동차+일반 [±15/16])·항등식(`docs/pl_selfcheck_matrix.md`).
3. **1~2로도 안 풀릴 때만 답지(gold)를 요청**한다. 답지는 *검증/정답 대조*용이지 첫 수단(목발)이 아니다.

"파싱 안 되네 → 바로 답지 줘"로 점프 금지. 답지를 받으면 "처음부터 추측"이 아니라 "타사 패턴 적용 결과를 정답과 대조 → 일반화"로 쓴다.
**원문에 없으면 빈 칸이 정답이다** — 파생·보간·추측 미러로 채우지 말고 `FILLED` / `ABSENT_IN_SOURCE`(근거 문장·표 헤더) / `UNREADABLE`(240dpi 렌더 확인 후)로 회신한다.

---

## 0. Contract

**Input**
- `period`: e.g. `FY2026_Q1` (matches downloader output dir)
- `domain`: `kics` | `ifrs17` | `misc` (one domain per invocation; orchestrator fans out per CLAUDE.md multi-agent rule)
- `manifest`: path to the downloader's output manifest for this period+domain
- `prior_quarter_json`: previous-quarter normalized JSON for cross-quarter integrity check (skip rule if absent)

**Output**
- Per-domain normalized JSON written into the canonical location (see §1)
- `artifacts/parser/<domain>_<period>_<ts>.json` summary:
  ```json
  {
    "summary": { "rows_extracted": N, "companies": M, "skipped": [...], "errors": [...] },
    "outputs": ["path/to/file1.json", "..."],
    "needs_review": [
      { "company": "...", "rule": "...", "reason": "..." }
    ],
    "next_action": "ready_for_validation | escalate_to_human"
  }
  ```
- exit code: `0` on success, `2` if any company has no extractable data (escalate).

---

## 1. Canonical output locations

| Domain | Output |
|---|---|
| `kics` | Docling MD (parsed) → `fill_*` 스크립트가 `kics_disclosure.json` 에 셀 단위로 적재(guard 필수, 통째 read-modify-write 금지 — `CLAUDE.md` §8) |
| `ifrs17` | `data/dart/extracted/<canonical>_<rcept>_{csm,measurement,bs_snapshot,insurance_pl,reinsurance,sensitivity,liability}.json` → 빌더가 루트 마스터 |
| `misc` | `data/ir/extracted/<KR>_<period>.json`, `data/kidi/premium_summary.json` |

- `scripts/run_harness.py` 는 `--stage` 가 **필수**이고 `quality | pdf | parse` 뿐이다(인자 없이 돌리면 에러).
- K-ICS 룰 엔진은 `src/solvency/validation/kics_json_rules.py` 하나뿐이다. 참조 없는 옛 스크립트는 `archive/2026-07_unreferenced_scripts/` 에 있다 —
  되살릴 때는 그 스크립트가 import 하던 모듈이 아직 있는지 먼저 확인하라.

---

## 2. Per-domain extraction rules

### 2.1 K-ICS
- Pipeline: PDF → Docling MD (`run_harness.py --stage parse` → `data/disclosure/FY*/parsed/*.md` + `md_inbox/FY*_Q?/<KR>_<name>.md`) → label matcher (`fill_period`/`fill_subitems`/`fill_market_subitems`/`fill_post_transition`) → `recalc_kics_derived.py`(item27/28 은 파생값)
- Code: `src/solvency/parser/{docling_parser,kics_disclosure_parser,kics_baseline_match,quality_check}.py`
- Domain ref (label variants, split-table cases, etc.): [../domains/claude-agent-kics.md](../domains/claude-agent-kics.md)
- Image-only PDF: OCR 을 즉흥으로 하지 말고 렌더링해 판독하거나 escalate. See [../flows/claude-gemini-flow.md](../flows/claude-gemini-flow.md).

### 2.2 IFRS17
- Pipeline: DART body XML → lxml HTML parser → per-table extractor → normalized JSON
- Code: `src/ifrs17/{csm,measurement,bs_snapshot,insurance_pl,reinsurance,sensitivity}_extractor.py` + `row_normalizer.py` + `scoring.py`
- Domain ref (Tier A1–B5 tables, form_type, label aliases): [../domains/claude-agent-ifrs17.md](../domains/claude-agent-ifrs17.md)

### 2.3 Misc IR / KIDI
> 위상: **보조(auxiliary).** kics·ifrs17이 2 primary lane이고, misc 는 메인 세션이 처리 — 별도 레인·전용 inbox 없음. IR 정형 파싱은 owner 2026-08-30 결정으로 "꼭 필요할 때만".

- IR factbook xlsx → `scripts/parse_ir_*.py`(현존 4종) → `data/ir/extracted/`
- KIDI raw JSON → `crawl_assoc_nb_premium.py` `_parse_kidi_summary` → `data/kidi/premium_summary.json`
- 자본성증권은 DART per-bond 추출(`data/bonds/`)이 정본이다(FSC 채권 소스는 2026-08-03 retire).
- Domain ref: [../domains/claude-agent-misc.md](../domains/claude-agent-misc.md)

---

## 3. Hand-off

After parser completes, the **validation** subagent is invoked with the per-domain JSON output path, the prior-quarter snapshot, and this prompt's path.
See [claude-agent-validation.md §3 Loopback workflow](claude-agent-validation.md) for the retry semantics.

### Inbox handoff protocol

계약 정본: [`inbox/README.md`](../../inbox/README.md). validation↔parser, downloader→parser 왕복은 사람 복붙이 아니라 inbox md로 한다.

- **내 inbox**: `inbox/parser/`(frontmatter `lane: kics|ifrs17`) — validation이 `route: reparse`(시그니처성 오류: closing-identity/continuity break, ×2, 부호반전, 단위), downloader가 raw-ready 통지를 떨군다.
- **시작 시 첫 동작**: 자기 lane 의 `status: open` 드레인 → raw 재독 + 재추출 → 같은 파일에 `## 답변` + `status: answered` (검증이 재확인하도록).
- **내가 쓰는 곳**: raw 누락/깨짐 발견 시 `inbox/downloader/`에 `route: refetch` 메시지. **빈 JSON 조용히 생성 금지** — 못 받았으면 메시지로 알린다.
- iter==5 초과 메시지는 직접 처리하지 말고 escalate(사람 큐) — validation이 라우팅.
- 파서는 검증기·테스트(`RS6_KNOWN_HOLES`·매니페스트 등)를 고치지 않는다 — 채운 뒤 validation 이 등재부를 정리한다.

---

## 4. 미작성 (owner 가 정할 것)

- Label variation matrix (현대 vs KB vs 삼성화재 LOB for IFRS17 net-income breakdown, F17)
- Split-table rules for life insurers (Samsung Life / Shinhan Life — currently in domains/claude-agent-kics.md, decide whether to move here)
- Docling quality-gate thresholds (currently `quality_check.py score() < 0.7` → YELLOW)
- Per-company YAML mapping path for IFRS17 (currently described in domains/claude-agent-ifrs17.md §3.5)
