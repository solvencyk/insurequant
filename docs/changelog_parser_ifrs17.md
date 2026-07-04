# Parser Changelog — IFRS17 lane (Stage 2)

> Last updated: 2026-07-04 · Stage 2/5 — parser (ifrs17 lane)
> Prompt: docs/agents/claude-agent-parser.md (shared) + docs/domains/claude-agent-ifrs17.md · TODO: TODO_parser_ifrs17.md

IFRS17 extraction history: DART body XML → CSM_waterfall / PL_breakdown / NB-CSM-multiple masters.
Code: `src/ifrs17/` (csm / measurement / insurance_pl / reinsurance / bs_snapshot / sensitivity extractors +
`scoring.py` config layer). Validators: CSM golds, PL golds, csm_waterfall / pl_bridge crosscheck.

**Pre-split combined history (before 2026-06-13): [`changelog_parser.md`](changelog_parser.md)** (frozen).
Convention: see [`docs/agents/doc-style.md`](agents/doc-style.md).

## 2026-07-04 — IBK연금보험 KR1011 신규 온보딩 (CSM + PL + viz 전파)

- **universe.py**: IBK연금보험을 `NON_LISTED_SKIP`에서 제거 → `AUDIT_REPORT_ANNUAL`에 추가. DART 감사보고서 F형 라우트.
- **ifrs17_ingest_audit_annual.py**: `NAME_ALIASES` 적용 (IBK연금보험 → 아이비케이연금보험 DART 검색).
- **CSM_waterfall.json**: 3개년 18레코드 hand-assemble (measurement block0 당기 whole-book, 천원→억원). closure/continuity 3중 검증 통과. waterfall viz partial (newbiz 스테이지 누락 — parser 추가 대응 필요).
- **build_pl_breakdown.py 4패치**: IBK 라벨 변형 처리 — `NI_LABELS`+당기순손익, `_is_income_statement`+영업손익, `extract_tier1` ni_raw+op 확장.
- **_GOLD_CELL_OVERRIDE KR1011 3개년**: notes [166][167] (보험수익/보험서비스비용 내역) 직접 계산. item3=보험수익합계−서비스비용합계, item4=CSM상각, item5=RA변동, item6=예실차(예상−실제), item7=잔차(손실부담계약). closure 5종 Δ=0 전부. item8-12=0(재보없음), 13-14=0(자동차/일반없음).
- **viz 전파 재빌드**: sensitivity_heatmap(27/32), csm_amort_schedule(28/30), insurance_pl_breakdown(29/29), csm_waterfall(47 total), csm_bubble, downstream_kpis, earnings_quadrant.
- **publishing inbox**: `20260704T0600Z__parser_ifrs17__KR1011__ibk_masters_ready.md` 발송.

---

## 2026-06-20 — owner-fill durability · capital securities · CSM continuity (교보/삼성) · provenance
- **Owner xlsx fill durability (0811Z):** owner가 root에 sync한 fill을 빌드 소실서 보호. PL은 override 레이어가 없어 신규 **`data/dart/viz/pl_manual_overrides.json`** + `build_root_masters._apply_pl_overrides`(_zero_other_expense 後) 도입(121셀). CSM 10셀(AIG손해 2025.4Q 6·하나손해 이자부리/조정 4)→`csm_manual_overrides.json`. 재빌드=owner root 값 정확 재현(값 변경 0 검증). 현대해상 26셀 estimate 플래그.
- **자본증권 발행잔액→한도소진율 (0238Z, owner):** 24사 DART 사업보고서 자금조달/사채/신종 주석 per-bond 추출(발행일·법만기·**콜(=실효만기 5y)**·금액·잔액) → `data/bonds/capital_securities_fy2025.json` + 정식 `data/dart/capital_securities_issuance.json`(신종→Tier1·후순위→Tier2·provenance). `wire_capital_securities_to_utilization.py`로 tier1/tier2_utilization 분자 라이브 교체(**경과조치 pre-2023 별도제외**=owner 결정) + 신한이지 분모 SCR×50% 교정 → **data-contract gate RED 4→0**(동양240%/KB218%/미래126% proxy + denom). forward outlook=콜 roll-off(`capital_securities_forward_outlook.json`), 흥국식 콜경과 예외 플래그. census: 보유25/무발행11(삼성화재·삼성생명·외국계). NB: as_of 2025.4Q(2026.1Q raw 5사만→콜 reconcile), 푸본 후순위 발행일 estimate.
- **CSM continuity 정정 (0600Z 교보 / 0545Z 삼성):** 교보 2023.4Q 기말+2024.1Q/2Q 기초→58,249.2(재작성 통일, FY2024 rollforward 확인), 삼성 2023.4Q 기말 123,926→122,474(owner gold). item4(가정조정) 흡수로 identity 유지. csm_manual_overrides. **validate_master_tables cont 6→0**, 8셀만 변경·무클로버.
- **Provenance 사이드카 (1242Z-B/1252Z):** `emit_ifrs17_provenance.py` → `CSM_waterfall_provenance.json`(321)·`PL_breakdown_provenance.json`(632), source_id=DART+item_block, owner_override/estimate 플래그.
- **진단(미해소, open):** nb_csm 0420Z=8/30 회수·22 interim §14 추출기갭. sensitivity 3 partial(미래에셋 OCR·신한라이프 prose·한화손해 시장위험형)=자동복구불가. 한화 CSM 상각스케줄 1029Z=form_type unknown 추출갭. 삼성화재 자동차손익 2026.1Q=-40=owner 확인 정답(pass).

