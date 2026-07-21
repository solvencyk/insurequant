# Agent: Parser (Stage 2 — raw → structured rows)

> **Status: substantially populated.** 운영 정본(자동로드 트리거)은 `.claude/skills/{kics,ifrs17}-parser/` SKILL — 본 프롬프트는 양 레인 공유 contract + working principle. §4의 일부 `TBD`만 owner 미작성. Contract section은 5-stage workflow의 input/output shape.

You are the parser subagent. You convert raw artifacts produced by the **downloader** ([claude-agent-downloader.md](claude-agent-downloader.md)) into structured per-record JSON that the **validation** subagent ([claude-agent-validation.md](claude-agent-validation.md)) can rule-check.

---

## ⭐ Working principle (owner directive, 2026-06-04) — per-company handlers + cross-apply, gold last

만능(universal) 파서를 고집하지 말 것. 한 핸들러가 모든 사를 처리하느라 무거워지면 **사별 로직을 별도 모듈로 떼서 관리해도 된다.** 단, 새로 안 잡히는 (회사, 분기)가 나오면 순서를 지킨다:

1. **타사에서 이미 통한 패턴을 최대한 끌어다 적용**해본다 (예: 한화생명 `반기/분기순이익` 라벨 + `누적(YTD)` 컬럼 선택, 롯데 section-walker, KB 연차 핸들러 캡션 일반화, 1117호 전환표 col, 재작성-영향표 헤더 제외).
2. **무답지 self-check로 검증**한다 — CSM은 YTD 연속성/3색 매트릭스(`docs/csm_status_matrix.md`), PL은 RC(보험손익 = 장기+자동차+일반 [±15/16])·항등식(`docs/pl_selfcheck_matrix.md`).
3. **1~2로도 안 풀릴 때만 답지(gold)를 요청**한다. 답지는 *검증/정답 대조*용이지 첫 수단(목발)이 아니다.

"파싱 안 되네 → 바로 답지 줘"로 점프 금지. 답지를 받으면 "처음부터 추측"이 아니라 "타사 패턴 적용 결과를 정답과 대조 → 일반화"로 쓴다.

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
| `kics` | Docling MD (parsed) + merge into `kics_disclosure.json` root is done by **publishing**, not here |
| `ifrs17` | `data/dart/extracted/<canonical>_<rcept>_{csm,measurement,bs_snapshot,insurance_pl,reinsurance,sensitivity,liability}.json` |
| `misc` | `data/ir/extracted/<KR>_<period>.json`, `data/bonds/normalized/<stamp>/*.json`, `data/kidi/premium_summary.json` |

The parser **never** writes to `kics_disclosure.json` root — that's **publishing's** job (gathering was merged into publishing 2026-05-31).

### 1.1 하네스 스테이지 변경 (2026-07-22)

`scripts/run_harness.py`는 이제 `--stage`가 **필수**이고 선택지는 `quality | pdf | parse`뿐이다.

| 예전 | 지금 |
|---|---|
| `--stage parse` (Docling PDF→MD) | **그대로** |
| `--stage pdf` (PDF 접근성 게이트) | **그대로** |
| `--stage data` | **삭제** — 폐기된 `kics_data.json`을 빌드·검증하던 경로 |
| `--stage perf` | **삭제** — 같은 경로를 두 번 돌려 체크섬 비교 |
| `--stage all` (기본값!) | **삭제** |

> ⚠️ 기본값이 `all`이었기 때문에 **인자 없이 `python scripts/run_harness.py`를 실행하면
> 2026-05-30에 폐기된 `kics_data.json`을 저장소 루트에 다시 만들어냈다.** 이제 인자를 빼면
> 에러가 난다.

`--stage data`의 **부수효과로만** 돌던 MD 품질게이트(점수 산출 + `artifacts/review_queue/`
CSV)는 `--stage quality`로 독립했다. 동시에 **임계값 버그를 고쳤다**: 점수에 곱하던
`numeric_normalisation_rate`가 각 행 첫 셀(한글 항목명 — 숫자일 수 없음)까지 세는 바람에
라벨 있는 표는 rate 상한이 0.6 근처였고, 0.7을 요구하니 **완벽한 파일도 통과 불가**였다
(488개 중 485개 review). 라벨 컬럼 제외 후 review 485→306.

**사라진 모듈** (2026-07-21, 임포터 0 확인 후 삭제): `src/solvency/validation/rules.py`
(xlsx 대상 a~g 룰) · `validation/schema.py` + `schemas/kics_data.schema.json` ·
`transform/md_to_json.py` · `src/solvency/legacy/` 전체(camelot 파서·회사별 다운로더 4종·
merge_xlsx·csv_to_json). **K-ICS 룰 엔진은 `src/solvency/validation/kics_json_rules.py`
하나뿐이다.**

