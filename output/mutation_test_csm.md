# CSM Waterfall — Validation Net Mutation Test

> Read-only probe. Injects changelog failure signatures into in-memory copies of `CSM_waterfall.json`, measures which detectors catch them.

- Companies tested: **23** (IR cohort 9 / non-IR 14)
- Detectors: CLOSING_IDENTITY, NB_NONNEG, CONTINUITY, QOQ_JUMP, CROSS_SOURCE_IR (cohort only)

## Catch rate per injected failure

| Injection | caught / tested | caught by (internal) | cross-source-only blind spots |
|---|---|---|---|
| `DOUBLE_uniform` 소계 ×2 (전기간, identity 보존) | 8/23 | — | 8 cohort caught **only** by IR · **14 non-IR BLIND** |
| `DOUBLE_1period` 소계 ×2 (단일분기) | 21/23 | QOQ_JUMP×19, CONTINUITY×13 | **1 non-IR BLIND** |
| `BASIS_uniform` 별도→연결 ×1.45 (전기간, identity 보존) | 8/23 | — | 8 cohort caught **only** by IR · **14 non-IR BLIND** |
| `BASIS_1period` 별도→연결 ×1.45 (단일분기) | 21/23 | QOQ_JUMP×19, CONTINUITY×13 | **1 non-IR BLIND** |
| `OFFYEAR` off-by-one-year (값 1년 시프트) | 3/23 | CONTINUITY×2 | 1 cohort caught **only** by IR · **13 non-IR BLIND** |
| `UNIT100_1period` 단위 ×100 (단일분기) | 21/23 | QOQ_JUMP×19, CONTINUITY×13 | **1 non-IR BLIND** |
| `SIGNFLIP_NB` 신계약 부호반전 (단일분기) | 23/23 | CLOSING_IDENTITY×23, NB_NONNEG×23 | — |

## Reading this

- **Internal detectors** (identity/continuity/qoq/nonneg) need no 2nd source → cover all companies.
- **CROSS_SOURCE_IR** only exists for the 9 IR cohort → a failure caught *only* by cross-source is **invisible on the ~26 non-IR companies**.
- `*_uniform` injections preserve closing identity AND continuity (everything scaled together) → the classic 'consistent-but-wrong'. Watch which detector (if any) still catches them.

## Back-test — pre-existing DART-vs-IR ratio (no injection)

Median `DART 신계약(값_당분기) / IR nb` over shared periods. ~1.0 = agree; far from 1.0 = a discrepancy the tool surfaces with no human (e.g. 한화손보 known ~2× from changelog).

| KR | company | baseline ratio | flag |
|---|---|---|---|
| KR0001 | 메리츠화재해상보험 | 1.000 | ok |
| KR0002 | 한화손해보험 | 0.484 | 🔴 off |
| KR0003 | 롯데손해보험 | 1.000 | ok |
| KR0008 | 삼성화재해상보험 | 0.459 | 🔴 off |
| KR0011 | DB손해보험 | 0.490 | 🔴 off |
| KR0068 | 한화생명 | 1.000 | ok |
| KR0069 | 삼성생명보험 | 1.000 | ok |
| KR0079 | 미래에셋생명보험 | 1.000 | ok |
