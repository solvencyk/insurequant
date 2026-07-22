# Agent: Publishing (Stage 4 — assemble masters + recommend push)

> **Status: SKELETON.** Body marked `TBD` is for the user/owner to author.
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

**2026-07-22 도출 결과 (검증됨):**

| Page | Fetches |
|---|---|
| `index.html` | `kics_disclosure.json` · `CSM_waterfall.json` · `NB_CSM_multiple.json` |
| `K-ICS.html` | `kics_disclosure.json` · `kics_rate_sensitivity.json` · `kics_tier1_utilization.json` · `kics_tier2_utilization.json` · `kics_forward_capital.json` |
| `IFRS17.html` | `CSM_waterfall.json` · `PL_breakdown.json` · `NB_CSM_multiple.json` · `data/dart/viz/csm_waterfall.json` · `csm_waterfall_history.json` · `csm_amort_schedule.json` · `insurance_pl_breakdown.json` · `sensitivity_heatmap.json` · `data/ir/nb_csm_ratio.json` |
| `공시보고서.html` | (없음 — 정적 페이지) |

여기에 `common.css` + `CNAME` + `.gitignore` + 4개 HTML을 더한 것이 keep-list다.

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

> **Path note:** the table lists the post-migration canonical (`data/dart/viz/*`). Live `main` still reads `data/ifrs17/viz/*` — see §9 "Pending path migration" for detail and the cutover trigger (when `fix/csm-*` lands on `main`).

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

0. **Data-contract + anomaly gate** — run `python scripts/prepush_check.py` (supersedes standalone `validate_data_contract.py`). Runs: ① data-contract hard gate (census + as-of staleness + domain-identity CHECK4) + ② generic-anomaly triage chain. **exit 2 (RED ≥ 1) = push BLOCKED, no exception, no documented-exception bypass.** Outputs: `data/_derived/anomaly_triage.json` (review queue) + `data/_derived/anomaly_skeptic_input.json` (REAL+UNCERTAIN candidates).

   **LLM-skeptic step (mandatory — publishing agent performs before recommending push):** Read `anomaly_skeptic_input.json` REAL+UNCERTAIN items and classify each adversarially as **EXTRACTION_ERROR / UNIT_ERROR / REAL_EVENT / NOISE**. Route EXTRACTION_ERROR/UNIT_ERROR to the appropriate parser inbox (lane: ifrs17 for CSM_waterfall/PL, lane: kics for K-ICS). REAL_EVENT/NOISE pass through. Prior verdict at `data/_derived/anomaly_skeptic_verdict.json` (orchestrator-generated) may be used as reference but must be re-verified if data changed. **Push recommendation forbidden without completing skeptic step.** Owner policy 2026-06-19.

   Current live (2026-06-20): RED=4 (all CHECK4 domain-identity: T2_UTIL_OVER_100_NO_EXEMPTION×3 [동양·KB·미래에셋, proxy-gross artifact] + T2_DENOM_NOT_SCR_HALF×1 [신한이지, 분모 1/100 스케일]). Routes pending: UTIL×3 → downloader OCR (`20260617T0000Z`) + kics parser; DENOM×1 → ifrs17 parser (`20260620T0238Z`); designer donut 잠정 숨김 완료.

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

**Keep-list (the ONLY files allowed on public `main`).** Authoritative = `git ls-tree -r --name-only main`; re-derive per §9.0 (grep the HTML) whenever an HTML's fetches change. Snapshot **verified live 2026-06-16** (commit `dbbb096`):

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
data/dart/viz/csm_amort_schedule.json
data/dart/viz/csm_waterfall.json
data/dart/viz/csm_waterfall_history.json
data/dart/viz/insurance_pl_breakdown.json
data/dart/viz/sensitivity_heatmap.json
data/ir/nb_csm_ratio.json
```

**Path migration LANDED (2026-06-16).** Live `main` now serves viz from `data/dart/viz/*` (matches §1 canonical); the old `data/ifrs17/viz/*` note is retired. `common.css` is a **new deploy asset** (designer frontend-design skill) — the 3 HTML pages `<link>` it, so it is now part of the keep-list and **must be pushed alongside any HTML change** (omitting it breaks all styling). No `csm_bubble.json` on main (index.html embeds the bubble inline).

**Procedure (agent runs the local git mechanically; only the push is gated).**

0. **Derive the keep-list, never guess it.** Grep each HTML for what it fetches (`fetch(` / `dataPaths(` / `resolveUrl(` / `src=` / `href=`). The keep-list = those files + the HTML + `CNAME` + `.gitignore`.
1. **Park in-progress work first.** On the feature branch: `git add -A && git commit -m "WIP checkpoint <reason>"`. A durable commit guarantees nothing is lost on the branch switch (do NOT use `git stash` for this — see §10).
2. **Switch to `main`** (must be clean): `git checkout main`. Untracked-but-present files can block the switch — move/remove them first.
3. **Delete everything not in the keep-list:** `git rm -r <paths>`. Build the delete list from `git ls-files`, NOT from memory; for dirs where you keep some + drop some (e.g. `data/ir`, `data/ifrs17/viz`), list those file-by-file via `git ls-files <dir>` first.
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
