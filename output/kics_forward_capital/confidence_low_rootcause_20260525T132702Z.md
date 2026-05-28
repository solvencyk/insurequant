# Forward Sim v3: confidence=low Root-Cause Analysis

Source: `output/kics_forward_capital/20260525T132702Z/forward_simulation_v3.json`
Cohort: 37 insurers | LOW: **24** | Generated: 2026-05-25 (F4 read-only analysis)

## Summary by category

| Cat | Definition | N |
|-----|------------|--:|
| A+B | FSC missing both T1 and T2 | 1 |
| B | FSC missing T2 (bond_t2=0, kics_t2>0) | 10 |
| C | FSC face >> BS — over_deduct (real call already done; bond DB stale) | 7 |
| D | FSC face << BS — under_deduct (bond DB partial) | 2 |
| E | Negative basic capital (pre-stressed baseline) | 2 |
| F | no_bonds_in_fsc + BS≈0 — false positive (confidence-logic quirk) | 1 |
| G | Other | 1 |

Classification is mutually exclusive — `E` (negative basic capital) takes priority over FSC-gap labels because the sim is already in a stressed regime.

## Per-insurer table (sorted by ratio drop magnitude)

| Code | Insurer | Cat | T1 gap | T2 gap | Drop pp | Sim bias | Recommendation |
|------|---------|-----|-------:|-------:|--------:|----------|----------------|
| KR0003 | 롯데손해보험 | E | +1% | +237% | +64.8 | over_deduct | Baseline already failing — confidence label is academic; mark as pre-stressed |
| KR0083 | 푸본현대생명보험 | C | +0% | +92% | +59.9 | over_deduct | Accept over_deduct bias; BS row is post-haircut residual while bond DB still lists face value |
| KR0032 | NH농협손해보험 | C | +0% | +216% | +46.8 | over_deduct | Accept over_deduct bias; BS row is post-haircut residual while bond DB still lists face value |
| KR0076 | 아이엠라이프생명보험 | C | +0% | +250% | +42.8 | over_deduct | Accept over_deduct bias; BS row is post-haircut residual while bond DB still lists face value |
| KR0100 | 처브라이프생명보험 | B | - | -100% | +42.4 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |
| KR0070 | 에이비엘생명보험 | C | - | +900% | +41.2 | over_deduct | Accept over_deduct bias; BS row is post-haircut residual while bond DB still lists face value |
| KR1010 | 교보라이프플래닛생명보험 | F | - | -100% | +38.6 | under_deduct | Confidence-logic patch (see end of report) |
| KR1000 | 코리안리재보험 | B | +0% | -100% | +36.5 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |
| KR0009 | 현대해상 | C | - | +577% | +35.4 | over_deduct | Accept over_deduct bias; BS row is post-haircut residual while bond DB still lists face value |
| KR0097 | 하나생명보험 | B | +0% | -100% | +30.3 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |
| KR0005 | 흥국화재 | C | -22% | +400% | +27.5 | over_deduct | Accept over_deduct bias; BS row is post-haircut residual while bond DB still lists face value |
| KR0068 | 한화생명 | G | -45% | -1% | +23.4 | neutral | Manual review |
| KR0050 | 하나손해보험 | B | +0% | -100% | +23.1 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |
| KR0072 | 케이디비생명보험 | E | -100% | -55% | +22.1 | under_deduct | Baseline already failing — confidence label is academic; mark as pre-stressed |
| KR0011 | DB손해보험 | C | +51% | +138% | +21.9 | over_deduct | Accept over_deduct bias; BS row is post-haircut residual while bond DB still lists face value |
| KR0049 | 악사손해보험 | B | - | -100% | +19.6 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |
| KR0079 | 미래에셋생명보험 | D | - | -77% | +14.3 | under_deduct | Investigate whether bond DB is missing a maturity layer vs. BS double-count |
| KR0010 | KB손해보험 | D | - | -88% | +13.9 | under_deduct | Investigate whether bond DB is missing a maturity layer vs. BS double-count |
| KR0008 | 삼성화재해상보험 | B | - | -100% | +0.0 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |
| KR0069 | 삼성생명보험 | B | - | -100% | +0.0 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |
| KR0075 | 비엔피파리바카디프생명보험 | B | - | -100% | +0.0 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |
| KR0099 | KB라이프생명 | A+B | -100% | -100% | +0.0 | under_deduct | Add full capital-instrument set to FSC bond DB; meanwhile mark sim under_deduct |
| KR0150 | 서울보증보험 | B | - | -100% | +0.0 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |
| KR1011 | IBK연금보험 | B | - | -100% | +0.0 | under_deduct | Add T2 subordinated rows to FSC bond DB (alias gap) |

## Top-3 highest impact

- **KR0003 롯데손해보험** (Cat E, 159% → 95%, drop +64.8pp): T1 gap 1.3%, T2 gap 237.0%. Bond face T2=7200.0억 vs BS T2=2136.7억 (subordinated_eok). Sim is **over_deduct**.
- **KR0083 푸본현대생명보험** (Cat C, 86% → 26%, drop +59.9pp): T1 gap 0.2%, T2 gap 91.6%. Bond face T2=6730.0억 vs BS T2=3511.7억 (subordinated_eok). Sim is **over_deduct**.
- **KR0032 NH농협손해보험** (Cat C, 131% → 84%, drop +46.8pp): T1 gap 0.0%, T2 gap 215.9%. Bond face T2=3000.0억 vs BS T2=949.6억 (subordinated_eok). Sim is **over_deduct**.

## Category F (false positive) — proposed 1-line fix

- KR1010 교보라이프플래닛생명보험: `kics_t2_base=0.1억` (numerical noise, effectively zero) → currently flagged `fsc_missing_t2` + low. Insurer has no real capital instruments; sim is fully deterministic.

In `scripts/forward_capital_simulation.py::compute_confidence` (around line 224), the early-exit branch uses strict equality `kics_t1 == 0 and kics_t2 == 0`. Replace with a small tolerance:

```python
# current (line ~224-226)
if (bond_coverage == "no_bonds_in_fsc"
        and bond_t1_out == 0 and bond_t2_out == 0
        and kics_t1 == 0 and kics_t2 == 0):

# proposed: tolerate sub-1억 BS residual (rounding noise)
if (bond_coverage == "no_bonds_in_fsc"
        and bond_t1_out == 0 and bond_t2_out == 0
        and kics_t1 < 1.0 and kics_t2 < 1.0):
```

Rationale: K-ICS BS values are in 억원; sub-1억 residuals are rounding/legacy noise. The patch reclassifies KR1010 교보라이프플래닛 (BS T2 = 0.1억) from `low` → `high`.

## Notes on the user-prompt context

- The handoff message labelled KR0008 삼성화재 and KR0049 악사 as Category F (no FSC gap possible). **Verification shows otherwise**: KR0008 has BS T2 = 4,097억 and KR0049 has BS T2 = 331억 — both insurers carry real subordinated debt on K-ICS but have **zero rows in the FSC bond DB**. These are genuine Category B (FSC alias/coverage gaps), not F. Phase 5 cross-ref v2 already flagged KR0008/KR0069 as alias follow-up items.
- Only KR1010 교보라이프플래닛 (BS T2 = 0.1억) qualifies as Category F under any reasonable definition.
- Six rows (KR0008, KR0069, KR0075, KR0099, KR0150, KR1011) show 0pp ratio drop because `outstanding_bonds_total_eok = 0` (nothing to deduct in the sim) — yet `low` confidence is correct: the sim is silently under-deducting real BS-listed capital. These should remain `low` until the FSC DB coverage is fixed.

