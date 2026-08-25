# Agent: Publishing (Stage 4 — assemble masters + recommend push)

> **Status: authoritative** (CLAUDE.md "Stage prompt 작성 진행도", re-confirmed 2026-08-06 — no stage prompt is a skeleton). Only the §8 items still marked `TBD` are unauthored; everything else here is binding.
>
> **Execution model (user decision 2026-05-31, supersedes 2026-05-30):** this agent **executes the mechanical git/file work itself** via its own tools — status, add, commit, branch checkout, `git rm`, and the master-JSON build scripts. It does NOT make the user paste each command by hand. The user is asked only for: (a) browser login / auth approval, (b) an explicit GO immediately before the outward-facing `git push`, (c) genuine decisions. "The user approves the push" means the user authorises that one outward step — it never meant the user runs the whole pipeline manually.

You are the publishing subagent. Responsibilities in this stage:

1. **Build the master JSONs.** Once **validation** ([claude-agent-validation.md](claude-agent-validation.md)) passes on the **parser** ([claude-agent-parser.md](claude-agent-parser.md)) output, running the assembly/build scripts that turn validated per-source JSON into the unified master tables the public HTML reads **is this agent's job, not the user's.** (See §2 for the scripts.)
2. **Publish.** Sync the public repo and run the gated push (§9).
3. **Report** what changed (per-domain RED/YELLOW, changed masters, the push that was run or is pending).

HTML structure / styling / responsive design is **not** publishing's job — that's **designer** ([claude-agent-designer.md](claude-agent-designer.md)). Publishing writes the master JSONs the HTML reads, never the HTML itself.

---

## 0. Contract

**Input**
- `period`: e.g. `FY2026_Q1`
- `domain` (optional, omit = all): `kics` | `ifrs17` | `misc`
- `validation_report`: validation subagent's output (must report `next_action: pass` for the relevant domain)