---

## 2026-06-16 — CSM 워터폴 continuity 전사 RED 8→0 (2026.1Q 기시 misparse + within-FY drift)

owner 직접 검증 + validation `20260616T0605Z`/downloader `20260616T0640Z`. `validate_csm_continuity.py` **RED 8(7사)→0**.

**근본원인** = `build_csm_waterfall_master`의 product-set 합산 버그(missing raw 아님 — 재추출이 committed 동일 misparse
재현). 당기 발행(원수) 유배당+무배당+변액 sub-table을 부분만 집거나 전분기 copy 혼입:
- **2026.1Q 5사** 기시(검증 워크플로우 9사 병렬, raw 후보블록 재구성): 푸본 1669.3→**1906.5**(유212.1+무1669.3+변25.1),
  메리츠 111893.5→**111037.0**(전분기 copy 제거), 신한 74422.9→**75537.3**, 에이비엘 9229.7→**9702.5**, 교보 70768.8→
  **65109.6**. 전부 = 직전 2025.4Q 기말(owner 검증).
- **within-FY drift**: FY2023(현대 88281.1·에이비엘 7017.8·KDB 5239.4·교보 46967.3)·FY2024(KB라이프 30176.4·코리안리
  8031.5) 기초 상수화. drift 원인 = 소급재작성(연중 기초 재공시) 또는 전기 copy.

**수정(비파괴)**: `build_csm_waterfall_master.py` 미실행(파괴적). 검증값을 `data/dart/viz/csm_manual_overrides.json`
'set'(+62) 인코딩 → `build_root_masters.build_csm()`(diag+override 공식 재조립, 값_당분기 정식 재계산). **durable**.
감사기록 `data/_derived/csm_continuity_corrections.json`. identity 무파손(15셀), within-FY 상수·FY경계 연속 검증, pytest 110.
⚠️ 다운스트림 viz(csm_bubble/NB_CSM_multiple/history/diag)·근본 파서 수정은 raw 복원 세션(별track).

## 2026-06-16 — designer/validation 후속: sensitivity period/as_of + NB-CSM partial sweep

**A. sensitivity period/as_of** (designer `20260616T0030Z`): `sensitivity_heatmap.json` entry가 rcept_no만 있고
`period`/`as_of`=null이던 것 → `viz_build_ifrs17_panels.py` `build_panel`에 `_period_asof_from_rcept` 추가
(`add_as_of` 플래그로 **sensitivity 패널만**) → 27社 FY2024/2024-12-31, 흥국 FY2025/2025-12-31. scenario 무변경,
타 패널 3종 byte-identical, pytest 110. designer `asOfFromRcept` fallback과 동일 규약(rcept 제출월).

**B. NB-CSM partial 오염 sweep** (validation `20260616T0230Z`): `csm_waterfall_history.json` non-ok **41 cells**
census(no_csm_block 29·partial 6·no_extract/empty/download_error 6). **partial 6건**(롯데 2025.2Q NB=0·미래에셋
2025.2Q/3Q·한화생명/현대해상 2025.2Q·삼성화재 2023.1Q)이 NB YTD 적극 오염. 재추출은 **반기/3분기 raw 부재로
raw-blocked** → downloader 발주(`inbox/downloader/20260616T0400Z__…nb_csm_interim_raw_fetch`). 삼성생명 2025.2Q
OVER(+26%)는 partial 아닌 **scope diff(별도/연결)**로 별건 disposition.

## 2026-06-16 — round3 IFRS17 QA (P1/P2/P3) + IFRS17 도메인 SKILL 결정화

