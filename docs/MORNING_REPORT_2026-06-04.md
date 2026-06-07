# Morning report — 2026-06-04 (overnight, parser stage)

Task (user, before sleep): extract PL for **all companies × all quarters (2023.1Q–2026.1Q)**
using the CSM-session lessons; **learn the rule from gold and generalize** instead of
answer-sheet hardcoding; maximize correctness and **request gold for only the few truly
stuck**.

## Result in one line

PL Tier-1 (보험손익·투자손익·영업이익·세전·법인세·당기순이익 = items 1, 15-24) is now solid for
**all 260 company-quarters** — self-check **broken `x` = 0** (was 44). Six **general rules**
(no company-code, no quarter-caption hardcoding) did it. Gold gate unchanged.

## What changed (all generalizable; details in `docs/changelog_parser.md` 2026-06-04)

| fix | what it generalizes | cells |
|---|---|---|
| FIX A — priority NI pick | 당기순이익 > 계속영업이익(손실) (중단영업=0 ordering trap) | 8 |
| FIX B — 법인세 residual | item23 = 세전 − 당기순 (DART sign/garbage conventions) | 12 |
| FIX C — identity-first basis | 영업이익=보험손익+투자손익 beats basis pref → 연결→별도 auto (AIG…) | several |
| footnote-ref guard | strip 주NN refs that parse as data (numbered I~X statements) | 하나생명 |
| Tier-2 unit reconcile | 천원/원 notes auto-scaled vs Tier-1 보험수익 | 악사 |
| abs-cost fallback | 보험비용=(negative) no longer flips item3 into 6× | 미래에셋 FY2023 |
| 롯데 Tier-2 de-hardcode | 기수/주석번호 → section-walker (combined+split note forms) | 롯데 FY2023/24 new |
| RC-gate | suppress breakdown when ΣLOB misses 보험손익 >25% (no garbage) | 19 |

## Self-check matrix (`docs/pl_selfcheck_matrix.md`)

`G=4  v=88  i=81  ~=11  x=0  .=206`
- **v** Tier-2 reconciles · **i** Tier-1 solid, no Tier-2 to check · **~** moderate
  wobble <25% (FY2023 first-year / quarterly 기타사업비용 omission — directionally OK) ·
  **.** no statement (unlisted Q1-Q3, empty by design).
- Gold gate (independent): 삼성화재 24/24, 메리츠 24/24, 삼성생명 22/24 (known item19 금융손익
  split), 한화생명 23/24. **No regression.**

## Gold update — 롯데 2024.4Q sheet received & integrated ✅ (`docs/pl_gold_needed.md`)

You sent `보험손익 breakdown_롯데_2024.xlsx`. It pinpointed the root cause: the extractor had
read a **restatement-impact table** ('소급재작성이 …에 미치는 영향', cols [재작성후/영향/재작성전])
as the statement, grabbing the 2023-restated 보험손익 468,499 instead of FY2024's 177,845.
Fixed **generally** (exclude '미치는 영향' tables; guard the 별도 보험비용 fallback) → 롯데
2024.4Q now matches your gold **23/24** (only item15 None-vs-0). PL golds now **5/5, no
regression**; the fix also cleaned 교보·하나's spurious breakdowns.

**Nothing else needs a sheet.** Remaining suppressed Q4 = 한화손해 2025.4Q (known NB-rowspan,
a **code fix**), 악사·교보라이프 (tiny). Quarterly Q1-Q3 suppressions for 메리츠/현대/삼성화재
are low-priority (their annual cells reconcile). Self-check now **G4 / v89 / i74 / ~11 / x0**.