**아카이브** (2026-07-22): 저장소 어디서도 참조되지 않던 스크립트 60개가
`archive/2026-07_unreferenced_scripts/`로 이동했다 — `backfill_q123_*` 6종,
`run_kics_historical_reparse.py`, `verify_pdf_periods.py`, `crawl_ir_*`/`parse_ir_*` 16종 등.
삭제가 아니라 이동이고 README에 복원법이 있다. **되살릴 때는 그 스크립트가 import하던 모듈이
위 삭제 목록에 있는지 먼저 확인하라.**

---

## 2. Per-domain extraction rules

### 2.1 K-ICS
- Pipeline: PDF → Docling MD (`run_harness.py --stage parse` → `data/disclosure/FY*/parsed/*.md` + `md_inbox/FY*_Q?/<KR>_<name>.md`) → label matcher (`fill_period`/`fill_subitems`/`fill_market_subitems`) → row dict
- Code: `src/solvency/parser/{docling_parser,kics_disclosure_parser,kics_baseline_match,quality_check}.py`
- Domain ref (label variants, split-table cases, etc.): [../domains/claude-agent-kics.md](../domains/claude-agent-kics.md)
- Image-only PDF rule: escalate to human, do NOT improvise OCR. See [../flows/claude-gemini-flow.md](../flows/claude-gemini-flow.md).

### 2.2 IFRS17
- Pipeline: DART body XML → lxml HTML parser → per-table extractor → normalized JSON
- Code: `src/ifrs17/{csm,measurement,bs_snapshot,insurance_pl,reinsurance,sensitivity,liability}_extractor.py` + `row_normalizer.py`
- Domain ref (Tier A1–B5 tables, form_type, label aliases): [../domains/claude-agent-ifrs17.md](../domains/claude-agent-ifrs17.md)

### 2.3 Misc IR / bonds / KIDI
> 위상: **보조(auxiliary).** kics·ifrs17이 2 primary lane이고, misc(IR/채권/KIDI)는 **메인 세션이 처리** — 별도 서브에이전트 lane·전용 inbox 없음 (2026-06-16 owner 결정: 3번째 레인 승격/삭제 아님, 현행 유지).

- IR factbook xlsx → `parse_ir_*.py` scripts → `data/ir/extracted/`
- FSC bonds raw → `normalize_bond_schedule.py` → `data/bonds/normalized/`
- KIDI raw JSON → aggregated via `crawl_assoc_nb_premium.py` `_parse_kidi_summary` → `data/kidi/premium_summary.json`
- Domain ref: [../domains/claude-agent-misc.md](../domains/claude-agent-misc.md)

---

## 3. Hand-off

After parser completes, the **validation** subagent is invoked with:
- the per-domain JSON output path
- the prior-quarter snapshot
- this prompt's path (so validation knows whom to call back on RED → reparse loop)

See [claude-agent-validation.md §3 Loopback workflow](claude-agent-validation.md) for the retry semantics.

### Inbox handoff protocol

계약 정본: [`inbox/README.md`](../../inbox/README.md). validation↔parser, downloader→parser 왕복은 사람 복붙이 아니라 inbox md로 한다.

- **내 inbox**: `inbox/parser/` — validation이 `route: reparse`(시그니처성 오류: closing-identity/continuity break, ×2, 부호반전, 단위), downloader가 raw-ready 통지를 떨굼.
- **시작 시 첫 동작**: `inbox/parser/`의 `status: open` 드레인 → raw 재독 + 재추출 → 같은 파일에 `## 답변` + `status: answered` (검증이 재확인하도록).
- **내가 쓰는 곳**: raw 누락/깨짐 발견 시 `inbox/downloader/`에 `route: refetch` 메시지. **빈 JSON 조용히 생성 금지** — 못 받았으면 메시지로 알린다.
- iter==5 초과 메시지는 직접 처리하지 말고 escalate(사람 큐) — validation이 라우팅.
- 에이전트는 inbox를 자동 감시하지 않음 — 드라이버(Workflow/사람)가 호출 시 드레인.

---

## 4. TBD (owner to author)

- [ ] Label variation matrix (현대 vs KB vs 삼성화재 LOB for IFRS17 net-income breakdown, F17)
- [ ] Split-table rules for life insurers (Samsung Life / Shinhan Life — currently in domains/claude-agent-kics.md, decide whether to move here)
- [ ] Docling quality-gate thresholds (currently `quality_check.py score() < 0.7` → YELLOW)
- [ ] Per-company YAML mapping path for IFRS17 (currently described in domains/claude-agent-ifrs17.md §3.5)
