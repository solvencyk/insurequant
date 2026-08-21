# Insurequant Changelog — Publishing Stage

> Last updated: 2026-08-14 · Stage 4/5 — publishing
> Prompt: docs/agents/claude-agent-publishing.md · TODO: TODO_publishing.md

**Scope:** master JSON assembly + change reporting + git push command recommendation. HTML structure/styling is **designer** ([`docs/changelog_designer.md`](changelog_designer.md)).

**Cross-stage history:** `docs/claude-changelog.md`.
**This file:** entries scoped to publishing work only.

---

## 2026-08-15 (배포 2차) — IFRS17 재무상태표 패널 T자 재구성 main push

`4f1d344..6e5634f`, 격리 워크트리 cherry-push. `IFRS17.html`(Panel 7 타일형 → Panel 1 최상단 T자, 좌 자산/우상 부채/우하 자본을 실값 비율로 배치 + 2단계 `+` 드릴다운, 세부 미공시 회사는 버튼 disabled) + `IFRS17_BS.json`(`섹션`·`레벨` 컬럼 신규, 항목 1-7→1-31, 1,637→5,008행 — 파서가 예고보다 빨리 세부계정 랜딩, owner가 원 발주 60여개 항목을 13개로 축소). 원 발주 `inbox/_resolved/20260814T1250Z`(owner→designer) — designer가 섹션/레벨 그룹핑 계약(항목번호 무하드코딩)으로 짜둬서 파서 스키마 랜딩 후 HTML 무수정으로 호환 확인.

부수 발견: `scripts/build_ifrs17_bs.py`가 이 시점까지 한 번도 git에 커밋된 적이 없었다(`git log --all` 이력 0건) — 이번 배포 커밋에 같이 포함해 추적 시작(단 main의 site-assets-only keep-list에는 안 들어감, 작업 브랜치에만).

Pre-flight `validate_data_contract.py` RED=0 YELLOW=236, `pytest test_deploy_assets.py` 10 passed. owner에게 파일목록 제시 후 GO 받고 push. **배포 확인 함정**: legacy `pages/builds/latest` API가 새 push 후 한동안 직전 커밋을 계속 "built"로 보여줘 폴링이 안 됨 — 이 저장소는 실제로 `pages-build-deployment` GitHub Actions 워크플로우로 배포되므로 `gh run list`/`gh run view --json headSha,conclusion`으로 해당 커밋의 run을 직접 확인하는 게 맞다(다음부터 이쪽 우선). 라이브 검증: `IFRS17_BS.json`에서 `섹션`/`레벨` 필드 WebFetch로 확인, `IFRS17.html`은 브라우저에서 삼성화재해상보험 선택 후 T자 패널 DOM 텍스트 직접 조회로 확인(자산 112조4,436억 = 부채 77조981억 + 자본 35조3,455억, 항등식 성립) — 세부 드릴다운 행(현금및현금성자산·보험계약부채·이익잉여금 등)도 실값으로 렌더.

---

## 2026-08-15 (배포) — 배당현황 오픈 + PL_breakdown 유실 셀 복구 main push

`de0aef9..4f1d344`, 격리 워크트리 cherry-push. 3파일: `dividend.json`(신규, DART alotMatter 배당에 관한 사항, 24개사, 1,924행) · `공시보고서.html`("준비 중" placeholder → 배당현황 대시보드, KPI 4종 + 항목1-7 분기표 + 종류주별 드릴다운, designer 작업물) · `PL_breakdown.json`(작업트리에서 유실됐던 61셀/1,475행 복구, 7,799→8,111행).

**dividend keep-list 등록** (`inbox/publishing/20260814T2230Z`): `dividend.json`+`scripts/build_dividend.py` 커밋(기존 미추적), `claude-agent-publishing.md` §1 fetch표에 `공시보고서.html`→`dividend.json` 등록해 `test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` FAIL→PASS 복구. xlsx는 이미 `배당` 시트가 있어 재생성 불필요(파서 확인).

**PL_breakdown 유실 복구**: 원 사고는 `inbox/parser/20260814T1637Z`(validation 발견, MASTER_HOLE RED=13) — `validate_master_tables.py`를 `--no-build` 없이 돌리면 첫 동작으로 `build_root_masters.py`를 재실행하는데, 그 산출물이 결정론적으로 61셀(1,475행)을 떨어뜨림(2026-07-30 근접사고와 동일 계열, `project_git_purge`). validation이 owner 지시로 HEAD∪작업트리 union-merge(키=원보험사코드+공시분기+항목번호, null-vs-실값까지 셀 단위 판정)로 8,111행 복구, `validate_master_tables.py --no-build` 골든 일치 확인. publishing은 그 복구본을 `PL_breakdown.json`만 단독 스코프로 커밋(`79b1f7d`, 공유 워킹트리 다른 세션 변경분 섞이지 않게 `git commit -- <path>`로 범위 고정)한 뒤 위 3파일과 함께 배포. **근본원인(빌더가 순가산이 아님 / rebuild 기본값)은 미수정 — `inbox/parser/20260814T1637Z`에 열어둠**, parser 몫.

Pre-flight `validate_data_contract.py` RED=0 YELLOW=220, `pytest test_deploy_assets.py` 10 passed. owner에게 정확한 파일목록+이유+게이트결과 제시 후 GO 받고 push. 배포 후 GitHub Pages 빌드 완료(`gh api .../pages/builds/latest` status=built로 폴링) 확인 후 라이브 검증: `dividend.json`/`PL_breakdown.json` WebFetch로 스키마 확인, `공시보고서.html`은 브라우저에서 실제로 삼성화재해상보험을 선택해 배당 Panel이 렌더되는지 DOM에서 직접 확인(현금배당금총액 8,289억원·주당배당금 19,500원·배당성향 41.1%, 2025.4Q 기준) — 콘솔 에러 0. 워크트리 정리 완료.

---

## 2026-08-14 (배포) — IFRS17_BS.json + IFRS17.html Panel 7 main push

