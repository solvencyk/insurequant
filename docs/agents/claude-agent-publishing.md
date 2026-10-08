# Agent: Publishing (Stage 4 — assemble masters + recommend push)

> **Execution model (user decision 2026-05-31):** this agent **executes the mechanical git/file work itself** — status, add, commit, branch, `git rm`,
> and the master-JSON build scripts. The user is asked only for: (a) browser login / auth, (b) an explicit GO immediately before an outward push to
> the live `main`, (c) genuine decisions. 변경 이력은 `docs/changelog_publishing.md`.

You are the publishing subagent. Responsibilities in this stage:

1. **Build the master JSONs.** Once **validation** ([claude-agent-validation.md](claude-agent-validation.md)) passes on the **parser** ([claude-agent-parser.md](claude-agent-parser.md)) output, running the assembly/build scripts that turn validated per-source JSON into the unified master tables the public HTML reads **is this agent's job, not the user's.** (See §2.)
2. **Publish.** Regenerate `public_exports/`, run the gate, prepare the deploy (§9).
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
  - List of changed masters
  - Suggested commit message (1-line summary + bullet body)
  - Suggested `git add` set (explicit file list, NEVER `git add -A`)
  - Final recommendation: `READY_TO_PUSH` | `BLOCKED` | `WARN_BUT_OK`
- exit code: `0` if READY_TO_PUSH, else `1` (BLOCKED) or `0` with WARN noted.

**Hard rules**
- Never overwrite a master while `validation_report.summary.red > 0` for the same domain. Block and escalate.
- Local git (`add`, `commit`, `branch`, `checkout`, `rm`) and the master-JSON build scripts: the agent runs these itself.
- **Live `main` deploy is the gated step** — state exactly which files will go, get the owner's GO. Never push to `main` silently.
- Before any destructive git op (`reset --hard`, `clean`, `stash drop`, `gc`, `prune`), state the impact and the recovery path first. See §10.

---

## 1. Canonical master locations (read by HTML)

> **이 표는 손으로 유지하지 말고 아래 명령으로 재도출하라.** keep-list의 근거 문서가 틀리면 배포가 조용히 깨진다
> (`tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` 가 "페이지가 fetch 하는 JSON 은 전부 이 문서와 designer §1 에 이름이 있다" 를 강제).
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

**2026-10-07 도출 결과 (live `main` 과 일치 확인):**

| Page | Fetches |
|---|---|
| `index.html` | `kics_disclosure.json` · `CSM_waterfall.json` · `NB_CSM_multiple.json` |
| `K-ICS.html` | `kics_disclosure.json` · `kics_rate_sensitivity.json` · `kics_duration_gap.json` · `kics_tier1_utilization.json` · `kics_tier2_utilization.json` · `kics_forward_capital.json` |
| `IFRS17.html` | `CSM_waterfall.json` · `PL_breakdown.json` · `NB_CSM_multiple.json` · `kics_disclosure.json` · `IFRS17_BS.json` · `data/dart/viz/csm_waterfall.json` · `csm_amort_schedule.json` · `insurance_pl_breakdown.json` · `sensitivity_heatmap.json` · `data/ir/nb_csm_ratio.json` · `data/loss_ratio/panel_loss_ratio.json` · `data/persistency/panel_persistency.json` |
| `공시보고서.html` | `dividend.json` · `kics_disclosure.json` |

The HTML pages fetch these directly — **데이터를 HTML 에 인라인하지 않는다**(K-ICS 하단 3패널도 루트 JSON 을 fetch 한다. JSON 을 빼고 HTML 만 올리면
패널이 에러 없이 빈칸이 된다). 빌더가 만들지만 어떤 페이지도 읽지 않는 파일(`csm_bubble.json`·`ifrs17_panels.json`·`net_income_breakdown.json`·
`nb_premium_wolnap.json`·`disclosed_csm_multiple.json`)은 배포하지 않는다.

