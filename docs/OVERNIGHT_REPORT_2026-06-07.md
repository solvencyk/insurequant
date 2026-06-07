# Overnight Autonomous Report — 2026-06-07 (night #2)

Parser-stage autonomous run. Mandate: finish open TODO + tractable mid-term goals + run the
validation gates myself and loop-fix until clean. Owner asleep.

## TL;DR

**CSM master tables are now fully consistent: closing 0F + crosscheck 0F.** The validator's
new `CSM_PLAUSIBILITY` continuity/duplicate rule (which I'd argued for) surfaced 5 real
absolute-value extraction bugs that the arithmetic-only closing-identity check had passed.
All 5 fixed, verified, committed. Both mid-term goals (MLG-1, MLG-2) were investigated and
found to need an owner decision / multi-session work — documented, not forced.

## Validation gate state (final)

```
closing:302P/0F/6S | crosscheck:69P/1M/0F | plausibility:0dup/1spike/12cont
pl_bridge:2058P/14F/456S | PL gold: 1 DIRECT fail (DB손보 2024.2Q item11, PL lane)
K-ICS: RED=2 (both KR0010 documented OCR exceptions → gate PASS) | NB CSM: 5/5 pass
```

- **CSM domain: clean (0F/0F).** Was crosscheck 2F (롯데·케이디비 2025.4Q) → now 0F.
  plausibility 복붙 6→0.
- **pl_bridge 14F unchanged** = FY2023 quarters (site non-exposed) + 메리츠 2023 + small
  residuals (흥국 −345/−714, KB라이프 +1,136, 악사 +3,483). PL lane; not CSM.

## Fixed & committed (CSM, branch fix/csm-product-segmented-columns)

| # | Company | Root cause | Result | Commit |
|---|---------|-----------|--------|--------|
| 1 | 흥국화재 | 배당합산 picked 기말=None block → closing collapsed to 유배당 sub-total (34억) → broken 4Q 기초 poisoned anchor → 2025.Q copied 2024 | pick_group prefers complete block; 2025.4Q 34→28,047; 복붙 0 | 2edfa2e |
| 2 | 케이디비 (분기) | 전기 `제N(전)기` with 가/나 enumerator slipped past startswith prior test → anchor poisoned | _is_prior_caption re.search; 2025.1~3Q de-collided | 2edfa2e |
| 3 | 메트라이프 | 별도세그합산 summed grand-total + components → 기초 2× | _strip_aggregate; 2025.4Q 기초 48,134→24,067 | 2edfa2e |
| 4 | 케이디비 2025.4Q (연차) | _double_total_sum doubled psum → _comparable_min picked 무배당 segment | _strip_aggregate first; 5,338→7,730 | a924202 |
| 5 | 롯데손보 | 배당있는/없는 = SEPARATE CER tables; single-pick took tiny 배당있는 or missed 분기말 label | 분기말 labels + _pattern2_segsum (sum 당기 배당groups, disjoint-guarded); 2025.4Q 12,828→24,748; 2026.1Q·2025.3Q resurrected | e5bb9c9 |

Root masters rebuilt + committed (2f05308): `CSM_waterfall.json`, `NB_CSM_multiple.json`,
viz diag/cov, nb_csm_validation. No regression on 삼성화재/현대/한화손보/삼성생명/메리츠/DB생명/한화생명.

## Mid-term goals — investigated, deferred (owner decision needed)

- **MLG-1 (듀레이션갭):** DART body has the gap *narrative* + maturity ladders + 100bp rate
  sensitivity, but NOT asset/liability duration numbers or the gap itself (needs maturity +
  discount-curve derivation). Life insurers rich, non-life sparse. **Owner decision:** extract
  100bp sensitivity only (direct), vs define a duration-derivation rule.
- **MLG-2 (K-ICS 시장위험 분해):** No consolidated 시장위험액 현황 table; sub-risks
  (금리/주식/부동산/외환/자산집중) are heterogeneous per-company tables (금리 = 충격 shock table,
  needs derivation). PL-Tier2-scale per-company handlers + an owner ruling on 금리위험액
  derivation are required before validation R11 (Σ=시장위험액) can close.

## Remaining / not done this session

- **PL Tier-2 follow-up (미래에셋 분기 unit, 한화손해 13/14, 롯데 6/12):** the worktree subagent
  hit its session limit while still probing (no extractor edit landed). Main is finishing this
  directly. These are coverage improvements (filling Tier-2 cells), not gate failures.
- **PL gold 1 DIRECT fail** (DB손보 2024.2Q item11 재보험 RA, ~10%): pre-existing partial gold,
  PL lane.
- **Low-priority/gray (documented, deferred):** 롯데 2023.1Q; 롯데 2025.2Q/3Q 배당있는 (~0.5%,
  half-year filing doesn't split it); 케이디비 2024.1Q spike (+58%, warn); closing 6 SKIP
  (amort label variants, edge quarters, regression risk without an active CSM gold gate);
  cont 12 (IFRS17 opening-restatement gray-zone — validator guidance = YELLOW not RED).

## Deploy readiness

CSM master tables (CSM_waterfall.json, NB_CSM_multiple.json) are validated and deployable
(closing 0F, crosscheck 0F). PL_breakdown.json is at the prior baseline (14F pl_bridge are
known FY2023/residual, non-blocking). git push is owner's call.