`255e445..de0aef9`. 격리 워크트리(`../insurequant-main-deploy`)로 `IFRS17_BS.json`(신규 마스터, 1,637행) + `IFRS17.html`(Panel 7 "재무상태표·자본의 질") 2개 파일만 cherry-push — `common.css`는 main과 diff 0이라 미포함. Pre-flight `validate_data_contract.py` RED=0 YELLOW=220 확인, 정확한 파일목록+이유+게이트결과 제시 후 owner GO 받고 `git push origin main` 실행. 배포 후 검증: `IFRS17_BS.json`을 WebFetch로 스키마 확인(원보험사코드/원수사명/티커/생손보여부/항목번호/항목명/공시분기/값), `IFRS17.html`은 브라우저에서 실제로 삼성생명(KR0069)을 선택해 Panel 7이 렌더되는지 DOM에서 직접 확인(자산총계 309조 9,483억원 표시, 2025.4Q) — 콘솔 에러 0. 로컬 static server(8896 config) 사전 확인은 Browser pane 컴포지팅 문제로 무산됐으나 curl 200 확인 후 진행, 라이브 브라우저 검증으로 최종 확인 완료. 워크트리 정리 완료.

## 2026-08-14 — equity_composition → IFRS17_BS keep-list swap (HIGH, `20260814T0232Z`) + inbox backlog triage