> ### HTML 무참조 상시 유지 파일
>
> 아래 파일은 **어떤 HTML 도 참조하지 않아 위 grep 으로 도출되지 않지만** 공개 `main` 에 반드시
> 있어야 한다. 빠져도 에러가 안 나고 조용히 풀린다. `tests/test_deploy_assets.py::
> test_always_keep_files_exist_and_are_documented` 가 존재 + 이 절·`docs/launch_runbook.md` 에
> 이름이 있는지 강제한다(`ALWAYS_KEEP` 상수가 정본 — 새 항목은 거기와 두 문서를 같이 고칠 것).
>
> | 파일 | 빠지면 |
> |---|---|
> | `CNAME` | 커스텀 도메인 해제 |
> | `.nojekyll` | GitHub Pages 기본 Jekyll 이 `_` 로 시작하는 경로를 배포에서 뺌 |
> | `.gitignore` | slim 워크트리 위생 |
> | `robots.txt` | 크롤러 정책(AI 학습 크롤러 차단·`/public_exports/` 색인 제외) 소멸 |
> | `LICENSE` | 공개 저장소·`https://www.insurequant.com/LICENSE` 의 이용 조건 사라짐(데이터베이스제작자권 고지) |
> | `og-image.png` | 링크 미리보기 카드. `og:image` 메타만 가리켜 grep 으로 도출되지 않는다. 빠지면 카톡·팀즈·링크드인 미리보기가 글자만 남음(2026-10-07) |
>
> `sitemap.xml` 은 각 HTML 의 `<link rel="sitemap">` 으로 참조돼 grep 으로 도출된다. `common.css`·`theme.js`·`download-survey.js`·
> `report-widget.js`·`forms-config.js`·`privacy.html`·`public_exports/*` 는 HTML `<script src>`/`href` 또는 그 JS 의 fetch 로 도출된다.

---

## 2. Per-domain assembly scripts

### 2.1 K-ICS merge (md_inbox → kics_disclosure.json)
- `scripts/fill_period_to_disclosure.py` — main merge
- `scripts/fill_subitems_to_disclosure.py` — subitem injection
- `scripts/fill_post_transition_to_disclosure.py` — 경과조치적용후 데이터
- `scripts/fill_missing_ratios.py` — derived ratio backfill
- `scripts/recalc_kics_derived.py` / `scripts/recalc_basic_capital_ratio_post.py` — derived metrics
- `scripts/compute_tier{1,2}_utilization.py` — Tier 1/2 hybrid utilization → `output/tier{1,2}_utilization/`
- `scripts/wire_capital_securities_to_utilization.py` — 위 산출물의 분자를 DART per-bond + 경과조치 면제로 갈아끼운다 (in place)
- **`scripts/sync_tier_utilization_to_deploy.py` — `output/tier{1,2}_utilization/` → 배포본 루트 `kics_tier{1,2}_utilization.json`.**
  위 두 스크립트를 돌렸으면 **반드시** 이것도 돌린다(기본 dry-run, `--apply` 로 반영). 건너뛰면 배포본이 옛 스냅샷에 굳는다 —
  `validate_live_artifacts.py` 의 `TIER_DEPLOYED_VALUE_DIFFERS` 가 뜨면 이 sync 를 건너뛴 것이다(`PM-2026-08-25_gate_read_the_wrong_file.md`).
- `scripts/forward_capital_simulation.py` — forward-looking sim (인자 없이 실행, 데이터 JSON 만 쓴다)
- `scripts/promote_from_to_be.py` — what-if → as-is promotion

### 2.2 IFRS17 batch builders + viz
- `scripts/ifrs17_batch_{all,historical,bs_snapshot,insurance_pl,kics_sensitivity,measurement,reinsurance,sensitivity}.py`
- `scripts/ifrs17_promote_history_to_measurement.py`
- `scripts/build_nb_csm_multiple.py`, `scripts/build_net_income_breakdown.py`
- `scripts/viz_build_{csm_bubble,csm_waterfall,csm_waterfall_history,earnings_quadrant,ifrs17_kpis,ifrs17_panels,nb_csm_ratio}.py`
  > `viz_build_ifrs17_panels.py`·`viz_build_csm_waterfall.py` 는 **골든 있음** — 산출을 바꾸면
  > `python -m pytest tests/test_viz_{ifrs17_panels,csm_waterfall}_golden.py`. 인플레이스로 덮어쓰는 빌더라 실행 전 백업.

### 2.3 Misc
- `scripts/analyze_transitional_measures*.py`
- `scripts/export_red_all_cases.py` / `scripts/summarize_red_findings.py` (post-validation reporting)
- `scripts/export_public_sheets.py` — **커밋된 HEAD 를 읽는다**: 마스터 커밋 → `public_exports/` 재생성 → 재커밋.

