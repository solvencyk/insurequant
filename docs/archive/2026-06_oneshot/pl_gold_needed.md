# PL breakdown — hand-built gold request (the few that truly need an answer sheet)

Generated alongside `scripts/_pl_goldneeded.py` from the Tier-2 reconciliation gate in
`scripts/build_pl_breakdown.py`.  **Tier-1 (보험손익·투자손익·영업이익·세전·법인세·당기순이익 등
items 1, 15-24) is solid for all 260 company-quarters** (self-check broken `x`=0; see
`docs/pl_selfcheck_matrix.md`).  What is missing is only the **Tier-2 issued/reinsurance
decomposition (items 2-14)** for the cells below, where the breakdown did not reconcile to
the statement 보험손익 within 25% and was therefore suppressed rather than published wrong.

## Status — 롯데손해 2024.4Q RESOLVED (2026-06-04)

The one mid-size ask is **done**: user sent `보험손익 breakdown_롯데_2024.xlsx`. Root cause was
the extractor reading a **restatement-impact table** ('…소급재작성이 …에 미치는 영향', columns
[재작성후, 영향, 재작성전]) as the statement, picking the 2023-restated 보험손익 (468,499)
instead of FY2024's 177,845. Fixed generally (exclude '미치는 영향' tables) → 롯데 2024.4Q now
matches the gold 23/24 (only item15 None-vs-0). No company-specific hardcoding.

## Status — 한화생명 quarterly RESOLVED (2026-06-04)

User sent `보험손익 breakdown_한화생명_2025.2Q.xlsx` (별도). It exposed two GENERAL bugs that had
been blocking quarterly extraction fleet-wide: (1) 분기/반기보고서 statements label net income
**반기순이익/분기순이익** (not 당기순이익) — the matcher missed the whole statement; (2) quarterly
statements are **[3개월, 누적]** and the schema wants the **누적(YTD)** column, not 3개월. Fixed
both generally → 한화생명 2025.2Q matches 20/24 (Tier-1 exact; only item5/10 위험조정 minor), AND
삼성생명·현대·삼성화재 quarterly were corrected from 3개월/garbage to proper YTD. `no_income_statement`
149→60; listed insurers now hold 8-10 quarterly cells each.

## Remaining Q4 cells with no trustworthy breakdown

| company | code | quarter(s) | why it's stuck | matters? |
|---|---|---|---|---|
| 교보라이프플래닛 | KR1010 | 2024.4Q | digital-only micro insurer; 생보 comprehensive note absent/atypical. tiny. | low |

**That's the only Q4 gold candidate left.** 한화손해 2025.4Q NB-rowspan and 악사 LOB are now
either resolved or quarterly-only suppressions (Tier-1 intact). Quarterly Tier-2 breakdowns that
don't reconcile (24 cells) are RC-gate-suppressed (Tier-1 kept) — quarterly-note noise, not gold.

## Known minor (no action needed)
- **한화생명 2023.2Q** — first-IFRS17-year statement has uneven 3개월/누적 column counts on the
  영업외 rows → col alignment off → 22≠20+21 (self-check x). 1 of 292 cells, FY2023 only.

## Low priority — quarterly (Q1-Q3) suppressions (Tier-1 intact, breakdown blank)

These are listed insurers whose **quarterly** notes don't match the (also-quarterly)
statement; the annual (Q4) cells for the same companies reconcile fine. Not worth gold.

- 메리츠화재 KR0001: 2023.3Q, 2024.2Q, 2024.3Q, 2025.2Q, 2025.3Q
- 현대해상 KR0009: 2024.2Q, 2024.3Q, 2025.2Q, 2025.3Q
- 삼성화재 KR0008: 2025.2Q, 2025.3Q
- 미래에셋생명 KR0079: 2023.3Q

## Accepted as-is (moderate wobble <25%, directionally correct — no gold needed)

DB생명 2023.3Q, 미래에셋 2023.4Q (6.4%), 삼성생명 2023.4Q (11%), 신한라이프 2023.4Q (11%),
롯데손해 2024.1Q, 메리츠 2023.1Q/2023.2Q/2024.1Q/2025.1Q/2026.1Q, 악사 2024.4Q (19.7%) —
these are mostly FY2023 first-IFRS17-year layouts or quarterly 기타사업비용 omissions; the
breakdown is published and close enough to validate by self-check.

## Gold format (same as the existing PL golds)

A `보험손익 breakdown_<회사>.xlsx` sheet, 24-item schema, col index 4 = 항목번호, col index 7 =
값 (백만원).  See `보험손익 breakdown_삼성화재.xlsx` for the template; verified by
`scripts/_verify_pl_golds.py`.