**1. keep-list + xlsx source swap.** Owner archived `equity_composition.json`(항목1-49) in favor of the single `IFRS17_BS.json`(항목1-7) master — `docs/agents/claude-agent-publishing.md` §1 fetch table, §9 keep-list snapshot, and §0 live-gate line updated to match; `scripts/build_master_xlsx.py:18` MASTERS entry repointed `equity_composition.json`→`IFRS17_BS.json` (sheet name `17BS` unchanged, columns 9→8 since the schema is stock-only, no `값_당분기`). Regenerated via the official `xlsx` skill after confirming with owner that the pre-existing `17BS_PIVOT` manual sheet (owner's 해약환급금준비금 hand-review) would be lost on rewrite — its correction logic was already ported into `build_ifrs17_bs.py`, so proceeded with a `.bak_20260814_prepivotloss` backup. Result: 8 cols × 1,637 rows, xlsx mtime newer than `IFRS17_BS.json`. `pytest tests/test_deploy_assets.py` 10 passed.
**Not pushed yet.** `IFRS17_BS.json` is not yet on `main`. At the time of the original report, `validate_data_contract.py` was RED=42, all `[IFRS17_BS] BS_CENSUS_MISSING_ITEM` (6 companies with partial Tier-2 face-table extraction). **Correction (re-checked same day):** a concurrent validation-lane session closed this out before this note was finalized — owner confirmed via live DART API probe (status 013/014) that those 6 companies are non-listed and file only audit reports with no XBRL attachment at all, so the extraction gap is unrecoverable; owner directed a census exemption (`IFRS17_BS_NO_SOURCE`, `BS_IDENTITY` still checked) added to `validate_data_contract.py` (`inbox/_resolved/20260814T0620Z`). **Gate is now RED=0** (YELLOW 220, one new `BS_CENSUS_NO_SOURCE_COMPANY` for visibility). §9 keep-list comment and §0 live-gate line corrected to match. Technical gate is clear; actual `main` push still needs an explicit owner GO (publishing recommends only, never executes `git push`).

**2. Inbox hygiene.** Several publishing-inbox tickets going back to 2026-06-16 had already been substantively completed (their `## 답변` sections said so, some literally writing "status: answered" in the body) but the YAML frontmatter `status` field was still `open`, or the ticket had been overtaken by later architecture changes. Reconciled against current repo state and closed out:
- Archived to `_resolved/` as genuinely done/superseded: `20260803T0743Z`(xlsx regen, prior answer verified) · `20260814T0135Z`(equity keep-list gap, confirmed superseded by this session's 0232Z) · `20260620T0859Z_skeptic_hardening_grounding`(all 4 hardening rules verified present in `claude-agent-publishing.md` §3) · `20260616T0700Z`(K-ICS inline `FORWARD_DATA` reembed — moot, superseded by the later no-inline-data-in-HTML refactor; grep confirms 0 occurrences of `FORWARD_DATA` in `K-ICS.html` now) · `20260813T0422Z`(equity_composition deploy-prep — file itself archived, superseded).
- Frontmatter synced `open`→`answered` (content already resolved, left in place per protocol since these are informational owner-instruction tickets, not archived unilaterally): `20260619T0412Z`(prepush_check chain + LLM-skeptic wiring, confirmed live in §0) · `20260620T0834Z`(코리안리/삼성화재/신한이지 5-cell owner-confirmed registry, confirmed `data/_gold/user_pl_confirmed_cells.json` exists).
- **Left genuinely open, not started**: `20260620T0859Z__gold_overlay_durable_ownerfix` — owner's request to unify all masters (not just K-ICS) onto a durable gold-overlay-as-last-build-step pattern. `## 답변` is blank; this is real unstarted architecture work, out of scope for this session without owner check-in.

---

## 2026-08-03 (2차) — inbox 처리: master xlsx 재생성 + forward baseline 키 오기 수정 (UH-7)

**1. `insurequant_master_tables.xlsx` 재생성** (`inbox/publishing/20260803T0743Z`, owner escalate → resolved). 위 배포로 마스터 JSON 4종이 갱신됐는데 xlsx가 7/30 stale이었음. 재생성 전 `data_only=False`로 전체 시트 스캔해 수식 셀 0건(=owner 수기 리뷰 formula 없음) 확인 → `.bak` 백업 → 공식 `xlsx` skill 워크플로우로 `scripts/build_master_xlsx.py` 실행(`build_csm_waterfall_master.py`는 미실행). 결과: CSM워터폴 1,962행·신계약CSM배수 327행·손익분해PL 7,799행(행수 유지, 값만 갱신). KR0004 3개년(2023/2024/2025.4Q) + KR0051 투자이익/보험금융손익 분리값을 xlsx에서 직접 read-back해 확인. xlsx는 git 미추적/keep-list 밖 — push 대상 아님.

**2. `kics_forward_capital.json` `baseline_2025_4Q` 키 오기** (`inbox/publishing/20260803T0210Z`, validation UH-7 → answered). `scripts/forward_capital_simulation.py:482`의 키가 `BASELINE_QUARTER`("2026.1Q")와 무관하게 하드코딩된 `"baseline_2025_4Q"`였음(2026-06-16 rebaseline 때 안 따라간 잔존 이름) — 데이터는 맞고 키 이름만 거짓이라 게이트는 통과하지만 다음 분기 as-of 판단 때 같은 오독을 재생산할 위험. 조치: quarter-agnostic `"baseline"` 필드 + 형제 `"baseline_quarter"`로 교체(하드코딩 연도 재발 방지), 이번 릴리스만 `"baseline_2025_4Q"` alias를 같은 payload로 병기해 하위호환 유지. 재생성 후 `validate_data_contract.py` RED=0 YELLOW=219(불변) 확인, `pytest tests/test_deploy_assets.py` 9 passed. `K-ICS.html:1090`이 이 키를 읽는 유일한 소비처(publishing은 HTML을 못 건드림) → designer inbox(`20260803T0900Z`)로 스왑 요청, alias는 designer 확인 후 다음 실행에서 제거.

## 2026-08-03 — main 배포: 마스터 JSON 4종 동기화 (`a4e8a7c..255e445`)

**배경**: 2026-08-03 capsec 체인(`184286c`·`64043fa`·`cb084e7`·`08321db`·`eea9da3`)이 작업 브랜치에만 커밋돼 있었고 라이브(main)에는 미반영. owner 지시로 배포.

**올린 것 (4개, 전부 루트 마스터 JSON — HTML/CSS는 손대지 않음)**:

| 파일 | 델타 |
|---|---|
| `CSM_waterfall.json` | KR0075 비엔피파리바카디프 CSM 단위 재정정 + KR0004 예별손해 3개년(2023/2024/2025.4Q) 18셀 신규 온보딩 (1944→1962행) |
| `NB_CSM_multiple.json` | 위 반영 재산출 (321→327행) |
| `PL_breakdown.json` | **KR0051 신한이지손해보험** 2025.4Q 투자이익 -3890.709458→-1603.902737 / 보험금융손익 0.0→-2286.806721 (부모 투자손익 -3890.709458 불변, 7799행 유지) |
| `kics_forward_capital.json` | 자본증권 소스 FSC bonds → DART 개별사채 리베이스 (38사 유지, 값 전면 갱신) |

**올리지 않은 것**: `index.html`/`K-ICS.html`/`IFRS17.html`/`공시보고서.html`/`common.css` — main과 이미 byte-identical(HTML은 designer 소관이기도 함). provenance sidecar 4종은 HTML이 참조하지 않아 keep-list 밖 → main slim 유지 위해 제외.

**절차(runbook 준수)**: ① pre-flight `validate_data_contract.py` **SUMMARY RED=0** YELLOW=219 provisional=False ② K-ICS 게이트 별도 실행 — RED=12는 전부 `TODO.md` 등재 exception(KR0087 2023.2Q ×7 · KR0097 2024.2Q ×4 · KR0079 8_life ×1, image-only)이고 `kics_disclosure.json`은 main과 diff 0이라 이번 변경과 무관 ③ keep-list를 4개 HTML의 `fetch(`/`src=`/`href=`에서 재파생 ④ **행 손실 가드** — main 버전과 신버전을 (원보험사코드,항목번호,공시분기) 키로 대조해 dropped cells 0 확인 ⑤ 격리 워크트리 `git worktree add ../insurequant-main-deploy main`, staged가 정확히 4개인지 확인 ⑥ owner 사전 GO로 push ⑦ 워크트리 제거, 작업 브랜치 복귀 확인.

**배포 후 검증(라이브 브라우저 fetch, cache-bust)**: CSM 1962행·KR0004 3분기 present·KR0075 2025.4Q 기말 299.584 / PL 7799행·KR0051 3항목 분리 확인 / NB 327행 / forward 38사. 회사망에서 `curl`은 TLS 차단으로 빈 응답 — 브라우저 경유로 검증했다.

⚠️ **정정**: 배포 커밋 `255e445`의 메시지가 PL 델타 회사를 KR0075로 잘못 적었다(실제 KR0051). main은 공개 배포 브랜치라 force-push로 고치지 않고 여기에만 정정 기록.

**후속**: `insurequant_master_tables.xlsx`가 stale(7/30 17:16 < 마스터 4종 8/3) → `inbox/publishing/20260803T0743Z__owner__MULTI__master_xlsx_regen_after_json_deploy.md`로 재생성 발주(공식 `xlsx` skill 경유, openpyxl 재저장 금지). xlsx는 keep-list 밖이라 배포 대상 아님.

---

## 2026-07-22 — main 배포: K-ICS 패널 데이터 인라인 → 외부 JSON (`a5d0ffa..8372b53`)

**올린 것 (4개)**: `K-ICS.html`(208,957→62,081자) + 신규 keep-list 3개 `kics_tier1_utilization.json`(39행)·`kics_tier2_utilization.json`(39행)·`kics_forward_capital.json`(38행). 배경·근거는 cross-stage changelog 2026-07-21 리팩토링 2차 B 항목.

**절차(runbook 준수)**: ① pre-flight `validate_data_contract.py` **SUMMARY RED=0** ② keep-list를 HTML의 `fetch(`/`src=`/`href=`에서 재파생(기억 아님) ③ **main과 내 브랜치의 K-ICS.html 차이가 내 변경뿐임을 확인** — designer a5d0ffa a11y 작업을 되돌리지 않음을 push 전에 검증 ④ 격리 워크트리(`git worktree add --detach origin/main`), 같은 폴더 checkout 바꿔치기 안 함 ⑤ 워크트리 staged가 정확히 4개 파일인지 확인 ⑥ **배포될 그 워크트리를 직접 서빙해서** 헤드리스 검증(ALL PASS) ⑦ owner GO 후 push.

**배포 후 검증**: 3개 JSON 200(26,265 / 25,080 / 131,747 bytes), 라이브 `K-ICS.html` 69,045 bytes·인라인 블롭 0, 라이브 브라우저에서 패널 39/39/38 적재·자본도넛 실수치·forward 렌더·**콘솔 에러 0**.

⚠️ **이후 K-ICS.html을 배포할 때 이 3개 JSON은 항상 동반**해야 한다. HTML만 올리면 자본도넛·forward가 **에러 없이 빈칸**이 된다. `tests/test_deploy_assets.py`가 4개 페이지의 로컬 fetch/link 참조 존재를 강제하므로, 배포 전 `pytest tests/test_deploy_assets.py`를 keep-list 파생의 기계적 확인으로 쓸 것.

---

## 2026-07-22 -- designer A11y color fixes + treemap revert, deployed to main via launch runbook

Feature branch (`fix/csm-product-segmented-columns`) had two uncommitted-then-committed designer
changes sitting ahead of `main`: the A11y owner-review-queue color/contrast fixes
(`docs/changelog_designer.md` 2026-07-21d, commit `2e4f114`) and a same-day-plus-one revert of the
treemap red→blue swap after owner flagged it broke an intentional finviz.com-style market-map
identity (commit `6fc34c1`). Ran the newly-adopted `docs/launch_runbook.md` procedure end to end for
the first time on designer-only output (no master JSON changes involved).

- **Pre-flight**: `python scripts/validate_data_contract.py` → `SUMMARY RED=0` (YELLOW=200, existing
  triage queue, non-blocking).
- **Shared-tree check**: `git branch --show-current` + `git status` before touching anything — found
  an unrelated concurrent session's staged changes (`schemas/kics_data.schema.json` deletion,
  `src/solvency/legacy/*` removal, `scripts/run_harness.py`/`src/solvency/config.py` edits). Did
  **not** stage or commit any of it — `git reset` (index-only, no working-tree impact) to unstage,
  then re-staged only the designer files. That session went on to commit its own work cleanly
  (`0543414` etc.) with no interference either direction.
- **Isolated worktree cherry-push**: `git worktree add ../insurequant-main-deploy main` (after
  fast-forwarding local `main` to `origin/main`, which already had an earlier a11y sync `8e8c01d` —
  the keyboard-access/aria-label batch, not the color batch) → `git checkout
  fix/csm-product-segmented-columns -- index.html K-ICS.html IFRS17.html common.css` → verified
  `git status`/`git diff --cached` showed exactly those 4 files and nothing else → committed
  (`a5d0ffa`).
- **Owner GO**: presented the 4-file list + 1-line reason each + gate result in chat; owner confirmed
  ("push 고고") before `git push origin main`.
- **Live verification**: polled `common.css` for the active-tab underline (propagated ~15-30s after
  push, GitHub Pages), then confirmed all 4 files' specific changed values live via curl —
  `K-ICS.html` placeholder gray, `IFRS17.html` `NB_LINE_COLORS`, `index.html` bubble-legend green,
  and confirmed `index.html`'s treemap `hue` is `0` (red) in both branches, not `215` — the revert
  is correctly live, not just on the feature branch.
- **Cleanup**: `git worktree remove ../insurequant-main-deploy`, confirmed clean return to the
  feature branch (`git status` clean of tracked changes).
- **Not deployed** (intentionally out of scope): the concurrent session's `src/solvency/legacy`
  removal / `schemas/` change — backend-only, not a site asset, not touched by this deploy.

## 2026-07-21 -- provenance sidecar 3종 발행 + 게이트 로더 버그 수정 + launch runbook 신설

Inbox 드레인 (`inbox/publishing/`): validation의 UH-3 후속(`20260721T0530Z`) + owner의 런북 발주
(`20260721T0233Z`), 둘 다 `status: answered`/`resolved`. 겸사겸사 오래 미커밋 상태였던 IBK(KR1011)
스레드(`20260704T0600Z`, 실제 배포는 `7bf0d60`으로 이미 완료돼 있었음)도 xlsx 재생성 확인 후 종결.

### Provenance sidecar 발행 (forward_capital · tier1/tier2_utilization)

`templates/{forward_capital_latest,tier1_utilization_latest,tier2_utilization_latest}_provenance.json`
3종 신설 — `--print-provenance-contract` 스키마 그대로: `source_id=FSC_BONDS`, `effective_filtered=true`,
`as_of_date=2026-03-31`(=2026.1Q). source_file은 각 마스터가 **실제로** 읽는 파일로 정확히 매핑:
- forward_capital → `data/bonds/normalized/20260616T060817Z/bonds_by_insurer.json` (forward manifest의
  `bonds_source`와 동일 스냅샷).
- tier1/tier2_utilization → `data/bonds/capital_securities_fy2025.json` (DART per-bond 발행현황;
  `wire_capital_securities_to_utilization.py`가 이 파일의 `call_date`/`legal_maturity` 기준
  `is_grandfathered`/`amort` 효력필터를 실제로 적용함을 코드 리딩으로 확인한 뒤 `effective_filtered=true`
  기재 — 상위 `compute_tier{1,2}_utilization.py`는 이 필터를 안 하는 구버전이라 혼동 주의, 2026.1Q
  산출물은 `wire_*` 스크립트가 in-place 갱신한 버전).

**버그 발견 + 수정 (발행만으론 안 잡혔을 뻔)**: `Env.MASTER_FILES`(`validate_data_contract.py`)에
`forward_capital`이 `forward_capital_latest`라는 다른 키로 등록돼 있어 `check_as_of`의
`sidecars.get("forward_capital")`과 영원히 매칭이 안 됐고, `tier1_utilization`/`tier2_utilization`은
그 dict에 항목 자체가 없어 사이드카 로드 경로가 없었음 — 3종 다 발행해도 게이트가 못 찾는 상태.
`MASTER_FILES` 3개 키를 lookup 이름과 맞춰 수정/추가.

**검증**: `--selftest` 14/14 유지(회귀 0). 게이트 `MISSING_PROVENANCE_SIDECAR` YELLOW 4→**1**
(잔여 sensitivity_heatmap = parser ifrs17 별도 소관, 원 티켓 스코프 밖). RED=0 불변.

### Launch runbook 신설 (owner 발주 `20260721T0233Z`)

`docs/launch_runbook.md`(정본 절차서) + `.claude/skills/launch-runbook/SKILL.md`(로컬 skill) 신설.
Pre-flight 게이트 → keep-list 재파생 → 격리 워크트리 cherry-push → owner 승인 지점 → 배포 후 검증 →
**§6 rollback(신규 — 이전 TBD)**: HTML/JSON은 격리 워크트리에서 `git revert`(force-push 금지), 마스터
xlsx 손상은 `.bak` 복원 → Excel 재오픈 → `build_master_xlsx.py` 최후수단 순. `claude-agent-publishing.md`
§8 TBD 3건(branch policy·site-deploy hook·rollback contract) 체크 완료 + 링크. **로컬 skill 채택**
(외부 미도입) — 이 저장소에 이미 로컬 skill 패턴(a11y-audit·incident-postmortem) 존재 + 절차가 이
저장소의 공유 워킹트리·slim keep-list·K-ICS 별도게이트 함정에 강결합돼 범용 외부 스킬로는 못 담음.
**이번 발주로 실제 배포는 실행 안 함**(지시대로 문서화만).

### 2026.1Q 적용후 요구자본 fill — 배포 확인 결과 이미 라이브 (중복 push 없음)

`inbox/publishing/20260716T0330Z`(validation) — 2026.1Q 5개사(한화생명·교보·하나·롯데손해·농협)
적용후 요구자본 fill을 main에 반영할지 owner에게 질의 → **"지금 배포 진행"** 승인. 착수 전
`git fetch origin main` + `kics_disclosure.json` 정규화 전체 대조(18,878 레코드) → **diff 0** —
다른 세션이 이 사이(`25d8e98` 2026-07-16 · `1c9ebdc`/`8e8c01d` 2026-07-21) 이미 라이브에 올려둠.
**push 실행 안 함**(중복 배포 스킵), 스레드 resolved.

### 미착수 (다음 세션 트리아지 필요)

`inbox/publishing/`에 `status: open`으로 남아 있는 2026-06-16~20 backlog 5건 — 이번 세션에서 손대지
않음(스코프 밖, 오래된 항목이라 이미 다른 경로로 해소됐을 가능성도 있어 트리아지 우선): reembed-done
트리거·prepush 체인 문서화·owner-confirmed registry 분쟁 3건·gold-overlay 통일·skeptic 하드닝.

---

## 2026-06-17 -- push BLOCKED (data-contract RED=52) + 게이트 #0 와이어링

### 게이트 #0 data-contract 신설 (owner 정책 2026-06-16 12:44)

owner 정책 확정: **"RED 1건이라도 있으면 push 안 한다."** — documented-exception 우회 불가, fixable RED은 고쳐서 0으로.

- `claude-agent-publishing.md` §3 #0 gate 명문화: `validate_data_contract.py` exit 2 = BLOCKED, exception 없음.
- 현재 라이브 RED=52 (CHECK2 sensitivity_heatmap FY2024 stale = V12 parser refill 대기 + CHECK1 census 30).
- owner inbox `1242Z` + validation inbox `1254Z` 모두 resolved.

### push 대기 중인 변경 (main에 미반영)

designer 트리거(`1300Z`) 수신. 다음 배포 후보 변경이 feature branch에 파킹됨:
- K-ICS.html: FORWARD_DATA 2026.1Q 재임베드 + Baseline 라벨 (designer)
- IFRS17.html: common.css 채택 + WF_Q_WINDOW=5 + PL 워터폴 zero-crossing fix (designer)
- CSM_waterfall.json: continuity RED 8→0 교정
- PL_breakdown.json: 기타사업비용 item16 0처리 (KB손해 13Q, 흥국화재 6Q, KDB 1Q)

**push 재개 조건**: `validate_data_contract.py` exit 0 (sensitivity_heatmap V12 parser refill 완료 후).

### 자본성증권 소스 조사 완료 (downloader 1300Z + parser 1305Z)

- KDB생명(KR0072) 신종 DART 2,410억 ≈ BS 2,403억 ✓ 확인.
- 현대해상(KR0009) 후순위 FSC 26,000억이 정확, BS 3,766억 = 파서 오파싱 → parser(kics) 재파싱 발주(`1530Z`).
- 농협생명(KR0104) 신종 DART/FSC 5,000억, BS=0 = 파서 누락 → parser(kics) 재파싱 발주(`1530Z`).
- 흥국화재(KR0005) per-bond: 신종 4,120억(≈BS), 후순위 3,200억(Face=gross, BS=경과조치 인정분).
- 사모채 7사(삼성생명·악사·하나손해·AIA·삼성화재·KDB후순위·교보): 공개 소스 없음, forward-sim BS 총계 단순가정 유지.
- forward_capital_simulation 재실행: parser KR0009/KR0104 재파싱 + data-contract gate clear 후 예정.

---

## 2026-06-16 -- 배포 `99fb923..dbbb096`: common.css 디자인시스템 + 2026.1Q site refresh

owner 승인 push("오늘까지 작업본 + designer common.css 같이"). origin/main 배포(7파일, worktree on main → fast-forward, rebase 불요·origin==local 99fb923).

- **common.css** (신규 배포에셋): 디자인시스템 단일소스(토큰+chrome+A11y), index/K-ICS/IFRS17.html 3개가 `<link>` 참조 → **HTML과 반드시 동반 배포**(누락 시 스타일 붕괴). designer frontend-design skill 산출물.
- index.html(92)/K-ICS.html(31)/IFRS17.html(156): common.css 추출 + 렌더수정. kics_disclosure.json(4700, 예별 13Q 백필). kics_rate_sensitivity.json(294)·sensitivity_heatmap.json(144) refresh.
- **게이트**: K-ICS `validate_kics_disclosure.py` RED=24 **전부 documented**(TODO.md 36-96: 36_irr 12·19_market 7·예별 KR0004 rule1·AIA·micro 등) + census MISSING=6 documented(image-PDF OCR). 충족.
- **continuity break**(전기말 CSM≠당기 기시): owner가 **내일(6/17) 수정 deferred**. 이 배포의 CSM waterfall 데이터(CSM_waterfall.json + data/dart/viz/csm_waterfall*.json)는 **live와 동일=델타 밖** → 배포가 악화 안 시킴. 이미 parser 작업중(validation `csm_2026q1_opening_misparse` + downloader `csm_continuity_raw_ready`).
- **미반영(후속)**: K-ICS.html `window.FORWARD_DATA`는 아직 구 베이스라인 — 2026.1Q forward 재임베드는 designer 대기건(`inbox/designer/20260616T0605Z`, JSON 준비완료). 다음 push에 반영.
- ls-remote 확인 origin/main=dbbb096. worktree 제거, feature 무손상.

## 2026-06-16 -- Forward-capital 2026.1Q 재베이스라인 + (a) T2-디커플 신뢰도 산식

parser-kics 발주(`inbox/publishing/20260616T0600Z`, owner QA 후속). owner가 신뢰도 산식 **(a) T2 디커플** 선택. `forward_capital_simulation.py` 두 파트:

- **재베이스라인**: `BASELINE_QUARTER` 2025.4Q→2026.1Q, `TIER{1,2}_JSON`→_20261Q(parser 산출분), `BASELINE_YEAR` 2025→2026(as-of 2026-03-31 — 경과조치 phase-out 램프 앵커링, 2026.1Q post값의 ~1년 run-off 이중계상 방지). Face=`_latest_bonds_dir()` 자동 픽 clean 스냅샷 `20260616T060817Z`(카카오페이 Face=0·KB라이프 1,200억 반영).
- **(a) T2 디커플**: `_overall_bucket(t1_bucket, t1_real_error, t2_hard_error)` 재작성 — overall=T1 reconciliation 기준, T2 Face(FSC outstanding)-vs-BS(grandfathered issued) 개념차는 advisory(overall 안 깎음). 진짜 오류만 hard-low: T1/T2 한쪽결측 + t2_util>100%. 불변식 검증 통과(low 21건 전부 진짜 사유, T2 개념차 단독 low=0; 분해 fsc_missing_t2 10·T1gap 4·kics_missing_t1 4·util>100 3). **T2 개념차 false-low 8개사 구제**. dist high=15/med=2/low=21(구 22/37).
- **경계**: 스크립트에 `--no-html` 플래그 신설 → publishing은 JSON만(`templates/forward_capital_latest.json` + `output/.../20260616T063704Z/forward_simulation_v3.json`), K-ICS.html `window.FORWARD_DATA` 재임베드는 **designer**(handoff `inbox/designer/20260616T0605Z` blocked→open 전환). 스키마 불변(level/t1_gap_pct/t2_gap_pct). forward JSON은 slim keep-list 비대상 → **push 없음**(사이트엔 designer inline 임베드로만 반영). parser 스레드 resolved→`_resolved/`.

## 2026-06-16 -- publishing 프롬프트 내부모순 정리 (MD 감사 후속)

owner 발주(`inbox/publishing/20260616T0514Z`). `docs/agents/claude-agent-publishing.md` 3건 surgical 수정:
1. **헤더↔§5 모순 해소**: 옛 문장 "Subagent prints these... does **not** execute them" 삭제 → 헤더(L5)·§1 hard-rule(L36)·§9(L201)와 일치하는 "agent runs local git itself; only outward `git push` is gated"로 교체.
2. **§3 "gathering scripts" → "assembly/build scripts"** (죽은 stage명 정정, 문서 내 잔존 0 확인).
3. **(선택) §1 경로 주석**: 표 아래 §9 "Pending path migration" cross-ref 한 줄 추가(`data/dart/viz/*` post-migration canonical vs 라이브 `main` `data/ifrs17/viz/*`). 경로 자체 미변경.

검증: UTF-8 no BOM·깨진 한글 없음·grep 정합. 배포 없음(docs/agents = IP, slim keep-list 비대상). inbox answered.

## 2026-06-16 -- V7(NB_CSM_DART_VS_IR) gate enforcement 조사: publishing 차단 미배선 확인

owner backlog 🟠-6(`inbox/publishing/20260612T0900Z`) 위임. **결론: NB_CSM_DART_VS_IR RED는 publishing 어셈블을 차단하지 않음 — 전용 차단 로직 미배선. 단 publishing 코드 갭 아니라 validation 측 배선 갭.**

3층 전수 확인:
1. **어셈블 `build_root_masters.py` = 검증게이트 전무** — diag 소스→루트 마스터 무조건 transform(owner override + unit-cap만). validation 결과 미참조 → RED여도 빌드. (설계상 정상: V7 severity="RED→DART parser loopback", 교정은 parser 소스에서.)
2. **V7 미집계** — 도구 `check_nb_csm_widespread.py`·`check_nb_csm_history.py` **소스 둘 다 부재(.pyc만 잔존)**, 파이프라인 미호출, `validate_master_tables.py` 미포함, `validation_report*.json` 0건.
3. **publishing 게이트는 generic·절차적** — §3.1/Hard-rule/exit-table = "validation subagent report `summary.red==0` per domain → else BLOCKED". V7가 그 리포트에 surface되면 **이미 차단됨**. 결손은 V7 자동집계뿐.

판정·조치: 전용 V7 publishing 게이트 **신설 비권장**(parser-loopback 설계 + V1으로 retire 예정). enforcement 지점은 generic 게이트로 충분 — V7를 validation 리포트에 올릴지/도구 소스 복원/retire는 **validation 소관**이라 inbox 발주(`inbox/validation/20260616T0100Z__publishing__MULTI__v7_gate_enforcement_findings`). publishing은 무코드(pre-push 체크리스트 1줄: IFRS17 RED 시 V7 7사 cohort 포함 확인). 현재 V7는 parser 교정 중(롯데 FY2025 P1 / off-by-one history P2).



owner 발주(`inbox/publishing/20260616T0043Z`): Anthropic 공식 `xlsx` skill을 publishing master xlsx 작업의 **상시 디폴트 도구로 즉시 채택**(별도 평가 없이). 발주 시점에 마침 재생성 룰 발동 → #1 대상으로 첫 적용.

- **트리거**: 오늘 배포한 master JSON 2건(`kics_disclosure.json`·`kics_rate_sensitivity.json`, 둘 다 6/16)이 기존 xlsx(6/15)보다 최신 → `feedback_rebuild_master_xlsx` stale 룰 발동.
- **조치**: `xlsx` skill 워크플로우 하에 `scripts/build_master_xlsx.py` 실행. skill 원칙 "Existing template conventions ALWAYS override" → 기존 컨벤션(맑은 고딕·헤더 305496·`#,##0.##;(#,##0.##);-`) 유지, 표준화 강제 안 함.
- **결과**(7시트): 요약 + K-ICS공시 17,197 · 금리민감도 516 · CSM워터폴 **1,926** · CSM상각 290 · 신계약CSM배수 321 · 손익분해PL 7,727. read-back 한글 무결, 정적값(수식 0)이라 recalc N/A·formula 에러 불가.
- **금지선**: `build_csm_waterfall_master.py` 미실행(CSM워터폴 1,926행 유지로 입증 — raw purge 브랜치 붕괴 회피, 메모리 `project_git_purge`). 멀티라인 인라인 `python -c` 미사용.
- **배포 없음**: xlsx는 untracked 빌드물(리뷰어용), slim keep-list 비대상 → push 불요. backlog `🔴-3` 종결. inbox `xlsx_skill_adoption` answered.
- 적용대상 #2(리뷰루프 I열 재계산)·#3(gold xlsx 게이트)는 발생 시 skill 적용 예약. 분담 불변(diag→parser inbox, 데이터 도메인 오류→parser 바운스).

## 2026-06-15 -- Forward sim: 신종자본증권 tier-priority deduction (T2→T1)

owner 발주(`inbox/publishing/20260615T0435Z`). `forward_capital_simulation.py` 채권 차감부를 tier 우선(보완자본 먼저→기본자본) 으로 교체. 별도 순서분기 없이 매 시점 재계산:
- `HYBRID_LIMIT_RATIO=0.15` (신종/조건부=SCR×15%, 규정 다.(1)). `limit_y=scr_y×0.15`, `H_y=total_hybrid−누계신종call`.
- `basic_y = basic_baseline + (min(H_y,L_y) − min(H_0,L_0))` → 신종 call이 H를 줄여도 H≥L인 동안 기본자본 불변(초과분=T2에서만 차감), H<L부터 기본자본 감소. 후순위채는 총자본만 차감(기본자본 불변, 유지).
- 출력 진단필드 추가: hybrid_remaining/tier1/tier2_overflow/limit_eok.

검증(KR1000): 2027 신종 3,300억 call → 기본자본 35,582 불변(T2만), 2028 초과분 소진 후 기본자본 34,550으로 하락 = **T2-first 확인**. 빌드 37사 ok → `forward_simulation_v3.json`(20260615T050803Z) + `templates/forward_capital_latest.json` + K-ICS.html `window.FORWARD_DATA` 동기화. **K-ICS.html 배포는 owner GO 대기.**

## 2026-06-14 -- Slim-publish deploy: IFRS17/K-ICS designer fixes + sensitivity heatmap (option B)

origin/main 배포 (`25a329d..d45ebd5`, 3파일). **kics_disclosure.json 보류**(K-ICS 게이트 RED>0: 36_irr×11 등 미문서화 — validation/parser 트리아지 대기). master JSON + HTML만.

- IFRS17.html (현대해상 #FFB81C, ΔCSM 억원 헤더, 모바일 패딩), K-ICS.html (드롭다운 누락사 fillMissingCompanies), data/dart/viz/sensitivity_heatmap.json (흥국/푸본현대 정정+단위정규화).
- 절차: main이 이미 slim(17 site assets, data/dart/viz 경로 이전 완료) 확인 → §9 대량삭제 dance 불필요. **git worktree**로 main 체크아웃(피처 워킹트리 동시쓰기 충돌 회피, §8b 권장). origin/main이 앞서있어(미purge 이력) **force-push 대신 rebase**로 fast-forward. local main(purge본)은 force-push 안 함.
- tier1 100% 캡 수정은 K-ICS.html이 `window.TIER1_DATA` inline+JS캡이라 사이트 미영향(내부 정합성용), keep-list 아님 → 미배포.
- 라이브 검증(raw curl): K-ICS.html fillMissingCompanies✓, IFRS17.html FFB81C+ΔCSM(억원)✓, sensitivity_heatmap.json 200/48KB✓.

## 2026-06-14 -- Tier-1 hybrid utilization 100% cap (glitch G2 resolution)

9개사 2025.4Q tier1(기본자본 신종자본증권) 소진율 >100% (코리안리 242.5%, NH농협손해 187%, 교보 171% 등). 진단: 규정(K-ICS 해설서 [별표22] Ⅲ.2.다.(1)) 상 신종 한도(SCR×10%, 조건부자본증권 15%) 초과분은 보완자본 자동 재분류 → 소진율 정의상 ≤100%. >100%는 Ⅴ.1 재분류액(excess) 파싱누락 artifact. parser-kics 회신: standalone Ⅴ.1 행 9사 전부 부재(번들 "…초과한 금액 **등**" 행으로만 공시). 번들값 검산상 신종 한도초과분과 40배 차이(번들="등" 기타항목; 신종초과분은 공시 보완자본에 직접 반영, 라.(1)).

owner 결정: **소진율 100% 캡(옵션 2/3)** — tier2 cascade는 공시 보완자본 이중계상이라 미채택.

- `compute_tier1_utilization.py`: `utilization_pct=min(recognized/limit,1.0)*100` 캡(util_strict 동일) + 신설 필드 `tier1_hybrid_overflow_eok=max(recognized−한도,0)`(보완자본 재분류분 명시, 예: 코리안리 4,749억). definition에 `utilization_cap` 주석.
- 9사 util15 → 전부 100.0, util>100=0건. `templates/tier1_utilization_latest.json`(K-ICS.html 리더) 갱신.
- **무변경**: compute_tier2/forward_capital_simulation(cascade 미채택), K-ICS.html(line 816 Math.min 캡 그대로=안전망, designer 도메인). designer XXX%+ 도넛 구현 보류 확정.
- inbox 종결: parser `tier1_hybrid_excess_unparsed`(blind_spot, resolved), owner `tier1_overflow_cascade`(resolved) → `_resolved/`. designer 스레드 재통지(예외 없음).

## 2026-05-31 -- Publishing stage created (merge of gathering + pushing)

User decision: parser+validation are the "real" pipeline; gathering+pushing are mechanical follow-up to those. Merged into one **publishing** stage with two responsibilities: (1) assemble validated per-source JSON into HTML-ready masters, (2) report changes + recommend commit/push commands (human still runs `git push`).

- Combined prompt: `docs/agents/claude-agent-publishing.md` (replaces `claude-agent-gathering.md` + `claude-agent-pushing.md`, both deleted).
- New TODO/changelog created from root TODO items: F4 v2 / F13 / INDEX-IFRS17-BUBBLE / INDEX-BUBBLE-V2 / MISC-IR-NB-DENOM (publishing side) / MISC-IR-PROTOTYPE / IFRS17-CSM-BUBBLE.
- Done archive imported: KICS-TIER1/2-UTIL / KICS-FORWARD-CAPITAL / IFRS17-HTML-DASH / F17 Panel 3 data / F5 / F6 data side / F1 cross-nav data hook.
- Hard rule retained from pushing: this stage **reports + recommends only**, never runs `git push`.
- Hard split with designer: publishing owns master JSONs; designer owns HTML. If a new master field needs HTML rendering, publishing reports `manual_html_edit` warn and stops — designer takes over.

---

## 2026-05-30 -- Forward sim v3 deployed + bond tier `(신종)` fix data refresh

**Forward sim v3 (`20260525T061947Z`):** confidence high **5** (+1). KR0032: `fsc_missing_t1` cleared, T1 gap 0%; still **low** on T2 face vs BS (over_deduct). KR0104: **high**. KR0072: **`fsc_missing_t1` remains** — FSC has only **called** tier1 (700억); BS still shows 2403억 outstanding 신종 (not in FSC outstanding cohort).

**Weak capital (document only, no "fix"):** KR0003 Lotte basic_cap **-3875**억 / basic ratio **-23.7%**; KR0072 KDB basic_cap **-3311**억. User-confirmed real stress, not parser error.

(Bond normalize itself = downloader; this entry is the publishing-side refresh that consumed it.)

---

## 2026-05-30 -- F17 Panel 3 clean 4-bar swap (data side)

`scripts/build_net_income_breakdown.py` → `data/dart/viz/net_income_breakdown.json`. Tier1 10/10 손보 OK. Panel 3 (IFRS17.html) swapped from raw-table-last-column 12-row horizontal bar dump to clean 4-bar 당기순이익 decomposition (보험손익 / 투자손익 / 영업외 → 당기순이익). 보험금융 + 보종별 caption.

Designer swapped HTML; publishing owned the JSON shape.

---

## 2026-05-28 -- IFRS17 yearly CSM amort F6 (data side)

`viz_build_ifrs17_panels.py`: `extract_amort_schedule` now emits `yearly` (y1..y10 + y10plus + total) and `granularity` alongside the existing 4-bucket `buckets` (kept — `viz_build_ifrs17_kpis.py` + bubble still read buckets). New helpers `_year_bucket_cell` / `_year_bucket_indices` / `_yearly_from_aligned` / `_extract_transposed_yearly`. `granularity='yearly'` only when >=7 of y1..y10 present.

Split: **16 yearly / 6 coarse / 2 no-data** (of 24); 22/24 ok unchanged.

(HTML panel 2 swap = designer 2026-05-28.)

---

## 2026-05-25 -- IFRS17 CSM 시계열 panel 6 data buildout (assembly side)

Stage 3 of the IFRS-HIST pipeline (stages 1+2 = downloader/parser):

- `viz_build_csm_waterfall_history.py`: reuses `pick_main_block` + `extract_stages` + `detect_unit_scale` from FY-only viz builder. Aggregates per-(insurer, period) snapshots into time-series payload.
- Coverage 20 → **257 ok + 2 partial** out of 299 reachable after measurement promote.
- Output: `data/dart/viz/csm_waterfall_history.json` (319KB, 23 companies × 13 periods).
- IFRS17.html Panel 6 data wiring: dual-axis line, 기말 CSM solid + 신계약 CSM dashed, 22 background lines (회색 spaghetti).
- nulls for `no_csm_block` periods (spanGaps: false) — visible as gaps in HTML.

Push #2 deployed: commit e846e5a (6 files, 9271 insertions). data file 200 OK at 319KB at https://solvencyk.github.io/insurequant/data/dart/viz/csm_waterfall_history.json (now path; previously templates/).

---

## Older entries

Pre-2026-05-25 publishing/gathering/viz entries are in the compressed historical archive of root `docs/claude-changelog.md` ("## Historical archive (compressed)"):

- IFRS17 CSM Waterfall picker (5 no_csm 손보사 → 0, MVP filter off, ceded penalty)
- K-ICS.html Phase 4 (자본성증권 도넛 + Forward Outlook 라인)
- Forward sim v2 (confidence per-row, capacity_exhausted cap)
- KICS-FORWARD-CAPITAL Phase 3 v1 (yearly × 5y, 19사 cohort)
- Bond calendar v3 (5y Call rule for ALL bonds, 3-status outstanding/called/matured)
- FSC schedule API per-insurer full pull (publishing-side normalize)
- HTML single-source refactor P1+P4 (cross-cutting refactor; designer side too)