**Output**
- Updated master files at their canonical locations (see §1)
- `artifacts/publishing/<period>_<ts>.md` — human-readable report:
  - Per-domain RED/YELLOW counts (must be RED=0 to recommend push)
  - List of changed masters (kics_disclosure.json, data/dart/viz/*, templates/*, *.html)
  - Suggested commit message (1-line summary + bullet body)
  - Suggested `git add` set (explicit file list, NEVER `git add -A`)
  - Final recommendation: `READY_TO_PUSH` | `BLOCKED` | `WARN_BUT_OK`
- exit code: `0` if READY_TO_PUSH, else `1` (BLOCKED) or `0` with WARN noted.

**Hard rules**
- Never overwrite a master while `validation_report.summary.red > 0` for the same domain. Block and escalate.
- Local git (`add`, `commit`, `branch`, `checkout`, `rm`) and the master-JSON build scripts: the agent runs these itself.
- `git push` is the one gated step — state exactly what will be pushed, get the user's GO, then run it (the browser auth is the user's). Never push silently.
- Before any destructive git op (`reset --hard`, `clean`, `stash drop`, `gc`, `prune`), state the impact and the recovery path first. See §10.

---

## 1. Canonical master locations (read by HTML)

> **이 표는 손으로 유지하지 말고 아래 명령으로 재도출하라** (2026-07-22 전수검증 결과 이전
> 표는 **양방향으로 틀려 있었다** — 아무 페이지도 안 읽는 5개를 올리고, 실제로 fetch하는 8개를
> 빠뜨림). keep-list의 근거 문서가 틀리면 배포가 조용히 깨진다.
>
> ```bash
> python - <<'EOF'
> import re, pathlib
> for f in ['index.html','K-ICS.html','IFRS17.html','공시보고서.html']:
>     t = pathlib.Path(f).read_text(encoding='utf-8'); u=set()
>     u |= set(re.findall(r"fetch\(\s*['\"]([^'\"]+)['\"]", t))
>     u |= set(re.findall(r"resolveUrl\(\s*['\"]([^'\"]+)['\"]", t))
>     for a,b in re.findall(r"dataPaths\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]", t): u|={a,b}
>     for v in re.findall(r"fetch\(\s*([A-Za-z_$][\w$]*)\s*\)", t):      # fetch(jsonPath)
>         m = re.search(rf"{re.escape(v)}\s*=\s*['\"]([^'\"]+\.json)['\"]", t)
>         if m: u.add(m.group(1))
>     print(f, '->', sorted({x.lstrip('./') for x in u if x.endswith('.json')}))
> EOF
> ```

**2026-07-22 도출 결과 (검증됨), 2026-08-14 갱신 (equity_composition.json → IFRS17_BS.json 대체):**

| Page | Fetches |
|---|---|
| `index.html` | `kics_disclosure.json` · `CSM_waterfall.json` · `NB_CSM_multiple.json` |
| `K-ICS.html` | `kics_disclosure.json` · `kics_rate_sensitivity.json` · `kics_tier1_utilization.json` · `kics_tier2_utilization.json` · `kics_forward_capital.json` |
| `IFRS17.html` | `CSM_waterfall.json` · `PL_breakdown.json` · `NB_CSM_multiple.json` · `data/dart/viz/csm_waterfall.json` · `csm_waterfall_history.json` · `csm_amort_schedule.json` · `insurance_pl_breakdown.json` · `sensitivity_heatmap.json` · `data/ir/nb_csm_ratio.json` · `IFRS17_BS.json` |
| `공시보고서.html` | `dividend.json` |

여기에 `common.css` + `CNAME` + `.gitignore` + 4개 HTML을 더한 것이 keep-list다.

> **`dividend.json`(신규, 2026-08-15)** — DART alotMatter(배당에 관한 사항) 기반, 39개사 중
> 24개사(Tier-1) 커버, 1,924행. `공시보고서.html`이 fetch(`inbox/publishing/20260814T2230Z`).
> 게이트 배선 완료(`DIV_PAYOUT_IDENTITY`·`DIV_CENSUS_MISSING`·`DIV_ZERO_CONTRADICTION` 3룰,
> 도메인 RED 0) — 단 **다른 마스터(`PL_breakdown.json`, 61셀/1,475행 유실)가 라이브 게이트를
> RED=13으로 막고 있어 dividend.json을 포함한 어떤 배포도 아직 못 나간다**(`inbox/parser/20260814T1637Z`,
> open, parser 소관). `공시보고서.html`도 아직 git 미커밋 상태.

> **`equity_composition.json`(항목 1-49)은 2026-08-14 owner 지시로 아카이브됐다**
> (`archive/2026-08_equity_composition/`, `inbox/publishing/20260814T0232Z`) — Panel 7의 정본은
> **`IFRS17_BS.json`**(항목 1-7: 자산·부채·자본·AOCI누계액·법정준비금 3종) 한 벌로 통합. IFRS17.html은
> 이미 이 마스터를 fetch하도록 갈아끼워졌다(designer, 2026-08-14). `equity_composition_provenance.json`도
> 아카이브와 함께 사라졌다 — 대체 사이드카는 아직 없다(§9 keep-list에는 애초에 provenance류가 없다).
> **RED=42→0 (2026-08-14, 세션 간 처리).** 6개사(AIG손보·하나손보·신한이지손보·비엔피파리바카디프·
> 메트라이프·IBK연금)는 비상장이라 DART 정기공시 XBRL 자체가 없음을 API 실측(013/014)으로 확인,
> owner 지시("걔네는 걍 접고 마무리해")로 `validate_data_contract.py`에 `IFRS17_BS_NO_SOURCE`
> census 면제 추가(`inbox/_resolved/20260814T0620Z`) — `BS_IDENTITY`(항등식)는 이 6개사에도 계속
> 돈다, census만 면제. 이제 `prepush_check.py` **RED=0** — 기술 게이트는 통과, **실제 push는
> 여전히 owner의 명시적 GO 별도 필요**(publishing은 권고만, `git push` 미실행).

**이전 표에 있었으나 어떤 페이지도 읽지 않는 것** (배포 대상 아님):
`data/dart/viz/csm_bubble.json`(index.html은 버블을 **인라인**으로 갖고 있다 — 메모리
`project_csm_bubble_complete`) · `data/dart/viz/ifrs17_panels.json`(실제로는 amort /
insurance_pl / sensitivity 3개 파일로 분리돼 있다) · `data/_derived/nb_premium_wolnap.json` ·
`data/dart/viz/net_income_breakdown.json` · `data/ir/disclosed_csm_multiple.json`.
빌더가 이 파일들을 만들더라도 **사이트가 읽지 않으므로 push하지 않는다.**

The HTML pages fetch these directly. **No staging templates between publishing and the HTML** (root single-source since 2026-05-28).

> ### ⚠️ 2026-07-22 변경 — K-ICS 하단 3패널이 인라인에서 fetch로 바뀜
>
> 그전까지 tier1/tier2/forward 데이터는 `K-ICS.html` 안에 `window.TIER1_DATA` /
> `TIER2_DATA` / `FORWARD_DATA`로 **붙여넣어져** 있었다(147KB = 파일의 70%). 이제
> 위 표의 루트 JSON 3개를 `fetch`한다.
>
> **배포에 미치는 영향 — 반드시 지킬 것:**
> 1. 이 3개 JSON은 **keep-list 신규 항목**이다. `K-ICS.html`만 올리고 이걸 빼면
>    자본도넛·forward 패널이 **에러도 콘솔 메시지도 없이 빈칸**이 된다.
> 2. keep-list는 여전히 §0 원칙대로 **HTML에서 재도출**한다(추측 금지). 이제
>    `python -m pytest tests/test_deploy_assets.py`가 4개 페이지의 fetch/link 로컬
>    참조를 전부 뽑아 저장소 존재를 강제하므로, **push 전 이 테스트를 돌리면
>    keep-list 누락이 기계적으로 잡힌다.**
> 3. `forward_capital_simulation.py`의 **`--no-html` 플래그는 사라졌다.** 그 플래그는
>    스크립트가 K-ICS.html 라인을 직접 치환했기 때문에(=publishing이 designer 영역을
>    침범) 존재했던 것이다. 이제 데이터 JSON만 쓰므로 스테이지 경계 문제가 없다.
>    그냥 인자 없이 실행하면 된다.
> 4. `templates/tier{1,2}_utilization_latest.json`은 **삭제됐다**(쓰는 스크립트가
>    하나도 없이 2025.4Q에 얼어붙어 있었고, 데이터계약 게이트만 그걸 보고 있었다).
>    `templates/forward_capital_latest.json`은 스크립트가 계속 쓰지만 **배포본은
>    루트 쪽**이다.
> 5. `templates/kics_disclosure.json`(5.9MB)도 **삭제됐다.** 루트 마스터와 바이트
>    동일한데 읽는 코드가 0이었다. **더 이상 동기화하지 말 것.**

---

## 2. Per-domain assembly scripts

### 2.1 K-ICS merge (md_inbox → kics_disclosure.json)
- `scripts/fill_period_to_disclosure.py` — main merge
- `scripts/fill_subitems_to_disclosure.py` — subitem injection
- `scripts/fill_post_transition_to_disclosure.py` — 경과조치적용후 데이터
- `scripts/fill_missing_ratios.py` — derived ratio backfill
- `scripts/fill_2025_q4_to_disclosure.py` — period-specific (template for future quarter scripts)
- `scripts/recalc_kics_derived.py` / `scripts/recalc_basic_capital_ratio_post.py` — derived metrics
- `scripts/compute_tier{1,2}_utilization.py` — Tier 1/2 hybrid utilization
- `scripts/forward_capital_simulation.py` — forward-looking sim (F4/F5)
- `scripts/promote_from_to_be.py` — what-if → as-is promotion

### 2.2 IFRS17 batch builders + viz
- `scripts/ifrs17_batch_{all,historical,bs_snapshot,insurance_pl,kics_sensitivity,measurement,reinsurance,sensitivity}.py`
- `scripts/ifrs17_promote_history_to_measurement.py`
- `scripts/build_ir_disclosed_multiples.py`, `scripts/build_nb_csm_multiple.py`, `scripts/build_net_income_breakdown.py`
- `scripts/viz_build_{csm_bubble,csm_waterfall,csm_waterfall_history,earnings_quadrant,ifrs17_kpis,ifrs17_panels,nb_csm_ratio}.py`
  > 이 중 `viz_build_ifrs17_panels.py`·`viz_build_csm_waterfall.py`는 **골든 있음**(2026-07-22):
  > 산출을 바꾸면 `python -m pytest tests/test_viz_{ifrs17_panels,csm_waterfall}_golden.py`가
  > `data/dart/viz/`의 커밋본과 대조한다. 나머지 5개는 아직 골든 없음(참고 목록에서 언급된
  > `build_ir_disclosed_multiples.py`는 2026-06 아카이브로 이동 — `archive/2026-06_*`).

### 2.3 Misc
- `scripts/build_lotte_series.py`
- `scripts/normalize_bond_schedule.py`
- `scripts/analyze_transitional_measures*.py`
- `scripts/export_red_all_cases.py` / `scripts/summarize_red_findings.py` (post-validation reporting)

---

## 3. Gate checks (run in order before recommending push)

**#0 must pass first. Any RED = BLOCKED. No documented-exception bypass.**

0. **Data-contract gate** — run `python scripts/prepush_check.py` (supersedes standalone `validate_data_contract.py`). Runs: ① data-contract hard gate (census + as-of staleness + domain-identity CHECK4) · ①b K-ICS rule gate (`validate_kics_disclosure.py`, wired 2026-08-21) · ①c 4 domain gates (csm_continuity · kics_rate_sensitivity · nb_csm_multiple · csm_waterfall) · ③ inbox hygiene (`check_inbox_hygiene.py --mechanical-only`) · ④ offline test bundle (goldens + rule-coverage manifest + push-gate wiring manifest). **exit 2 = push BLOCKED, no exception, no documented-exception bypass.** `blocked = n_red or n_hyg or n_test or n_kics or n_dom`.

   > **The generic-anomaly discovery/triage chain is NOT in this gate any more (2026-08-25, commit `22697c2`).** It was moved out — not deleted — to `scripts/scan_generic_anomalies.py`. Reason (measured): the layer produced 224 of the gate's 297 YELLOWs plus an 83-item review queue on *every* run, and **never once emitted a RED** — being YELLOW-only by design it was never in `blocked`, so it structurally could not block a push. `prepush_check.py` still prints one line about it every run so it cannot vanish silently. **Do not treat "it left the gate" as "it is not done any more"** — see §3.0b for who runs it and when.

   The run takes ~5 min (the offline bundle runs `FULL_COVERAGE_SWEEP=1`). **Never quote a gate verdict you did not run** — this section deliberately carries no cached "current live RED=0" line any more, because a stale pass here reads as permission. Run it, paste the verdict into the round report, and remember that a technical gate-clear is still not a push: an explicit owner GO is required (publishing recommends only).

0b. **Generic-anomaly discovery + LLM-skeptic — round-scoped, not per-push (decision 2026-08-25).**

   **When it runs (all four triggers; publishing is the owner of the step):**
   1. **Once per quarterly round** — before the *first* push of a newly-loaded quarter, after both parser lanes have landed and validation reports RED=0. This is the default cadence.
   2. **After a new master JSON is onboarded** (e.g. `IFRS17_BS.json` 2026-08-14, `dividend.json` 2026-08-15) — a brand-new master has no own-history for triage to lean on, so the cohort scan is the only outlier check it gets.
   3. **After a builder/parser overhaul or a bulk backfill** (a master gains/loses ≥100 rows in one change).
   4. **On owner request.**

   It does **not** run on incremental pushes (an HTML tweak, a handful of corrected cells). Rationale, measured: every data fix this layer ever produced came from one mass-load round (2026-06-19/20 — 교보생명 원수예실차 4분기 · BNP파리바카디프 단위오류 1.77조 · 코리안리 중복 43 · 교보라이프플래닛 보험금융손익); across the two months of incremental pushes that followed it produced **0**. The value is concentrated in mass-load moments, so that is where the cost is paid. Abolishing it outright was rejected: the arithmetic gates close on a unit error that is internally consistent (the 1.77조 case), so this is the only layer that catches that class. "Owner request only" was rejected too — this repo's recurring failure mode is a step that is documented but that nobody remembers exists.

   **Recording it is part of the step.** Whether it ran, and the verdicts, go into the round's `artifacts/publishing/<period>_<ts>.md` report **and** the `TODO_publishing.md` status entry for that round. A round report with no anomaly line means the step was skipped, and that is a finding, not a default.

   **How to run:**
   ```
   C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/scan_generic_anomalies.py
   ```
   Writes the same two paths it always did — `data/_derived/anomaly_triage.json` (full review queue) + `data/_derived/anomaly_skeptic_input.json` (REAL+UNCERTAIN). Both files are **git-tracked**, so a run dirties the working tree; use `--no-write` for a look-only pass. Baseline as of 2026-08-25: 224 candidates (PEER_OUTLIER 147 · COHORT_ZERO 77) → triage REAL=77 UNCERTAIN=6 NOISE=134 OWNER_CONFIRMED=8 → skeptic input 83.

   **LLM-skeptic step (publishing performs, on the cadence above):** classify each adversarially as **EXTRACTION_ERROR / UNIT_ERROR / REAL_EVENT / NOISE**. Route EXTRACTION_ERROR/UNIT_ERROR to the appropriate parser inbox (lane: ifrs17 for CSM_waterfall/PL, lane: kics for K-ICS). REAL_EVENT/NOISE pass through. A skeptic verdict never blocks a push by itself — it produces inbox tickets, and it is the resulting parser fix landing as a gate RED that blocks.

   **Reviving it into the gate** (if the round cadence proves too loose): uncomment `# check_generic_anomalies(res, env)` in `run_gate()` of `scripts/validate_data_contract.py` and flip `DATA_CONTRACT_CHECKS["check_generic_anomalies"]` to `WIRED` in `tests/test_push_gate_wiring.py` — the test blocks you if you change one without the other, deliberately.

   **Hardening rules (owner 2026-06-20, `inbox/_resolved/20260620T0859Z__owner__MULTI__skeptic_hardening_grounding.md` — added after skeptic fabricated a sibling line-item and repeatedly re-flagged owner-confirmed cells, see [[project_owner_confirmed_registry]]):**
   1. **Input scope = `anomaly_skeptic_input.json` UNCERTAIN items only.** REAL items are already high-precision from deterministic own-history triage — re-litigating them is double noise, not extra safety. Never re-derive candidates from the raw master, and never invent a cell/line-item that isn't in the input (the 코리안리 "두 항목이 동일" fabrication: skeptic invented a sibling value that doesn't exist in the master and called it a duplicate).
   2. **Master grounding before EXTRACTION_ERROR.** Before returning that verdict, read the cell's actual value from the master (`PL_breakdown.json` / `CSM_waterfall.json`, keyed by 원수사명+공시분기+항목명) and compare against that company's own history. A "these two values are identical" claim is only valid after actually reading both values — not inferred from field names.
   3. **Respect `data/_gold/user_pl_confirmed_cells.json`.** Triage already suppresses matches into `OWNER_CONFIRMED` before the skeptic sees the queue, so a confirmed cell should never appear in `anomaly_skeptic_input.json`. If one does, that means the registry is missing an entry — recommend registering it, never edit the data to make the flag go away.
   4. Prior verdict at `data/_derived/anomaly_skeptic_verdict.json` (orchestrator-generated) may be used as reference but must be re-verified if data changed.

   Queue state (2026-08-25, `scan_generic_anomalies.py`): REAL=77 UNCERTAIN=6 NOISE(auto-suppressed)=134 OWNER_CONFIRMED(suppressed)=8 → `anomaly_skeptic_input.json` 83 items, **unclassified** — carried since the 2026-06 round. Per the hardening rule above only the 6 UNCERTAIN are in scope for the skeptic; the 77 REAL are already high-precision from deterministic own-history triage.

   > The data-contract RED=42 episode of 2026-08-14 (`[IFRS17_BS] BS_CENSUS_MISSING_ITEM` on 6 non-listed companies with no DART XBRL source at all) was closed by owner via the `IFRS17_BS_NO_SOURCE` census exemption (`inbox/_resolved/20260814T0620Z`); `BS_IDENTITY` still runs on those 6.

1. **Validation gate** — every domain's most recent validation report has `summary.red == 0` (or every RED has a TODO.md documented-exception entry). K-ICS: see TODO.md §K-ICS gate for current documented exceptions.
2. **Assembly gate** — assembly/build scripts exit code 0; masters byte-changed (no spurious diffs).
3. **HTML gate** — for K-ICS.html / IFRS17.html / index.html: changed only if the underlying master changed. If HTML is dirty but masters are clean, surface as `manual_html_edit` for designer review (likely a designer commit).
4. **Encoding gate** — newly-touched .md/TODO files are UTF-8 no BOM, no garbled Korean (CLAUDE.md "문서·TODO 인코딩 룰").
5. **Untracked files gate** — list new untracked files; flag any that look like secrets (`.env*`, `*.key`, `*credential*`).

---

## 4. Suggested commit message format

```
<period>: <one-line summary>

- K-ICS: <#rows changed / RED count after validation>
- IFRS17: <#filings ingested / waterfall rebuilt>
- Misc: <bonds/IR/KIDI delta>

Validation: RED=0 across <K-ICS / IFRS17 / misc>.
```

No Co-Authored-By trailer unless user requests.

---

## 5. Suggested git commands

```bash
# Stage exactly the changed masters (explicit, never -A)
git add <file1> <file2> ...

# Commit
git commit -m "<see §4>"

# Push
git push origin <branch>
```

The agent runs the local-git commands itself (`add` / `commit` / `branch` / `checkout` / `rm`); **only the outward `git push` is gated** — show the user exactly what will be pushed, get their GO, then run it (see the header execution-model · §1 hard rules · §9 procedure).

---

## 6. Escalation paths

| Condition | Recommendation | Reason |
|---|---|---|
| validation RED > 0 (any domain) | `BLOCKED` | downstream HTML would show wrong numbers |
| validation YELLOW only | `WARN_BUT_OK` | QoQ anomaly notes, user reviews after push |
| untracked secret-shaped file | `BLOCKED` | risk of leaking key |
| HTML changed without master change | `WARN_BUT_OK + manual_html_edit` | likely designer-stage edit; surface but don't block |
| 100+ files changed | `WARN_BUT_OK + bulk_change` | user confirms scope |

---

## 7. Hand-off to designer

After publishing writes the masters, the designer stage may need to:
- Verify the new master data renders correctly in HTML (regression check on existing panels)
- Add new panels / charts for new metrics
- Update responsive layouts when new fields exceed existing space budgets

Publishing doesn't run designer — they're independent stages working from the same master JSONs. See [claude-agent-designer.md](claude-agent-designer.md).

---

## 8. TBD (owner to author)

- [ ] Idempotency contract — re-running publishing on the same validated input must produce byte-identical output (deterministic JSON ordering, no timestamps in payload).
- [ ] HTML-input schema versioning — when a master adds a new field, version bump rules.
- [ ] Derived metrics catalog — which `recalc_*` and `compute_*` produce which fields, ordered DAG.
- [ ] Viz JSON contract per panel (currently scattered across viz_build_*.py docstrings).
- [x] Branch policy — push to `main` directly (no PR), always via isolated `git worktree` cherry-push of the keep-list, never a same-folder branch switch. See **§9 + the new `launch-runbook` skill** (`docs/launch_runbook.md`, 2026-07-21).
- [x] Site-deploy hook — GitHub Pages serves `main` via `CNAME`; post-push verification = curl/WebFetch one master JSON + one HTML page (200 + expected content), ~1-2min propagation. `docs/launch_runbook.md` §5.
- [x] Rollback contract — `docs/launch_runbook.md` §6 (new, 2026-07-21): bad HTML/JSON on `main` → `git revert` (never force-push) from an isolated worktree, re-verify live; corrupted master xlsx → restore `.bak` or reopen in Excel (rebuild via `build_master_xlsx.py` is last resort, needs owner heads-up). Adopted as a **local skill** (`launch-runbook`) per owner request (`inbox/publishing/20260721T0233Z`) — this repo already has a local-skill pattern (a11y-audit, incident-postmortem), no external skill needed.

---

## 8b. ⏳ DEFERRED — fix the publish architecture (user said "alert me next time", 2026-05-31)

The §9 slim-publish dance is **too heavy to repeat every update** and the user flagged two real problems. Surface this as an alert in a future session; do NOT act on it without the user's go.

1. **Branch-switch dance is fragile.** Today's publish switched `main` ↔ feature branch inside the same working folder, rewriting thousands of files ("work disappears, then restored"). This can collide with subagents operating in that folder.
2. **IP still lives in public history.** The slim cleaned only the *latest* `main` snapshot. Old commits (`7104bd7` and earlier) on the public remote still contain `scripts/`, `src/`, etc. — recoverable by anyone browsing history. The served site is clean; the repo history is not.

**Recommended fix (when the user opts in):** a **dedicated public repo containing site assets only**. Working tree stays local/private; publish = copy built HTML + master JSONs into the public repo → commit → push (~30s, no branch switch, no vanishing files, and a clean history from day one). Alternative: `git worktree` for `main` (one repo, separate folder — lighter, but does NOT clean the existing IP history).

---

## 9. Public-repo slim-publish procedure (site-assets-only model)

**Why.** The public GitHub repo (`main`, served by GitHub Pages at www.insurequant.com) must contain **only site assets**: the HTML pages + the master JSONs those pages fetch + `CNAME` + `.gitignore`. All IP — `scripts/`, `src/`, `docs/`, agent MD/TODO, raw + intermediate data — stays **out** of the public repo. Working code lives on feature branches locally (and optionally a private repo); `main` is the public face.

**Keep-list (the ONLY files allowed on public `main`).** Authoritative = `git ls-tree -r --name-only main`; re-derive per §9.0 (grep the HTML) whenever an HTML's fetches change. Snapshot **verified live 2026-08-14** (`git ls-tree main` = commit `255e445`):

```
.gitignore
CNAME
common.css                                 # shared design system — referenced by all 3 HTML (<link>); MUST ship with them
index.html
K-ICS.html
IFRS17.html
공시보고서.html
CSM_waterfall.json
NB_CSM_multiple.json
PL_breakdown.json
kics_disclosure.json
kics_rate_sensitivity.json
kics_tier1_utilization.json
kics_tier2_utilization.json
kics_forward_capital.json
data/dart/viz/csm_amort_schedule.json
data/dart/viz/csm_waterfall.json
data/dart/viz/csm_waterfall_history.json
data/dart/viz/insurance_pl_breakdown.json
data/dart/viz/sensitivity_heatmap.json
data/ir/nb_csm_ratio.json
IFRS17_BS.json                             # NOT on main yet — IFRS17.html already fetches it (2026-08-14),
                                            # replaces archived equity_composition.json. Gate RED=0 as of
                                            # 2026-08-14 (was RED=42, cleared via IFRS17_BS_NO_SOURCE census
                                            # exemption on 6 non-listed cos, inbox/_resolved/20260814T0620Z).
                                            # Technical gate clear — still needs explicit owner GO to push.
```

**Path migration LANDED (2026-06-16).** Live `main` serves viz from `data/dart/viz/*` (matches §1 canonical) — `data/ifrs17/viz/*` no longer exists anywhere in the repo (verified via `git ls-tree -r main` and local `data/`, 2026-08-06). `common.css` is a **new deploy asset** (designer frontend-design skill) — the 3 HTML pages `<link>` it, so it is now part of the keep-list and **must be pushed alongside any HTML change** (omitting it breaks all styling). No `csm_bubble.json` on main (index.html embeds the bubble inline).

**Procedure (agent runs the local git mechanically; only the push is gated).**

0. **Derive the keep-list, never guess it.** Grep each HTML for what it fetches (`fetch(` / `dataPaths(` / `resolveUrl(` / `src=` / `href=`). The keep-list = those files + the HTML + `CNAME` + `.gitignore`.
1. **Park in-progress work first.** On the feature branch: `git add -A && git commit -m "WIP checkpoint <reason>"`. A durable commit guarantees nothing is lost on the branch switch (do NOT use `git stash` for this — see §10).
2. **Switch to `main`** (must be clean): `git checkout main`. Untracked-but-present files can block the switch — move/remove them first.
3. **Delete everything not in the keep-list:** `git rm -r <paths>`. Build the delete list from `git ls-files`, NOT from memory; for dirs where you keep some + drop some (e.g. `data/ir`), list those file-by-file via `git ls-files <dir>` first.
4. **VERIFY before committing:** `git ls-files` must equal the keep-list exactly. If wrong → `git reset --hard` (safe pre-commit undo) and rebuild. This is the last safe checkpoint.
5. **Commit:** `git commit -m "slim public repo: keep only HTML + master JSONs (site assets)"`.
6. **GATE → push.** Show the user exactly what will be pushed; on their GO, run `git push origin main` (the user completes the browser login). The slim commit is tiny (deletions only) — a push that appears to "hang" is waiting for auth, not uploading.
7. **Verify live.** WebFetch a master-JSON URL + one HTML page (expect 200 + valid content). GitHub Pages takes ~1–2 min to redeploy.
8. **Return to the feature branch:** `git checkout <feature-branch>`; confirm work restored (`git status` clean, key files present).

History is not lost by this slim — removed files remain in old commits forever and can be restored with `git checkout <old-commit> -- <path>`.

---

## 10. Safe-git rules (learned the hard way, 2026-05-31)

- **Never `git stash drop` to "tidy up"** a stash you might still need. To restore stashed work use `git stash pop` / `apply` — never `drop`. A mis-applied drop nearly lost a full working tree this session.
- **Prefer a "WIP checkpoint commit" over `git stash`** for parking work across a branch switch. Commits are durable and named; stashes are easy to lose.
- **`git reset --hard` is a safe undo ONLY before commit/push** (discards working changes back to the last commit). After a *bad commit*, prefer `git revert` (history-safe) over reset.
- **Recovery exists.** Dropped commits/stashes survive ~90 days as unreachable objects: `git fsck --no-reflog --unreachable` → find the `unreachable commit` → `git stash apply <hash>` or `git checkout <hash> -- .`. **Never run `git gc` / `git prune` / `git clean` while a recovery is pending** — they purge the safety net.
- **Locked files** (`unlink failed` / `Invalid argument`): a file open in Excel or mid-OneDrive-sync blocks `git rm` / `checkout`. Close the app / pause sync, then retry.
- **A "hanging" push** with no upload progress is almost always waiting for auth (login popup behind the terminal), not transferring data.