---

## 3. Gate checks (run in order before recommending push)

**#0 must pass first. Any RED = BLOCKED. No documented-exception bypass.**

0. **Push gate** — `python scripts/prepush_check.py`(훅과 같은 것). ① data-contract hard gate · ①b K-ICS rule gate · ①c 도메인 게이트 ·
   ③ inbox hygiene · ④ 오프라인 테스트(골든 + 매니페스트). **exit 2 = push BLOCKED.** 범위 판정은 `CLAUDE.md` §5.
   **Never quote a gate verdict you did not run** — 돌려서 verdict 를 라운드 보고서에 붙인다. 기술적 gate-clear 는 push 허가가 아니다(owner GO 별도).

0b. **Generic-anomaly discovery + LLM-skeptic — 라운드 단위, push 마다가 아니다(2026-08-25 결정).**
   - **언제**: ① 새 분기 적재 후 첫 push 전(양 parser 레인 적재 + validation RED=0) ② 새 마스터 JSON 온보딩 직후 ③ 빌더/파서 대개편·대량 백필(한 변경에 ±100행)
     ④ owner 요청. HTML 수정·소수 셀 정정 같은 증분 push 에서는 안 돌린다. 산술 게이트가 못 보는 "내부적으로 일관된 단위 오류"(1.77조 사례)를 잡는 유일한 층이다.
   - **실행**: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/scan_generic_anomalies.py` → `data/_derived/anomaly_triage.json` + `anomaly_skeptic_input.json`
     (둘 다 git 추적이라 워킹트리가 더러워진다 — 보기만 할 땐 `--no-write`).
   - **기록이 단계의 일부다**: 돌렸는지와 판정을 라운드 보고서와 `TODO_publishing.md` Status 에 남긴다. 줄이 없으면 건너뛴 것이다.
   - **skeptic 규칙**(owner 2026-06-20): 입력은 `anomaly_skeptic_input.json` 의 UNCERTAIN 만(REAL 재심 금지, 마스터에서 후보를 새로 만들지 말 것) ·
     EXTRACTION_ERROR 판정 전에 마스터 셀 실제 값과 자기 이력을 읽는다(필드명으로 "두 값 동일" 추론 금지) · `data/_gold/user_pl_confirmed_cells.json` 존중
     (확정 셀이 입력에 있으면 등재 누락이니 등재를 권고하고 데이터는 고치지 않는다). 분류는 EXTRACTION_ERROR / UNIT_ERROR / REAL_EVENT / NOISE,
     앞의 둘만 parser inbox(lane 지정)로 보낸다. skeptic 판정 자체는 push 를 막지 않는다.
   - **게이트로 되살리려면** `validate_data_contract.py` `run_gate()` 의 `# check_generic_anomalies(res, env)` 주석을 풀고
     `tests/test_push_gate_wiring.py` `DATA_CONTRACT_CHECKS["check_generic_anomalies"]` 를 `WIRED` 로 — 한쪽만 바꾸면 테스트가 막는다.

1. **Validation gate** — every domain's most recent validation report has `summary.red == 0` (or every RED has an entry in `docs/kics_gate_exceptions.md` / the code registries).
2. **Assembly gate** — assembly/build scripts exit code 0; masters byte-changed (no spurious diffs).
3. **HTML gate** — HTML changed only if the underlying master changed. If HTML is dirty but masters are clean, surface as `manual_html_edit` for designer review.
4. **Encoding gate** — newly-touched .md/TODO files are UTF-8 no BOM, no garbled Korean.
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

Publishing doesn't run designer — they're independent stages working from the same master JSONs. When a master gains a field or a new master
appears, tell designer the path and the schema delta. See [claude-agent-designer.md](claude-agent-designer.md).

---

## 8. 미작성 계약 (owner 가 정할 것)

- Idempotency contract — re-running publishing on the same validated input must produce byte-identical output (deterministic JSON ordering, no timestamps in payload).
- HTML-input schema versioning — when a master adds a new field, version bump rules.
- Derived metrics catalog — which `recalc_*` and `compute_*` produce which fields, ordered DAG.
- Viz JSON contract per panel (currently scattered across viz_build_*.py docstrings).
- (보류, owner 2026-05-31 "다음에 알려줘") 공개 저장소의 옛 커밋(`7104bd7` 이전)에 `scripts/`·`src/` 등이 남아 있다 — 사이트 자산 전용 저장소로 분리할지.

