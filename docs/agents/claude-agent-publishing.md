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

| Master | Path | Reader |
|---|---|---|
| K-ICS master | `kics_disclosure.json` (repo root) | K-ICS.html |
| IFRS17 CSM waterfall | `data/dart/viz/csm_waterfall.json` (+ `csm_waterfall_history.json`) | IFRS17.html |
| IFRS17 NB CSM bubble | `data/dart/viz/csm_bubble.json` | IFRS17.html + index.html |
| IFRS17 panels | `data/dart/viz/ifrs17_panels.json` (sensitivity, P&L, amort) | IFRS17.html |
| Forward capital | `templates/forward_capital_latest.json` | K-ICS.html (forward panel) |
| Tier 1/2 utilization | `templates/tier{1,2}_utilization_latest.json` | K-ICS.html |
| NB premium (월납월초) | `data/_derived/nb_premium_wolnap.json` | IFRS17.html |
| Net income breakdown | `data/dart/viz/net_income_breakdown.json` (F17) | IFRS17.html Panel 3 |
| Disclosed CSM multiples | `data/ir/disclosed_csm_multiple.json` | IFRS17.html |

The HTML pages fetch these directly. **No staging templates between publishing and the HTML** (root single-source since 2026-05-28).

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

### 2.3 Misc
- `scripts/build_lotte_series.py`
- `scripts/normalize_bond_schedule.py`
- `scripts/analyze_transitional_measures*.py`
- `scripts/export_red_all_cases.py` / `scripts/summarize_red_findings.py` (post-validation reporting)

---

## 3. Gate checks (run in order before recommending push)

1. **Validation gate** — every domain's most recent validation report has `summary.red == 0` (or every RED has a TODO.md documented-exception entry).
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
- [ ] Branch policy — push to main directly or always PR?
- [ ] Site-deploy hook (GitHub Pages CNAME serves from `main`; any post-push verification?)
- [ ] Rollback contract — if a bad push lands, what's the named revert procedure?

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