**round3 데이터 글리치** (inbox `20260616T0007Z__…ifrs17_pl_sensitivity_round3`) → **commit 5b9b0eb**:
- **P1 흥국 해지율 방향** = staleness(부호버그 아님). heatmap 흥국이 FY2024(rcept 2025…)였음 → FY2025 재추출
  (rcept 20260331004251) 반영. 해지율↑ csm/pl **둘 다 −**(FY2024는 csm−/pl+ 반대), 사망률↑ +27.95/+5.78 =
  owner 기대 일치. `viz_build_ifrs17_panels.py` best-status dedup으로 **흥국 1社만 교체**, 27社+패널3종
  byte-identical, pytest 110. (가비지사 농협/케이디비 미혼입 — phase-2 잔존.)
- **P2 푸본현대 투자손익 −1,487.7억** = **REAL**. FY2025 별도 포괄손익계산서 line-by-line + 요약 교차검증,
  24항목 전부 백만단위 일치, 당기순이익 −1,187억 = FY2025 연간순손실 실재. no-op.
- **P3 하나생명 투자손익 None** = **parse_miss**(실제 0 아님). II.투자수익/III.투자비용 2-line 공시 →
  build_pl_breakdown L275 단일 `L("투자손익")` 미스. 정확값 item18=317,891.06·item17=**+821.41백만**
  (영업이익=item1+item17 gap0; owner flag 예측 +15,037은 기타사업비용 이중차감 오폐합). `_GOLD_CELL_OVERRIDE
  [(KR0097,2025.4Q)]` 추가(메트라이프 audit-only 패턴). ⚠️ 라이브 master 반영 = raw-enabled rebuild 필요
  (이 브랜치 파괴적, [[project-git-purge]]). → TODO out_of_scope "하나 item17=FS-API" 항목 **해소**(파서측 정정).

**IFRS17 도메인 SKILL 결정화** (inbox `20260616T0043Z__…skill_creator_domain_skills`):
- Anthropic `skill-creator`로 `.claude/skills/ifrs17-parser/` 작성 — `SKILL.md`(트리거 description + 운영 코어) +
  `references/pipeline-map.md`(배선·파일맵·스키마·run/verify) + `references/quirks-and-traps.md`(단위/부호/사별
  quirk/destructive-rebuild/항등식). **SOT = `docs/domains/claude-agent-ifrs17.md` 유지**, SKILL은 그 위
  운영 트리거 레이어(요약+참조, 복붙 없음); SOT의 2026-05 PoC-status가 코드와 충돌 시 코드+SKILL 우선 명시.
  `.claude/` gitignore → 머신-로컬(미push). **K-ICS SKILL은 K-ICS 세션 별도**(2-lane split).

## 2026-06-14 — CSM sensitivity panel: column-map / unit / 손보-recovery (inbox 20260614T0712Z)

Owner live-site QA on the CSM sensitivity pipeline — fixed 3 glitches in
`scripts/viz_build_ifrs17_panels.py` (panel parser only; no extractor change):
- **G4b (column mapping)**: `_extract_sensitivity_band` used a fixed LEFT-anchored csm_idx, so
  rowspan-elided 2nd+ risk rows (기준금액 columns dropped) shifted → wrong ΔCSM + null PL. Now RIGHT-anchors
  (negative idx) for the standard 기타포괄손익-trailing layout; other layouts (위험경감/product-row) guarded, no regression.
- **G6 (units → 억원, data-determined)**: cue (억원/백만원/천원/만원) else cross-check table base CSM vs
  `CSM_waterfall.json` total CSM (억원) → power-of-10 snap. Owner's notes were BOTH wrong: 삼성=백만원 (not 만원),
  현대=천원 (not 원). 현대 사망률 ΔCSM −853억 ≈ 삼성 −1,334억 (640× anomaly gone). Output carries
  `unit/unit_detected/unit_source`. Sanity guard: max|ΔCSM| > 3× total CSM → `unit_source=suspect` + null + warning
  (메트라이프 default-백만원 −59조 blocked).
- **G7 (missing 손보)**: panel read only `_sensitivity_mvp.json` (is_mvp dropped valid tables) + the picker
  preferred CSM-less tables. Now reads full `_sensitivity.json` (build_panel skips non-rcept K-ICS files), picker
  prefers a 보험계약마진 column, methodology-table penalty, + a PL-only handler (NH 출재경감 당기손익). Recovered
  메리츠/DB손해/KB/NH (한화 = 별첨, legit partial) + bonus AIA/케이비라이프. **0 regressions, 25/28 ok.**
- Verify: production build touched only `sensitivity_heatmap.json` (other panels byte-identical); pytest 110;
  whole-cohort mvp-vs-full diff CHANGED 0.