---

## 9. 배포 — public `main` 은 site-assets-only

**Why.** 공개 GitHub 저장소의 `main`(GitHub Pages, www.insurequant.com)에는 **사이트 자산만** 둔다: HTML + 그 HTML 이 fetch 하는 JSON +
위 상시 유지 파일 + `public_exports/` + jp 비공개 프리뷰(`jp-f9027362/`). `scripts/`·`src/`·`docs/`·TODO·원천 데이터는 작업 브랜치에만 있다.
작업 브랜치 push 는 라이브가 아니다.

**Keep-list 정본 = `git ls-tree -r --name-only origin/main`.** 2026-10-07 실측(jp 10개 제외):
`.gitignore` · `.nojekyll` · `CNAME` · `LICENSE` · `robots.txt` · `og-image.png` · `sitemap.xml` · `common.css` · `theme.js` · `download-survey.js` · `report-widget.js` ·
`forms-config.js` · `privacy.html` · `index.html` · `K-ICS.html` · `IFRS17.html` · `공시보고서.html` · §1 표의 JSON 전부(`dividend.json`·`IFRS17_BS.json`
포함) · `public_exports/*`(15개). HTML 의 fetch 가 바뀌면 §1 명령으로 재도출하고 `tests/test_deploy_assets.py` 를 돌린다.

**절차 정본 = [`docs/launch_runbook.md`](../launch_runbook.md)** (격리 워크트리에서 main 으로 cherry-push · post-push 검증 · `git revert` 롤백).
- 같은 폴더에서 `git checkout main` 으로 브랜치를 오가는 방식은 **쓰지 않는다**(공유 워킹트리의 다른 세션 작업을 덮는다).
- owner 배포 경로: 폰 Termux 에서 저장소 클론 **안에서** `bash scripts/android_push_and_deploy.sh --from-origin --branch <작업브랜치>` —
  `origin/main` 과 작업 브랜치의 keep-list 차이 파일을 출력한 뒤 확인 없이 push 한다. 그래서 작업 브랜치를 먼저 push 해 둔다.
- 배포 후 `public_exports/manifest.json` 의 `build_id` 로 라이브를 확인한다(회사망은 TLS 검사 때문에 `curl -k` 가 필요할 수 있다).

---

## 10. Safe-git rules

- **Never `git stash drop` to "tidy up"** a stash you might still need. Restore with `git stash pop` / `apply` — never `drop`.
- **Prefer a "WIP checkpoint commit" over `git stash`** for parking work. Commits are durable and named; stashes are easy to lose.
- **`git reset --hard` is a safe undo ONLY before commit/push.** After a *bad commit*, prefer `git revert` (history-safe) over reset.
- **Recovery exists.** Dropped commits/stashes survive ~90 days as unreachable objects: `git fsck --no-reflog --unreachable` → `git stash apply <hash>` or `git checkout <hash> -- .`. **Never run `git gc` / `git prune` / `git clean` while a recovery is pending.**
- **Locked files** (`unlink failed` / `Invalid argument`): a file open in Excel or mid-OneDrive-sync blocks `git rm` / `checkout`. Close the app / pause sync, then retry.
- **A "hanging" push** with no upload progress is almost always waiting for auth (login popup behind the terminal), not transferring data.

## 12. jp 레인 산출물

`J-ESR/build_jesr_page_json.py` 가 `J-ESR/jesr_master.json` + 배포용 `jp/jesr_esr.json`(바이트 동일) 을 만든다(self-check 내장). 라이브 반영 시 `jp/index.html`·`jp/jesr_esr.json`·상세 3페이지(`jp/jesr.html`·`jp/jgaap.html`·`jp/disclosure.html` + `jp/jp.css`·`jp/jesr_app.js`·`jp/jesr_detail.json`)·`jp/terms.html`·`jp/report-widget.ja.js` 를 배포 keep-list(`android_push_and_deploy.sh` NEW_FILES) 에 넣고 `tests/test_deploy_assets.py` 로 확인한다. 배포 경로는 `jp-f9027362/`(비공개 프리뷰, `TODO_jp.md`). xlsx 시트는 만들지 않는다(owner 결정 전까지). 도메인 지식은 `docs/domains/claude-agent-jp.md`.
