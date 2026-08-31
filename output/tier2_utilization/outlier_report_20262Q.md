# Tier-2 utilization outlier report (2026.2Q)

## Summary

| Metric | Count |
|--------|------:|
| Total companies | 39 |
| In range 0-100% | 36 |
| Outliers (<0, >100, null) | 3 |
| Missing (null) | 0 |

Valid 0-100% distribution: min=0.00%, median=22.71%, max=85.87%

## Spot-check (formula fix before/after)

| Code | Company | Before | After | Notes |
|------|---------|-------:|------:|-------|
| KR0068 | Hanwha Life | 73.07% | 70.53% | Unchanged (gross pre_limit) |
| KR0008 | Samsung Fire | -169.59% | 3.97% | pre_limit already netted lapse |
| KR0001 | Meritz Fire | -321.70% | 294.40% | post-transition residual pre_limit |

## Outliers

### KR0001 메리츠화재해상보험

- **utilization_pct**: 294.40%
- **numerator_eok**: 92894.0
- **tier2_limit_eok**: 31553.5
- **data_source**: proxy
- **quality_flag**: util_over_100
- **lapse_excess_eok**: None
- **hybrid_eok**: None
- **subordinated_eok**: None
- **tier2_eok / pre_limit_eok**: 92894.0 / None
- **proxy_utilization_pct**: 294.4
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.

### KR0032 NH농협손해보험

- **utilization_pct**: 231.17%
- **numerator_eok**: 15538.0
- **tier2_limit_eok**: 6721.5
- **data_source**: proxy
- **quality_flag**: util_over_100
- **lapse_excess_eok**: None
- **hybrid_eok**: None
- **subordinated_eok**: None
- **tier2_eok / pre_limit_eok**: 15538.0 / None
- **proxy_utilization_pct**: 231.17
- **Interpretation**: Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.

### KR0079 미래에셋생명

- **utilization_pct**: -0.01%
- **numerator_eok**: -6.01
- **tier2_limit_eok**: 77987.02
- **data_source**: table
- **quality_flag**: util_negative
- **lapse_excess_eok**: 70547.6
- **hybrid_eok**: None
- **subordinated_eok**: 2930.94
- **tier2_eok / pre_limit_eok**: 73472.53 / 73472.53
- **proxy_utilization_pct**: 0.0
- **Interpretation**: Negative numerator after reconciliation — check MD table row semantics.