- **Follow-up (same session, decision-free sweep):** F16 흥국생명 product-as-rows **DONE** — new
  `_extract_heungkuk_product_rows` + `_is_heungkuk_csm_pl_capital_layout` (4th path, 흥국-specific bare-'CSM'×2 +
  손익효과 + 자본효과 header guard) → 6 proper risk scenarios (사망률/해지율/사업비 × 상승/하락; was garbage
  risk='건강보험' shock='5,852'). status unchanged (was already ok), 0 regression, other panels byte-identical,
  pytest 110. 미래에셋생명·신한라이프 confirmed **legit-absent** (no insurance-risk CSM sensitivity table in body
  — only market-risk/pension; current unavailable/partial correct). **BLOCKED on this branch (raw DART purged):**
  closing-5 label variants / 흥국화재 NEW 2025.4Q-2026.1Q / 흥국생명 2026.1Q doubling — every target (사,분기) raw
  XML was history-purged → can't reproduce or verify; owner must restore raw (backup `insurequant_git_backup_20260614`)
  or run on a branch that still has it. NOTE: gold gate also non-runnable here (`_verify_csm_golds.py` globs repo-root
  `CSM waterfall_*.xlsx` → 0/0; `build_csm_waterfall_master.py` collapses the committed diag to 1 company).
- **Follow-up (validation reparse 20260614T1135Z):** 푸본현대 csm_delta under-scale (csm 9.86억 vs pl 1164.85억)
  root cause was NOT a unit/ratio bug — all 4 of its SA-tagged blocks are the SAME measurement rollforward
  ("기말 보험계약부채(자산)", no ± shock rows); the panel read its rollforward columns as csm/pl = garbage. Fix:
  `_has_shock_rows` (a real sensitivity table has X% 증가/감소/상승/하락 rows) → added as the top picker signal
  AND a guard in extract_sensitivity that returns `partial` when the picked block has no shock rows. Also caught
  KB손해 (5 mis-tagged '(14) 가정변경…변동 내역' rollforwards, no real shock table). 푸본현대 + KB ok→partial
  (garbage→honest); 미래에셋/신한/한화 unchanged; **0 regression on the 23 real ok companies**; pytest 110. This
  removes the peer-scale outlier so validation's SENSITIVITY_UNIT_SANITY should clear. (NB: high within-row
  |csm/pl| for 현대/삼성/한화생명 is legit — CSM absorbs the shock, not an error.)

## 2026-06-14 — REFACTOR 6/6 (bs_snapshot/sensitivity externalization) + GOLDEN-E2E expansion

Finished the owner `parser_refactor` backlog (inbox `20260613T0200Z`) for the ifrs17 lane:
- **REFACTOR-2 → 6/6**: externalized bs_snapshot + sensitivity scoring keywords (15 lists) to
  `data/ifrs17/table_scoring_keywords.yaml` via `scoring.py` `load_scoring().extra` (bespoke sets — all
  ride in `.extra`, no standard fields). Module constant names unchanged → consumers
  (`viz_build_ifrs17_panels`, batch scripts) untouched. intra-block DEDUP `&bs_slices` anchor
  (`_HEADER_BS_SLICES`==`_ROW_SLICES`). New golden tests `test_{bs_snapshot,sensitivity}_extractor.py`.
- **GOLDEN-E2E**: hermetic multi-table fixtures for measurement/insurance_pl/reinsurance (삼성화재
  20250311001055 real values, 2 decoys + 1 genuine), proving table SELECTION end-to-end. +3 tests.
- **Verification** (main session re-ran, did not trust subagent report): `pytest tests/unit/` **110 passed**;
  independent HEAD-vs-config byte-identity **15/15** (non-circular — compares git HEAD constants, not the
  golden literals); E2E asserted values 9/9 present in source JSON; 6-extractor diff is import + constant-load
  only (logic unchanged, −280/+74).
- **Remaining**: REFACTOR-3 slice2 (`src/solvency/parser/` column-picker → registry) is K-ICS/solvency lane,
  out of ifrs17 session scope → kics lane to pick up.
- **Method note**: a workflow subagent HUNG the Windows shell on a multi-line `python -c "..."` JSON dump
  (default Bash timeout never fired → runner wedged, unstoppable via TaskStop). Recovery: drove Phase 2 via a
  hardened fresh Agent (script files / Read tool, never inline multi-line `python -c`). Bake this into future
  fan-out prompts.

## 2026-06-13 — Lane split
Parser forked into two parallel lanes (kics / ifrs17). IFRS17-scoped history starts here; older IFRS17 entries
remain in the frozen combined `changelog_parser.md`. In-flight: REFACTOR-1/2 (scoring config layer, 4/6
extractors + golden tests). Open work: [`TODO_parser_ifrs17.md`](../TODO_parser_ifrs17.md).
